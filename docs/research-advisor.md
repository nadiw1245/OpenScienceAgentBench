# Research trends and roadmap advisor

The advisor answers questions about the local arXiv digest and helps a new researcher compare practical directions. It can personalize a 30/60/90-day roadmap using interests, skills, goals, and constraints such as limited compute or data access.

## Setup

The default provider is Gemini through Google AI Studio. Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey), then set it in your shell. Gemini's OpenAI-compatible chat endpoint lets the advisor use Python's standard library; no package installation is required. The default model is `gemini-3.8-flash` and can be changed with `GEMINI_MODEL` or `--model`.

PowerShell:

```powershell
$env:GEMINI_API_KEY = "your-api-key"
# Optional: pick another model available to your API key.
$env:GEMINI_MODEL = "your-model-id"
```

Start the interactive advisor:

```powershell
python scripts/research_advisor.py
```

Gemini currently offers limited free-tier usage for eligible models, subject to quotas and changes. On Google's free tier, prompts and responses may be used to improve its products; do not submit confidential or unpublished research. Review the [current Gemini API pricing and free-tier terms](https://ai.google.dev/gemini-api/docs/pricing) before use.

### Other providers

Hugging Face Inference Providers are also supported. Create a fine-grained token with the **Make calls to Inference Providers** permission in [Hugging Face token settings](https://huggingface.co/settings/tokens). Free Hugging Face accounts currently have no included Inference Providers credits; routed requests require purchased credits or an eligible paid plan. Choose a model served by an Inference Provider and set both values:

```powershell
$env:HF_TOKEN = "your-hugging-face-token"
$env:HF_MODEL = "provider/model-id"
python scripts/research_advisor.py --provider huggingface
```

The OpenAI Responses API remains available as another option:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
python scripts/research_advisor.py --provider openai
```

To choose a different model, use the provider-specific variable (`GEMINI_MODEL`, `HF_MODEL`, or `OPENAI_MODEL`) or pass `--model`. API tokens and keys are read from environment variables and must not be committed to the repository.

## Asking questions

The advisor asks what you want to know, then optionally asks about your interests, background, available time/compute/data/mentorship, and goal. In an interactive session you can ask follow-up questions; type `quit` to end.

You can also provide a direct question and profile on the command line:

```powershell
python scripts/research_advisor.py "What trends appear in AI agents?" `
  --background "Beginner in Python, undergraduate mathematics" `
  --constraints "5 hours per week, no GPU" `
  --goal "Choose a small reproducible project"
```

Use `--once` to return one answer without follow-up chat, `--interests` to target a topic, or `--digest path/to/latest.json` to choose a different snapshot. Set `RESEARCH_ADVISOR_PROVIDER` to `gemini`, `huggingface`, or `openai` to change the default provider.

## Evidence and data handling

The advisor reads `data/latest.json`, selects up to 30 relevant papers, and sends their titles, clipped abstracts, categories, arXiv IDs, and your prompt/profile to the selected model provider. The OpenAI Responses API request sets `store: false`; Gemini and Hugging Face use their chat-completions APIs and follow those providers' own data terms. Check the terms for your chosen provider before sending private information.

The theme counts are keyword-based hints from a single snapshot, not statistical proof of a field-wide trend or growth over time. The advisor is instructed to cite only arXiv IDs in the selected digest, label possible gaps as hypotheses, and recommend checking full papers before committing to a direction. The CLI warns when an answer cites an arXiv ID or GitHub repository outside the selected records. It does not browse the web or verify whether a code repository reproduces a paper.

The current GitHub Actions workflow only refreshes the paper digest; it does not call the advisor or require an API secret.
