#!/usr/bin/env python3
"""Build an arXiv AI paper digest with explicit source provenance."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
DEFAULT_CATEGORIES = ("cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "cs.NE", "stat.ML")
MAX_API_RESULTS = 2000
GITHUB_URL_RE = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.IGNORECASE
)
MARKDOWN_SPECIAL_RE = re.compile(r"([\\`*_{}\[\]()#+.!|>])")
ROOT = Path(__file__).resolve().parents[1]


def markdown_escape(value: str) -> str:
    return MARKDOWN_SPECIAL_RE.sub(r"\\\1", value)


def github_repositories(fields: dict[str, str]) -> list[dict[str, object]]:
    """Extract GitHub repository URLs and record where each was found."""
    found: dict[str, set[str]] = {}
    ignored_owners = {"features", "marketplace", "orgs", "search", "sponsors", "topics"}

    for field_name, text in fields.items():
        for match in GITHUB_URL_RE.finditer(text):
            owner, repository = match.groups()
            repository = repository.rstrip(".,;:!?")
            if repository.lower().endswith(".git"):
                repository = repository[:-4]
            if not repository or owner.lower() in ignored_owners:
                continue
            url = f"https://github.com/{owner}/{repository}"
            found.setdefault(url, set()).add(field_name)

    return [
        {"url": url, "source_fields": sorted(source_fields)}
        for url, source_fields in sorted(found.items(), key=lambda item: item[0].casefold())
    ]


def parse_entry(entry: ET.Element) -> dict[str, object]:
    def text_at(path: str) -> str:
        element = entry.find(path)
        return " ".join((element.text or "").split()) if element is not None else ""

    raw_id = text_at(f"{{{ATOM_NS}}}id").rstrip("/").rsplit("/", 1)[-1]
    arxiv_id = re.sub(r"v\d+$", "", raw_id)
    abstract = text_at(f"{{{ATOM_NS}}}summary")
    comment = text_at(f"{{{ARXIV_NS}}}comment")
    title = text_at(f"{{{ATOM_NS}}}title")
    published = text_at(f"{{{ATOM_NS}}}published")
    updated = text_at(f"{{{ATOM_NS}}}updated")

    authors = [
        " ".join((name.text or "").split())
        for name in entry.findall(f"{{{ATOM_NS}}}author/{{{ATOM_NS}}}name")
        if name.text
    ]
    categories = sorted(
        {
            category.attrib["term"]
            for category in entry.findall(f"{{{ATOM_NS}}}category")
            if category.attrib.get("term")
        }
    )
    primary_category = entry.find(f"{{{ARXIV_NS}}}primary_category")
    primary_category_term = primary_category.attrib.get("term", "") if primary_category is not None else ""

    source_fields = {"abstract": abstract}
    if comment:
        source_fields["author_comment"] = comment
    repositories = github_repositories(source_fields)
    github_search_url = (
        "https://github.com/search?"
        + urllib.parse.urlencode({"q": title, "type": "repositories"})
    )

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "updated": updated,
        "primary_category": primary_category_term,
        "categories": categories,
        "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        "github_repositories": repositories,
        "github_search_url": github_search_url if not repositories else None,
    }


def fetch_entries(categories: tuple[str, ...], cutoff: datetime, now: datetime, api_limit: int) -> list[ET.Element]:
    category_query = " OR ".join(f"cat:{category}" for category in categories)
    date_query = (
        f"submittedDate:[{cutoff.strftime('%Y%m%d%H%M')} TO {now.strftime('%Y%m%d%H%M')}]"
    )
    search_query = f"({category_query}) AND {date_query}"
    parameters = urllib.parse.urlencode(
        {
            "search_query": search_query,
            "start": 0,
            "max_results": api_limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{parameters}",
        headers={"User-Agent": "OpenScienceAgentBench/0.1 (arXiv research digest)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        feed = ET.fromstring(response.read())
    return feed.findall(f"{{{ATOM_NS}}}entry")


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def collect_papers(
    entries: list[ET.Element], cutoff: datetime, now: datetime, max_papers: int
) -> list[dict[str, object]]:
    papers_by_id: dict[str, dict[str, object]] = {}
    for entry in entries:
        paper = parse_entry(entry)
        if not paper["arxiv_id"] or not paper["published"]:
            continue
        published = parse_datetime(str(paper["published"]))
        # arXiv's published date is the version 1 submission date. Excluding old
        # version 2+ updates keeps this feed focused on newly released papers.
        if cutoff <= published <= now:
            papers_by_id[str(paper["arxiv_id"])] = paper

    papers = sorted(
        papers_by_id.values(),
        key=lambda paper: (str(paper["published"]), str(paper["arxiv_id"])),
        reverse=True,
    )
    return papers[:max_papers]


def author_line(authors: list[str]) -> str:
    if len(authors) > 8:
        return ", ".join(authors[:8]) + ", et al."
    return ", ".join(authors) or "Authors not listed"


def render_markdown(papers: list[dict[str, object]], generated_at: datetime, days: int) -> str:
    lines = [
        "# Latest arXiv AI research",
        "",
        f"Generated at **{generated_at.strftime('%Y-%m-%d %H:%M UTC')}**. ",
        f"Showing version 1 papers first submitted in the last **{days} days**.",
        "",
        f"Found **{len(papers)} papers**. Repository links below are included only when present in arXiv metadata; GitHub search links are unverified suggestions.",
        "",
        "Source: [arXiv API](https://info.arxiv.org/help/api/user-manual.html).",
        "",
    ]
    if not papers:
        lines.extend(["No matching papers were returned for this window.", ""])
        return "\n".join(lines)

    for paper in papers:
        title = markdown_escape(str(paper["title"]))
        paper_url = str(paper["arxiv_url"])
        published = parse_datetime(str(paper["published"])).strftime("%Y-%m-%d")
        categories = ", ".join(str(category) for category in paper["categories"])
        abstract = str(paper["abstract"])
        if len(abstract) > 700:
            abstract = abstract[:697].rsplit(" ", 1)[0] + "..."

        lines.extend(
            [
                f"## [{title}]({paper_url})",
                "",
                f"**Authors:** {markdown_escape(author_line(paper['authors']))}  ",
                f"**First submitted:** {published} · **Categories:** {markdown_escape(categories)}",
                "",
                markdown_escape(abstract),
                "",
                f"[arXiv abstract]({paper_url}) · [PDF]({paper['pdf_url']})",
            ]
        )
        repositories = paper["github_repositories"]
        if repositories:
            repo_links = []
            for repository in repositories:
                source_fields = ", ".join(str(field) for field in repository["source_fields"])
                repo_links.append(
                    f"[{repository['url']}]({repository['url']}) (arXiv {markdown_escape(source_fields)})"
                )
            lines.append("**Repository listed in arXiv metadata:** " + "; ".join(repo_links))
        else:
            lines.append(
                f"**No repository link in arXiv metadata.** [Search GitHub (not verified)]({paper['github_search_url']})"
            )
        lines.append("")

    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(content)
    temporary_path.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=3, help="Rolling first-submission window (default: 3)")
    parser.add_argument(
        "--categories",
        default=",".join(DEFAULT_CATEGORIES),
        help="Comma-separated arXiv categories (default: %(default)s)",
    )
    parser.add_argument("--api-limit", type=int, default=2000, help="Maximum API results (1-2000)")
    parser.add_argument("--max-papers", type=int, default=100, help="Maximum papers written to the digest")
    parser.add_argument("--markdown", type=Path, default=ROOT / "docs" / "latest.md")
    parser.add_argument("--json", type=Path, default=ROOT / "data" / "latest.json")
    args = parser.parse_args()

    if args.days < 1:
        parser.error("--days must be at least 1")
    if not 1 <= args.api_limit <= MAX_API_RESULTS:
        parser.error(f"--api-limit must be between 1 and {MAX_API_RESULTS}")
    if args.max_papers < 1:
        parser.error("--max-papers must be at least 1")
    args.categories = tuple(category.strip() for category in args.categories.split(",") if category.strip())
    if not args.categories:
        parser.error("--categories must contain at least one category")
    return args


def main() -> int:
    args = parse_args()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=args.days)

    try:
        entries = fetch_entries(args.categories, cutoff, now, args.api_limit)
        papers = collect_papers(entries, cutoff, now, args.max_papers)
    except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError) as error:
        print(f"Could not retrieve or parse the arXiv feed: {error}", file=sys.stderr)
        return 1

    document = {
        "generated_at_utc": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": API_URL,
        "query": {
            "categories": list(args.categories),
            "first_submission_window_days": args.days,
            "cutoff_utc": cutoff.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "api_result_limit": args.api_limit,
            "paper_output_limit": args.max_papers,
        },
        "count": len(papers),
        "papers": papers,
    }
    write_text(args.markdown, render_markdown(papers, now, args.days))
    write_text(args.json, json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(papers)} papers to {args.markdown} and {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
