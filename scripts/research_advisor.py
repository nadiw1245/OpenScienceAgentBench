#!/usr/bin/env python3
"""Chat with an arXiv-grounded research trends and roadmap advisor."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


RESPONSES_URL = "https://api.openai.com/v1/responses"
CHAT_ENDPOINTS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "huggingface": "https://router.huggingface.co/v1/chat/completions",
}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIGEST = ROOT / "data" / "latest.json"
DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "openai": "gpt-6-luna",
}
MAX_CONTEXT_PAPERS = 30
ABSTRACT_CHARS = 900
MAX_FOLLOW_UPS = 6
ARXIV_ID_RE = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")
GITHUB_REPO_RE = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.IGNORECASE)

THEMES: dict[str, tuple[str, ...]] = {
    "Agents and autonomous workflows": (
        "agent", "agents", "agentic", "autonomous agent", "multi-agent", "tool use", "tool-using"
    ),
    "Robotics and embodied AI": (
        "robot", "robotics", "embodied", "manipulation", "world model", "vision-language-action", "vla"
    ),
    "Multimodal models": (
        "multimodal", "vision-language", "image", "video", "audio", "cross-modal", "visual reasoning"
    ),
    "Reasoning and planning": (
        "reasoning", "planning", "mathematical", "problem solving", "chain-of-thought", "logic"
    ),
    "Safety and evaluation": (
        "safety", "alignment", "robustness", "evaluation", "benchmark", "red-team", "trustworthy"
    ),
    "Model efficiency": (
        "efficient", "efficiency", "compression", "quantization", "pruning", "distillation", "inference"
    ),
    "Scientific and domain research": (
        "scientific discovery", "biology", "protein", "drug", "chemistry", "medical", "scientific research"
    ),
}

STOP_WORDS = {
    "about", "after", "also", "based", "between", "could", "current", "from", "give", "have",
    "into", "more", "most", "other", "paper", "papers", "path", "research", "should", "their",
    "there", "these", "this", "those", "trend", "trends", "what", "when", "where", "which",
    "with", "would", "your", "want", "will", "using", "into", "over", "under", "recent",
}

INSTRUCTIONS = """You are the OpenScienceAgentBench Research Advisor. Help early-career researchers understand recent AI research and choose a feasible research direction.

Evidence rules:
- Treat the supplied arXiv digest as a recent, limited snapshot, not a census of AI research. The keyword theme counts are heuristic tags and cannot prove a field-wide or increasing trend.
- When describing a pattern, call it a signal in this snapshot. Never claim a theme is growing over time unless the supplied data contains a time comparison.
- Cite concrete paper examples with Markdown links to their supplied arXiv URLs. Use only paper IDs and URLs present in the digest; do not invent citations, code links, results, or literature gaps.
- Paper abstracts are short summaries. Mark claims that need full-paper review, and tell the researcher to read cited papers before treating a gap or result as established.
- Distinguish a repository link listed in arXiv metadata from a GitHub title-search suggestion. Neither is proof that results reproduce.

Advice rules:
- Answer the research-trends question first, using 3-5 themes and a few cited examples.
- Tailor 2-3 possible research paths to the researcher's interests, background, goal, time, compute, data, and mentoring constraints. If information is missing, say what you assumed and ask up to three useful questions.
- Recommend one feasible path and give a staged 30/60/90-day roadmap with concrete deliverables. Include a first action the researcher can take this week, a baseline/reproduction step, an evaluation plan, and a clear condition for continuing or changing direction.
- Treat proposed research gaps as hypotheses to validate with a focused literature search, not as established novelty. Favor small, falsifiable questions and reproducible comparisons over promises of a breakthrough.
- Be encouraging but realistic. Prefer open datasets, modest compute, and a reproducible baseline when resources are limited. Keep the answer practical and concise."""


def paper_text(paper: dict[str, Any]) -> str:
    return " ".join(
        [
            str(paper.get("title", "")),
            str(paper.get("abstract", "")),
            " ".join(str(item) for item in paper.get("categories", [])),
        ]
    ).casefold()


def theme_labels(paper: dict[str, Any]) -> list[str]:
    text = paper_text(paper)
    return [
        label
        for label, keywords in THEMES.items()
        if any(re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text) for keyword in keywords)
    ]


def theme_counts(papers: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts = {label: 0 for label in THEMES}
    for paper in papers:
        for label in theme_labels(paper):
            counts[label] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def is_overview_question(question: str) -> bool:
    terms = set(re.findall(r"[a-z0-9]+", question.casefold()))
    return bool(
        terms
        & {
            "trend", "trends", "overview", "landscape", "popular", "happening",
            "direction", "directions", "theme", "themes", "emerging", "frontier",
        }
    )


def select_papers(
    papers: list[dict[str, Any]], question: str, profile: dict[str, str]
) -> list[dict[str, Any]]:
    if len(papers) <= MAX_CONTEXT_PAPERS:
        return papers

    profile_text = " ".join([question, *profile.values()]).casefold()
    terms = {
        term
        for term in re.findall(r"[a-z0-9][a-z0-9-]{2,}", profile_text)
        if term not in STOP_WORDS
    }
    recent_first = sorted(papers, key=lambda paper: str(paper.get("published", "")), reverse=True)

    if is_overview_question(question) or not terms:
        selected: list[dict[str, Any]] = []
        selected_ids: set[str] = set()
        for label, _ in theme_counts(recent_first):
            matches = [paper for paper in recent_first if label in theme_labels(paper)]
            for paper in matches[:3]:
                paper_id = str(paper.get("arxiv_id", ""))
                if paper_id not in selected_ids:
                    selected.append(paper)
                    selected_ids.add(paper_id)
                if len(selected) >= MAX_CONTEXT_PAPERS:
                    return selected
        for paper in recent_first:
            paper_id = str(paper.get("arxiv_id", ""))
            if paper_id not in selected_ids:
                selected.append(paper)
                selected_ids.add(paper_id)
            if len(selected) >= MAX_CONTEXT_PAPERS:
                break
        return selected

    scored: list[tuple[int, str, dict[str, Any]]] = []
    for paper in papers:
        title = str(paper.get("title", "")).casefold()
        abstract = str(paper.get("abstract", "")).casefold()
        categories = " ".join(str(item) for item in paper.get("categories", [])).casefold()
        score = sum(
            (6 if term in title else 0)
            + (2 if term in categories else 0)
            + min(3, abstract.count(term))
            for term in terms
        )
        if score:
            scored.append((score, str(paper.get("published", "")), paper))

    ranked = [paper for _, _, paper in sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)]
    selected = ranked[:MAX_CONTEXT_PAPERS]
    selected_ids = {str(paper.get("arxiv_id", "")) for paper in selected}
    if len(selected) < MAX_CONTEXT_PAPERS:
        selected.extend(
            paper
            for paper in recent_first
            if str(paper.get("arxiv_id", "")) not in selected_ids
        )
        selected = selected[:MAX_CONTEXT_PAPERS]
    return selected


def load_digest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as digest_file:
        digest = json.load(digest_file)
    if not isinstance(digest.get("papers"), list) or not digest["papers"]:
        raise ValueError(f"No paper records found in {path}. Generate a digest first.")
    return digest


def make_context(digest: dict[str, Any], papers: list[dict[str, Any]]) -> str:
    query = digest.get("query", {})
    counts = theme_counts(digest["papers"])
    lines = [
        "ARXIV SNAPSHOT METADATA",
        f"Generated at UTC: {digest.get('generated_at_utc', 'unknown')}",
        f"First-submission window in days: {query.get('first_submission_window_days', 'unknown')}",
        f"Categories: {', '.join(query.get('categories', []))}",
        f"Papers in snapshot: {digest.get('count', len(digest['papers']))}",
        "",
        "HEURISTIC THEME COUNTS (themes overlap; these are keyword tags, not evidence of a growing trend)",
    ]
    lines.extend(f"- {label}: {count}/{len(digest['papers'])} papers" for label, count in counts if count)
    lines.extend(["", f"PAPERS SELECTED FOR THIS QUESTION (up to {MAX_CONTEXT_PAPERS}; abstracts are clipped):"])

    for paper in papers:
        paper_id = str(paper.get("arxiv_id", ""))
        abstract = " ".join(str(paper.get("abstract", "")).split())[:ABSTRACT_CHARS]
        if len(str(paper.get("abstract", ""))) > ABSTRACT_CHARS:
            abstract += "..."
        repos = paper.get("github_repositories") or []
        repo_text = "; ".join(
            f"{repo.get('url')} (listed in arXiv {', '.join(repo.get('source_fields', []))})"
            for repo in repos
        ) or "no GitHub repository link found in arXiv metadata"
        lines.extend(
            [
                f"- arXiv:{paper_id} | {paper.get('title', '')}",
                f"  URL: {paper.get('arxiv_url', '')}",
                f"  First submitted: {paper.get('published', '')}; categories: {', '.join(paper.get('categories', []))}",
                f"  Themes: {', '.join(theme_labels(paper)) or 'unclassified by keyword rules'}",
                f"  Code evidence: {repo_text}",
                f"  Abstract: {abstract}",
            ]
        )
    return "\n".join(lines)


def build_initial_message(
    question: str, profile: dict[str, str], context: str
) -> str:
    profile_lines = [f"{key}: {value or 'not provided'}" for key, value in profile.items()]
    return (
        f"RESEARCHER QUESTION\n{question}\n\nRESEARCHER PROFILE\n"
        + "\n".join(profile_lines)
        + "\n\n"
        + context
    )


def response_text(result: dict[str, Any]) -> str:
    text_parts: list[str] = []
    for item in result.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                text_parts.append(str(content["text"]))
    if not text_parts:
        raise ValueError("The model response did not contain output text.")
    return "\n".join(text_parts).strip()


def chat_response_text(result: dict[str, Any]) -> str:
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("The chat response did not contain an assistant message.") from error
    if isinstance(content, str):
        answer = content.strip()
    elif isinstance(content, list):
        answer = "\n".join(
            str(part["text"])
            for part in content
            if isinstance(part, dict) and part.get("type") == "text" and part.get("text")
        ).strip()
    else:
        answer = ""
    if not answer:
        raise ValueError("The chat response did not contain output text.")
    return answer


def citation_warnings(answer: str, papers: list[dict[str, Any]]) -> list[str]:
    allowed_ids = {str(paper.get("arxiv_id", "")) for paper in papers}
    cited_ids = {match.group(1) for match in ARXIV_ID_RE.finditer(answer)}
    unknown_ids = sorted(cited_ids - allowed_ids)

    allowed_repositories = {
        str(repository.get("url", "")).rstrip("/").casefold()
        for paper in papers
        for repository in paper.get("github_repositories", [])
    }
    cited_repositories = {
        f"https://github.com/{match.group(1)}/{match.group(2)}".rstrip(".,;:!?").casefold()
        for match in GITHUB_REPO_RE.finditer(answer)
    }
    unknown_repositories = sorted(cited_repositories - allowed_repositories)

    warnings = []
    if unknown_ids:
        warnings.append("arXiv IDs outside the records supplied to this conversation: " + ", ".join(unknown_ids))
    if unknown_repositories:
        warnings.append("GitHub repositories not linked in the selected arXiv records: " + ", ".join(unknown_repositories))
    return warnings


def call_responses_api(
    api_key: str, model: str, history: list[dict[str, Any]]
) -> dict[str, Any]:
    payload = json.dumps(
        {
            "model": model,
            "instructions": INSTRUCTIONS,
            "input": history,
            "store": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        RESPONSES_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        message = api_error_message(error)
        raise RuntimeError(f"OpenAI API returned HTTP {error.code}: {message}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not connect to the OpenAI API: {error.reason}") from error
    return result


def api_error_message(error: urllib.error.HTTPError) -> str:
    try:
        error_data = json.loads(error.read().decode("utf-8"))
        detail = error_data.get("error", error_data)
        if isinstance(detail, dict):
            return str(detail.get("message", detail.get("detail", detail)))
        return str(detail)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return str(error)


def call_chat_api(
    provider: str,
    api_key: str,
    model: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = json.dumps(
        {
            "model": model,
            "messages": history,
            "max_tokens": 2200,
            "stream": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        CHAT_ENDPOINTS[provider],
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        message = api_error_message(error)
        raise RuntimeError(f"{provider.title()} API returned HTTP {error.code}: {message}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not connect to the {provider.title()} API: {error.reason}") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask about recent AI research and get a cited, personalized roadmap."
    )
    parser.add_argument("question", nargs="?", help="Question about trends or a research direction")
    parser.add_argument("--interests", default="", help="Research topics that interest you")
    parser.add_argument("--background", default="", help="Current skills or research experience")
    parser.add_argument("--constraints", default="", help="Time, compute, data, or mentorship constraints")
    parser.add_argument("--goal", default="", help="What you hope to achieve")
    parser.add_argument("--digest", type=Path, default=DEFAULT_DIGEST, help="Path to latest.json")
    parser.add_argument(
        "--provider",
        choices=("gemini", "huggingface", "openai"),
        default=os.environ.get("RESEARCH_ADVISOR_PROVIDER", "gemini").casefold(),
        help="Model API provider (default: RESEARCH_ADVISOR_PROVIDER or gemini)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID (default depends on provider or its provider-specific environment variable)",
    )
    parser.add_argument("--once", action="store_true", help="Return one answer without follow-up chat")
    args = parser.parse_args()
    return args


def read_optional(prompt: str, current: str) -> str:
    if current:
        return current
    return input(prompt).strip()


def main() -> int:
    args = parse_args()
    provider_env = {
        "gemini": ("GEMINI_API_KEY", "GEMINI_MODEL"),
        "huggingface": ("HF_TOKEN", "HF_MODEL"),
        "openai": ("OPENAI_API_KEY", "OPENAI_MODEL"),
    }
    token_name, model_env_name = provider_env[args.provider]
    api_key = os.environ.get(token_name, "").strip()
    if not api_key:
        print(f"Set {token_name} in your environment before starting the advisor.", file=sys.stderr)
        return 2
    model = args.model or os.environ.get(model_env_name) or DEFAULT_MODELS.get(args.provider)
    if not model:
        print(f"Set {model_env_name} or pass --model for the {args.provider} provider.", file=sys.stderr)
        return 2

    try:
        digest = load_digest(args.digest)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Could not load the arXiv digest: {error}", file=sys.stderr)
        return 2

    question = args.question or ""
    interactive = sys.stdin.isatty()
    if not question and interactive:
        question = input("What would you like to know about recent AI research? ").strip()
    if not question:
        print("Provide a question, for example: What research trends appear in AI agents?", file=sys.stderr)
        return 2

    profile = {
        "Interests": args.interests,
        "Background and skills": args.background,
        "Constraints (time, compute, data, mentorship)": args.constraints,
        "Desired outcome": args.goal,
    }
    if interactive:
        profile["Interests"] = read_optional("Research interests (optional): ", profile["Interests"])
        profile["Background and skills"] = read_optional(
            "Your background or current skills (optional): ", profile["Background and skills"]
        )
        profile["Constraints (time, compute, data, mentorship)"] = read_optional(
            "Time, compute, data, or mentoring limits (optional): ",
            profile["Constraints (time, compute, data, mentorship)"],
        )
        profile["Desired outcome"] = read_optional(
            "Your goal (paper, reproduction, portfolio, etc.; optional): ", profile["Desired outcome"]
        )

    selected = select_papers(digest["papers"], question, profile)
    context = make_context(digest, selected)
    available_papers = {str(paper.get("arxiv_id", "")): paper for paper in selected}
    conversation_topics = [question]
    initial_message = build_initial_message(question, profile, context)
    response_history = [{"role": "user", "content": initial_message}]
    chat_history = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": initial_message},
    ]

    try:
        for turn in range(MAX_FOLLOW_UPS + 1):
            if args.provider == "openai":
                response = call_responses_api(api_key, model, response_history)
                answer = response_text(response)
            else:
                response = call_chat_api(args.provider, api_key, model, chat_history)
                answer = chat_response_text(response)
            print("\n" + answer + "\n")
            warnings = citation_warnings(answer, list(available_papers.values()))
            if warnings:
                print("Source check: " + " | ".join(warnings))
            if not interactive or args.once or turn >= MAX_FOLLOW_UPS:
                break
            follow_up = input("Follow-up question (or type 'quit' to exit): ").strip()
            if not follow_up or follow_up.casefold() in {"q", "quit", "exit"}:
                break
            retrieval_question = " ".join([*conversation_topics[-2:], follow_up])
            selected = select_papers(digest["papers"], retrieval_question, profile)
            for paper in selected:
                available_papers[str(paper.get("arxiv_id", ""))] = paper
            context = make_context(digest, selected)
            conversation_topics.append(follow_up)
            follow_up_message = {
                "role": "user",
                "content": (
                    f"FOLLOW-UP QUESTION\n{follow_up}\n\n"
                    f"UPDATED ARXIV EVIDENCE FOR THIS TURN\n{context}"
                ),
            }
            if args.provider == "openai":
                response_history.extend([*response.get("output", []), follow_up_message])
            else:
                chat_history.extend(
                    [
                        {"role": "assistant", "content": answer},
                        follow_up_message,
                    ]
                )
    except (RuntimeError, ValueError, TimeoutError) as error:
        print(f"Advisor error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
