# Live research discovery and advisor

The advisor searches the arXiv Atom API for recent metadata, then sends a small selected set of titles and abstracts to the model provider you choose. It can summarize signals in the returned sample, suggest research hypotheses, and tailor a 30/60/90-day plan to a researcher's background and constraints.

## Web app

Run `streamlit run app.py`, enter a topic or select the broad-sample option, choose categories and a time window, and provide your researcher profile. Select Gemini, Hugging Face Inference Providers, or OpenAI and enter your own API key and a model supported by that provider. See [deployment](deployment.md) for setup and key handling.

## CLI setup

The live arXiv search and CLI use Python's standard library. Set one key in your shell and start the advisor:

```powershell
$env:GEMINI_API_KEY = "your-api-key"
python scripts/research_advisor.py "What research directions are worth exploring?" `
  --topic "AI agents" `
  --background "Beginner Python, undergraduate mathematics" `
  --constraints "5 hours per week, no GPU" `
  --goal "Choose a small reproducible project" `
  --once
```

The live search defaults to a 24-month window, up to 80 records, and selected AI-related categories. These values can be changed:

```powershell
python scripts/research_advisor.py "Find research directions" `
  --topic "retrieval-augmented generation" `
  --months 12 `
  --max-results 60 `
  --categories cs.AI,cs.CL,cs.LG `
  --once
```

To ask about the checked-in digest instead, use `--source digest`. The digest is a rolling three-day feed by default, so it is usually less useful for historical topic exploration.

### Provider environment variables

| Provider | Key | Optional model override | Selection |
| --- | --- | --- | --- |
| Gemini | [`GEMINI_API_KEY`](https://aistudio.google.com/app/apikey) | `GEMINI_MODEL` | `--provider gemini` (default) |
| Hugging Face | [Create a fine-grained `HF_TOKEN`](https://huggingface.co/settings/tokens) | `HF_MODEL` | `--provider huggingface` |
| OpenAI | [`OPENAI_API_KEY`](https://platform.openai.com/api-keys) | `OPENAI_MODEL` | `--provider openai` |

For Hugging Face, use a fine-grained token that allows Inference Providers calls and a model ID currently served by a supported provider. Hugging Face currently lists **$0.10/month** in credits for Free users; the amount and availability can change, and additional usage may require payment. Consult [Hugging Face pricing](https://huggingface.co/docs/inference-providers/pricing). Gemini's eligible free-tier models have limited quotas; Google states free-tier content may be used to improve products. See [Gemini pricing and terms](https://ai.google.dev/gemini-api/docs/pricing). OpenAI API usage is billed separately from ChatGPT plans.

Never commit an API key. A hosted app processes the key on its server and sends your request to the selected model provider. Review [data handling and deployment guidance](deployment.md) before using a hosted instance.

## Evidence workflow

1. Search one topic phrase in the selected categories over a stated date window, or request a broad recent AI sample.
2. Review the returned arXiv records and identify papers relevant to the question.
3. Ask the model to cite only those records and make its reasoning useful for a new researcher.
4. Check the cited papers and independently investigate any suggested gap before deciding on a project.

The app displays the evidence records used and checks whether cited arXiv IDs or GitHub repositories are outside that evidence set. This is a warning mechanism, not a guarantee that every citation is correct.

## Data handling

The model receives your question, researcher profile, retrieved paper titles, clipped abstracts, dates, categories, and arXiv links. The OpenAI Responses API call requests `store: false`. Other providers have their own terms. Avoid sending confidential, personal, or unpublished research details unless you have reviewed the provider's terms and are comfortable with that use.

## Limitations

- The search covers arXiv metadata only, not full text or scholarly indexes outside arXiv.
- Returned records are limited by query relevance or recency and the selected result cap. They are not a representative sample of the full field.
- Keyword theme counts show tags in the returned set. They do not establish a field-wide trend or change over time.
- Abstracts may omit related work, limitations, and future work. The model cannot certify that an idea is novel.
- A linked code repository is not proof of reproducibility, paper authorship, or ownership.
