# Support triage API

Install `pip install -r requirements.txt`, copy `.env.example` to `.env`, then `uvicorn app:app`. POST `/triage` with `{"text":"My invoice is wrong"}`. The closed output is category (billing, technical, account, other), urgency (low, medium, high), suggested team (billing, support, accounts, general), and a short summary.

With `LLM_ENABLED=false`, the API returns a deterministic manual-review fallback without calling a model. To use a model, install Ollama, pull `gemma3:1b`, set `LLM_ENABLED=true`, and restart. Requests are bounded to 30 seconds per attempt, retry timeouts/429/5xx, validate model output, and allow one repair. Logs include model, prompt version, duration, tokens when reported, and repair number. Local Ollama calls have no per-call API charge; electricity and hardware are not estimated.

On 2026-11-05, `gemma3:1b` with prompt version 1.0 classified 8/8 labeled evaluation cases correctly. This small set is only a smoke test, not a general accuracy estimate. One recorded call used 93 input and 42 output tokens, took 7,897 ms, and used no repair; its local API fee was $0. Run `python evals/evaluate.py` against the enabled model to reproduce it. Publication and staged commits remain outstanding.
