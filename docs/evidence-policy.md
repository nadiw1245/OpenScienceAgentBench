# Evidence policy

OpenScienceAgentBench keeps source records separate from claims that require further validation.

## Paper records

For live search and the daily digest, arXiv supplies the paper ID, title, authors, abstract, category, and submission dates. The live search stores its topic, query, selected categories, time window, result limit, sort order, and retrieval count for the advisor's context. Each record links to its arXiv abstract and PDF pages.

The app displays the arXiv records and abstracts sent to the model. Its citation check flags arXiv IDs and GitHub repository URLs outside that supplied record set. This is a basic warning, not a semantic check that a cited paper supports a claim.

## Repository links

A repository is included under `github_repositories` only when a GitHub URL appears in the paper's arXiv abstract or author comment. Each link records which metadata field contained it. This proves only that the arXiv record contained a link—not ownership, authorship, completeness, or reproducibility.

When no GitHub URL appears in those fields, a GitHub title-search URL can be offered as an unverified suggestion. It must not be presented as the paper's confirmed code repository.

## Research gaps and trends

- An explicitly stated limitation or future direction must be checked in the paper itself; abstracts may omit these details.
- A model-suggested gap is a hypothesis, not an established open problem or novelty claim.
- Theme labels are keyword-based navigation hints and do not show statistical trends.
- The bounded arXiv sample is not a systematic review and cannot prove novelty. Search broader literature and consult domain experts before committing to a gap.

## What counts as reproduction evidence

This tracker does not clone or execute code or compare results with a paper. A future reproduction record should include the repository URL and commit hash, environment and command, data/version details, expected result from the paper, observed result, and a run log or artifact. Until then, the project makes no reproduction claim.
