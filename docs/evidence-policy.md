# Evidence policy

The tracker separates source evidence from claims that require further validation.

## Paper record

Each item is identified by its arXiv ID and links to the arXiv abstract page. Title, authors, abstract, categories, and first-submission date come from the arXiv Atom API response. The generated JSON stores the query and UTC generation time so a digest can be traced to its source and retrieval window.

## Repository links

A repository is included under `github_repositories` only when a GitHub URL appears in the paper's arXiv abstract or author comment. Each link records which metadata field contained it. This is evidence of an explicit link in arXiv metadata, not independent proof of ownership, authorship, completeness, or reproducibility.

When no GitHub URL appears in those fields, the digest may include a GitHub title-search URL. It is labeled **search only — not verified** and is not treated as the paper's code repository.

## What counts as reproduction evidence

This tracker does not clone or execute code and does not compare results with a paper. A future reproduction record should include, at minimum, the repository URL and commit hash, environment and command, data/version details, expected result from the paper, observed result, and a run log or artifact. Until such a record exists, the tracker makes no reproduction claim.

## Scope limits

- The category list is a practical filter, not a complete definition of AI research.
- arXiv metadata and external repository links can change after a digest is generated.
- Missing GitHub links do not mean a paper has no code.
- A linked repository does not establish that its code reproduces the paper.
