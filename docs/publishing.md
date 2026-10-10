# Publishing and sharing

Use this checklist when preparing a public repository update. Clear provenance and a working first-run experience help people decide whether the project fits their needs; no repository setup can guarantee stars or citations.

## Repository profile

Suggested GitHub description:

> Search arXiv AI papers and get an evidence-linked research roadmap tailored to your experience and resources.

Suggested topics:

`arxiv` · `ai-research` · `open-science` · `literature-review` · `research-tools` · `research-advisor` · `streamlit`

Avoid describing this release as a validated research benchmark or reproduction system. Those capabilities are future work, not current features.

## Before announcing an update

1. Push the source, documentation, and generated digest to the default branch.
2. Deploy `app.py` from the GitHub repository on [Streamlit Community Cloud](https://share.streamlit.io/) using [the deployment guide](deployment.md). Add the live app URL to the repository website field and README after checking that it works.
3. Confirm the scheduled digest workflow is allowed to write repository contents, then run it once from **Actions** and review the result.
4. Check that the digest generation date and links look current.
5. Add a GitHub release only after reviewing the published version and its limitations.
6. Share a concrete demo: one topic query, the papers used as evidence, and the resulting roadmap.

The README banner is [`assets/social-preview.svg`](../assets/social-preview.svg). It also appears at the top of the repository README.

## Announcement draft

> I built OpenScienceAgentBench to help new researchers explore recent AI papers on arXiv. Search a topic, inspect the source records, and use an AI advisor to map a feasible project to your skills and resources. Suggested research gaps are hypotheses that need a broader literature review. Feedback on paper discovery and the research-planning workflow is welcome.

Adapt the draft to the venue and follow its community rules. Share a working example and invite specific feedback rather than asking for stars.
