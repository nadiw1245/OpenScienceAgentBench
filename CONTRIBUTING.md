# Contributing

Thank you for helping improve OpenScienceAgentBench. Contributions that strengthen source coverage, evidence quality, accessibility, and reproducibility are welcome.

## Before opening an issue

- Search existing issues to avoid duplicates.
- For tracker problems, include the arXiv ID, query options, and approximate time of retrieval.
- For advisor problems, include the selected provider and model name, but never include API keys, tokens, or private prompts.
- Separate observed behavior from assumptions about a paper, author, or repository.

## Proposing a change

1. Open an issue for substantial changes so the scope can be discussed.
2. Keep pull requests focused and describe the user-visible effect.
3. Include source links for factual changes to paper metadata or provider behavior.
4. Update relevant documentation when a command, environment variable, provider, or limitation changes.
5. Do not add credentials, private data, or generated claims that cannot be traced to a source.

## Evidence standards

- Record a GitHub repository as explicitly linked only when the arXiv metadata contains that link.
- Keep search suggestions labeled as unverified.
- Do not describe a repository as reproducing a paper unless the run, commit, environment, command, data version, expected result, and observed result are recorded.
- Treat the advisor's keyword counts as snapshot hints, not statistical evidence of a trend over time.

## Local workflow

The tracker and command-line advisor use Python's standard library. The Streamlit app uses the dependency in `requirements.txt`. Set up the web app locally with:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Refresh the digest with:

```powershell
python scripts/update_digest.py
```

Review generated changes in `docs/latest.md` and `data/latest.json` before including them in a pull request. Never commit API keys or tokens. See [SECURITY.md](SECURITY.md) for vulnerability reports.
