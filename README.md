# OpenScienceAgentBench

An arXiv research release tracker and evidence pipeline for open scientific AI. It collects recent papers from AI-related arXiv categories, links each record to its source, records GitHub repositories only when the arXiv metadata explicitly lists them, and includes an AI research advisor for evidence-backed trend questions and research roadmaps.

> A GitHub link in an arXiv record is evidence that the record points to that repository. It does not prove that the repository reproduces the paper's results. This project keeps those claims separate.

## Latest papers

The rolling digest is generated from the arXiv API:

**[Browse the latest digest](docs/latest.md)** · [Machine-readable JSON](data/latest.json)

## What it records

- New version 1 submissions in `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.RO`, `cs.NE`, and `stat.ML`.
- Paper title, authors, abstract, arXiv identifier, categories, and publication date.
- GitHub repositories explicitly linked in the arXiv abstract or author comment, with the metadata field recorded as evidence.
- A GitHub search link when arXiv metadata contains no repository link. Search results are suggestions and are marked as unverified.
- Generation time, query, and category list in the JSON output.
- An interactive advisor that summarizes signals in the digest and proposes a personalized, staged path for a new researcher.

The tracker does not assess paper quality, confirm repository ownership, run experiments, or validate reported results. See [the evidence policy](docs/evidence-policy.md).

## Run locally

Requirements: Python 3.10 or newer. The script uses only the Python standard library.

```powershell
python scripts/update_digest.py
```

By default, the script includes first submissions from the last three days and writes `docs/latest.md` and `data/latest.json`. Customize the time window, categories, or output limit:

```powershell
python scripts/update_digest.py --days 7 --max-papers 150
python scripts/update_digest.py --categories cs.AI,cs.LG,stat.ML
```

The script queries arXiv's Atom API with a maximum of 2,000 results per request. If the API or network is unavailable, it exits with an error and does not replace the current digest.

## Ask the research advisor

The advisor answers questions such as “What trends appear in AI agents?” and can turn your interests, current skills, and available time or compute into a 30/60/90-day roadmap. It cites arXiv papers from the local digest and treats research gaps as hypotheses to investigate. The default provider is Gemini via Google AI Studio's limited free tier.

```powershell
$env:GEMINI_API_KEY = "your-api-key"
python scripts/research_advisor.py
```

It uses Python's standard library. Hugging Face Inference Providers and the OpenAI Responses API can also be selected with `--provider huggingface` or `--provider openai`. Hugging Face currently includes no inference credits for free accounts, so routed calls require purchased credits or an eligible paid plan. Keys and tokens are read from shell environment variables and never saved in the repository. The advisor uses only the current local digest; it does not browse the web. Review [provider setup, evidence limits, and data handling](docs/research-advisor.md) before using it.

## Automatic updates

The GitHub Actions workflow refreshes the digest daily and can also be run from **Actions → Update arXiv digest → Run workflow**. It commits changed digest files to `main`. The workflow needs the repository's Actions setting to allow the workflow token to write contents; the workflow declares only the `contents: write` permission it needs.

## Data sources and scope

- Paper records: [arXiv API](https://info.arxiv.org/help/api/user-manual.html)
- Repository links: URLs present in arXiv API metadata only
- Generated files: [`docs/latest.md`](docs/latest.md) and [`data/latest.json`](data/latest.json)

This release provides the evidence tracker and a digest-grounded research advisor. A reproducible benchmark, scoring protocol, and experiment runner are not implemented yet.

## Contributing

Contributions that improve provenance, search coverage, and reproducibility are welcome. Please keep source links and verification limits explicit. See the [MIT license](LICENSE).
