# Research methodology and responsible use

This document describes what OpenScienceAgentBench can support and what a researcher must verify independently.

## Search design

- The live topic search queries the arXiv `all` field (title, abstract, and searchable metadata) for a phrase, selected AI-related categories, and a submitted-date interval.
- Broad mode omits the topic phrase and requests the latest records in those categories.
- Results are ranked by relevance for a topic query and by submission date for broad mode. The app asks for no more than 100 results and defaults to 80.
- The returned set is a convenient starting sample. It is not exhaustive, randomly sampled, or representative of all work in a field.
- The daily digest uses a separate rolling first-submission query and stores its parameters with its records.

The search follows the documented arXiv API syntax. See the [arXiv API User's Manual](https://info.arxiv.org/help/api/user-manual.html) for query fields and date filtering.

## Interpreting themes and trends

The advisor can group records with hand-written keyword tags and summarize the returned sample. Those counts can help a newcomer navigate a search, but the system has not established a controlled trend-measurement method. To claim that an area is growing, define a stable query and category scope, preserve comparable dated snapshots, account for duplicates and category changes, and measure counts or proportions across multiple windows. This version does not make that claim.

## Finding research questions

Use three labels when reviewing a candidate problem:

1. **Author-stated limitation or future work:** explicitly stated in the full paper. An abstract alone may not include it.
2. **Advisor-generated hypothesis:** an idea inferred from patterns or omissions in the retrieved sample. It may already be solved elsewhere.
3. **Validated open question:** a question checked against recent related work, surveys, proceedings, code, datasets, and feedback from an experienced researcher. This app does not perform or certify this validation.

Before choosing a gap, read the relevant full papers, search synonyms and adjacent fields, inspect related-work sections and citations, and ask a supervisor or subject expert. Then write a narrow question that can be answered with available data and compute.

## Turning a topic into a plan

A strong beginner project usually starts with a reproducible baseline and a measurable question:

- **First week:** select a narrow question, read a recent survey and several relevant papers, and record terms, methods, data, and evaluation measures.
- **First month:** reproduce one appropriate baseline or verify its published implementation; define a dataset split and success metric.
- **Second month:** run one controlled variation, ablation, or robustness check. Keep an experiment log and compare against the baseline.
- **Third month:** repeat the key result, document limitations, assess whether the evidence answers the question, and decide to continue, narrow, or switch.

Model-generated plans are starting points. Adapt them to local ethics requirements, domain knowledge, data licenses, safety concerns, and supervisor guidance.
