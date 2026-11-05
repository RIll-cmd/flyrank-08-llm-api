# Support triage API

## Current submission contract (version 1.1)

This version extends the SQLite task API with `/triage`. `JOB-CARD.md` defines the job. It loads `prompts/triage-v1.1.md`, which includes the full schema, rules, uncertainty behavior and two examples. The prompt and user input are sent in separate system/user messages through Ollama's chat endpoint.

`LLM_STUB=1` always returns a schema-valid fallback without a model call, even when `LLM_ENABLED=true`. `LLM_ENABLED=false` remains the kill switch. The default model is now `qwen3-vl:4b-instruct`; pull it with Ollama before enabling the model. The earlier gemma3 results below are historical.

A second invalid response after one repair returns 422 and writes input, raw output, error and prompt version to `logs/quarantine.jsonl`. This local log is gitignored and may contain sensitive input. Unknown output fields are forbidden. Each attempt has a 30-second timeout; only timeouts, 429 and 5xx are retried with backoff/jitter.

Live evaluation on 2026-11-05 with prompt 1.1 and Qwen: category **8/8**; category+urgency+team and summary shape **7/8**. The profile-update case missed one non-category field. Summary factual quality is not mechanically graded. Run `python evals/evaluate.py`; `BASE_URL` can select a different port. This is a small in-sample check.

```sh
curl -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d '{"text":"Please send my invoice"}'
curl -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d '{"text":""}'
```

The invalid request returns 400 naming text before calling the provider. Stub output is `{"category":"other","urgency":"medium","suggested_team":"general","summary":"Manual review required"}`. The instructions below describe the initial version where they differ from this section.

Install `pip install -r requirements.txt`, copy `.env.example` to `.env`, then `uvicorn app:app`. POST `/triage` with `{"text":"My invoice is wrong"}`. The closed output is category (billing, technical, account, other), urgency (low, medium, high), suggested team (billing, support, accounts, general), and a short summary.

With `LLM_ENABLED=false`, the API returns a deterministic manual-review fallback without calling a model. To use a model, install Ollama, pull `gemma3:1b`, set `LLM_ENABLED=true`, and restart. Requests are bounded to 30 seconds per attempt, retry timeouts/429/5xx, validate model output, and allow one repair. Logs include model, prompt version, duration, tokens when reported, and repair number. Local Ollama calls have no per-call API charge; electricity and hardware are not estimated.

On 2026-11-05, `gemma3:1b` with prompt version 1.0 classified 8/8 labeled evaluation cases correctly. This small set is only a smoke test, not a general accuracy estimate. One recorded call used 93 input and 42 output tokens, took 7,897 ms, and used no repair; its local API fee was $0. Run `python evals/evaluate.py` against the enabled model to reproduce it. The original stage-by-stage commit history remains incomplete.

Example with the enabled model:

```sh
curl -X POST http://127.0.0.1:8000/triage -H "Content-Type: application/json" -d '{"text":"My credit card was charged twice for this month"}'
```

Observed response: `{"category":"billing","urgency":"high","suggested_team":"support","summary":"Payment issue"}`. The eight-case score grades category only; the suggested team and urgency still need a human-quality evaluation.
