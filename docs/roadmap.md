# Project roadmap

This roadmap records project directions; it is not a promise of delivery dates. The current release is a paper discovery and planning aid, not a validated research benchmark or paper-reproduction platform.

## Available now

- Search arXiv live by topic or browse a broad recent sample from selected AI categories.
- Use the Streamlit interface or command-line advisor with Gemini, Hugging Face Inference Providers, or OpenAI.
- Review the retrieved papers and generate a personalized project plan.
- Browse a daily arXiv digest as Markdown and JSON.
- Keep repository links and unverified GitHub title-search suggestions distinct.

## Improve search quality

- Add explicit AND/OR query controls and author/category facets.
- Compare retrieval methods against a published evaluation set with human-reviewed relevance labels.
- Explore broader scholarly metadata sources while keeping source provenance visible.
- Add export formats for researcher notes and literature matrices.

## Measure research trends

- Preserve date-stamped snapshots for a stable set of categories and query definitions.
- Define deduplication and category-change handling before comparing time windows.
- Report counts with methods and caveats; do not label keyword counts as statistical evidence.

## Strengthen code evidence

- Check whether explicitly linked repositories are reachable and record when checked.
- Record repository commit hashes when a reproduction is attempted.
- Document the environment, command, data/version details, expected result, observed result, and run artifact.
- Keep verified reproduction status separate from the presence of a repository link.

## Evaluate the advisor

- Build a reviewed set of research questions and expected source records.
- Measure search coverage and citation correctness before evaluating usefulness or answer quality.
- Include early-career researchers and domain experts in usability review.
- Document limitations before describing any evaluation as a benchmark.

Community contributions are welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md).
