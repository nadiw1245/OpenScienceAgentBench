"""Streamlit interface for the live arXiv research advisor."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from research_advisor import (  # noqa: E402
    DEFAULT_MODELS,
    DEFAULT_CATEGORIES,
    INSTRUCTIONS,
    build_initial_message,
    call_chat_api,
    call_responses_api,
    chat_response_text,
    citation_warnings,
    fetch_live_papers,
    make_context,
    response_text,
    select_papers,
)


PROVIDER_OPTIONS = {
    "Gemini": "gemini",
    "Hugging Face Inference Providers": "huggingface",
    "OpenAI": "openai",
}
KEY_NAMES = {
    "gemini": "GEMINI_API_KEY",
    "huggingface": "HF_TOKEN",
    "openai": "OPENAI_API_KEY",
}
MODEL_NAMES = {
    "gemini": "GEMINI_MODEL",
    "huggingface": "HF_MODEL",
    "openai": "OPENAI_MODEL",
}


st.set_page_config(
    page_title="OpenScienceAgentBench",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_arxiv_search(
    topic: str,
    categories: tuple[str, ...],
    months: int,
    max_results: int,
    overview: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return fetch_live_papers(topic, categories, months, max_results, overview)


def ask_model(
    provider: str,
    api_key: str,
    model: str,
    message: str,
) -> str:
    if provider == "openai":
        result = call_responses_api(api_key, model, [{"role": "user", "content": message}])
        return response_text(result)
    result = call_chat_api(
        provider,
        api_key,
        model,
        [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": message},
        ],
    )
    return chat_response_text(result)


with st.sidebar:
    st.header("Model settings")
    provider_label = st.selectbox("AI provider", list(PROVIDER_OPTIONS))
    provider = PROVIDER_OPTIONS[provider_label]
    model_default = os.environ.get(MODEL_NAMES[provider], DEFAULT_MODELS.get(provider, ""))
    model_placeholder = "provider/model-name" if provider == "huggingface" else "Model ID"
    model = st.text_input("Model ID", value=model_default, placeholder=model_placeholder)
    api_key = st.text_input(
        f"{KEY_NAMES[provider]} (never commit this)",
        value=os.environ.get(KEY_NAMES[provider], ""),
        type="password",
        help="The selected model provider receives your prompt, researcher profile, and retrieved paper abstracts.",
    )
    if provider == "huggingface":
        st.caption("Hugging Face currently lists $0.10/month in credits for Free accounts, subject to change. Select a supported provider/model; usage beyond credits can require payment.")
    elif provider == "gemini":
        st.caption("Gemini API free-tier quotas vary by model and can change. Check the provider's current terms before sending unpublished work.")
    else:
        st.caption("OpenAI API usage is billed separately from ChatGPT subscriptions. Check current API pricing before use.")

    st.divider()
    st.caption("Paper retrieval is from arXiv metadata. The model summarizes only the returned sample.")


st.title("OpenScienceAgentBench")
st.subheader("From recent papers to a research direction")
st.write(
    "Search current arXiv records, inspect the papers behind the answer, and get a practical plan matched to your experience and resources."
)
st.info(
    "Research-gap suggestions are hypotheses, not proof of novelty. Review full papers and broader literature before committing to a project.",
    icon="📚",
)

with st.form("research-search"):
    topic = st.text_input("Research topic", value="AI agents", help="Use a short phrase, such as retrieval-augmented generation or medical imaging.")
    question = st.text_area(
        "What do you want help with?",
        value="Summarize recent research directions, identify candidate open questions, and recommend one feasible project for a new researcher.",
        height=110,
    )
    overview = st.checkbox("Search a broad recent AI sample instead of a topic phrase")
    categories = st.multiselect(
        "arXiv categories",
        options=list(DEFAULT_CATEGORIES),
        default=list(DEFAULT_CATEGORIES),
        help="This filter covers selected AI-related categories, not all scholarly research.",
    )
    col_window, col_limit = st.columns(2)
    with col_window:
        months = st.slider("Look back", min_value=1, max_value=60, value=24, format="%d months")
    with col_limit:
        max_results = st.select_slider("Maximum retrieved papers", options=[20, 40, 60, 80, 100], value=80)

    st.markdown("#### Your starting point")
    col_background, col_goal = st.columns(2)
    with col_background:
        background = st.text_input("Background and skills", placeholder="e.g. beginner Python, undergraduate statistics")
        constraints = st.text_input("Time, compute, data, or mentoring limits", placeholder="e.g. 5 hours/week, no GPU")
    with col_goal:
        interests = st.text_input("Specific interests", placeholder="e.g. AI agents for scientific workflows")
        goal = st.text_input("What would you like to achieve?", placeholder="e.g. a reproducible project or first paper")

    submitted = st.form_submit_button("Search papers and build my research plan", type="primary", use_container_width=True)


if submitted:
    st.session_state.pop("latest_research_result", None)
    if not api_key.strip():
        st.error(f"Enter a provider key in the sidebar ({KEY_NAMES[provider]}). The app does not include or provide API keys.")
    elif not model.strip():
        st.error("Enter a model ID supported by the selected provider.")
    elif not categories:
        st.error("Choose at least one arXiv category.")
    elif not overview and not topic.strip():
        st.error("Enter a topic or select the broad recent-sample option.")
    elif not question.strip():
        st.error("Enter the question you want the advisor to answer.")
    else:
        profile = {
            "Interests": interests,
            "Background and skills": background,
            "Constraints (time, compute, data, mentorship)": constraints,
            "Desired outcome": goal,
        }
        try:
            with st.spinner("Searching arXiv and preparing the source-linked evidence..."):
                papers, search_details = cached_arxiv_search(
                    topic.strip(), tuple(categories), months, int(max_results), overview
                )
            if not papers:
                st.warning("No matching papers were returned. Try a shorter phrase, different categories, or a longer window.")
            else:
                context_digest = {
                    "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "query": search_details,
                    "count": len(papers),
                    "papers": papers,
                }
                selected = select_papers(papers, question, profile)
                context = make_context(context_digest, selected)
                prompt = build_initial_message(question, profile, context)
                with st.spinner(f"Asking {provider_label} to synthesize the retrieved papers..."):
                    answer = ask_model(provider, api_key.strip(), model.strip(), prompt)
                warnings = citation_warnings(answer, selected)
                st.session_state["latest_research_result"] = {
                    "answer": answer,
                    "warnings": warnings,
                    "papers": selected,
                    "details": search_details,
                }
        except Exception as error:
            st.error(f"Research request failed: {error}")


result = st.session_state.get("latest_research_result")
if result:
    st.divider()
    st.header("Your research briefing")
    detail = result["details"]
    st.caption(
        f"{detail['returned_count']} arXiv records · {detail['search_mode']} search · "
        f"{detail['date_from_utc'][:10]} to {detail['date_to_utc'][:10]} · "
        f"categories: {', '.join(detail['categories'])}"
    )
    st.markdown(result["answer"])
    if result["warnings"]:
        st.warning("Citation review: " + " | ".join(result["warnings"]))
    st.download_button(
        "Download this briefing as Markdown",
        data=result["answer"],
        file_name="research-roadmap.md",
        mime="text/markdown",
    )
    with st.expander(f"Review the {len(result['papers'])} papers supplied to the advisor"):
        for paper in result["papers"]:
            st.markdown(f"**{paper.get('title', 'Untitled paper')}**")
            st.markdown(
                f"[arXiv:{paper.get('arxiv_id', '')}]({paper.get('arxiv_url', '')}) · "
                f"First submitted {str(paper.get('published', ''))[:10]} · "
                f"{', '.join(paper.get('categories', []))}"
            )
            st.write(paper.get("abstract", ""))
            repositories = paper.get("github_repositories") or []
            if repositories:
                st.caption("GitHub URL listed in arXiv metadata: " + ", ".join(repo["url"] for repo in repositories))
            else:
                st.caption("No GitHub URL found in the arXiv metadata inspected.")
            st.divider()

st.caption(
    "OpenScienceAgentBench is an exploratory aid. The search is limited to arXiv metadata and selected categories; "
    "it does not read full papers, establish novelty, assess paper quality, or verify reproducibility."
)
