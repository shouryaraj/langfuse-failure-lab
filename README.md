# Langfuse Failure Lab

Can tracing help explain a failed execution? This repo holds the experiments from one week of finding out, and a small tool, the **Silent-Failure Detector**, for the case where nothing raises an error.

## What is in here

| File | What it does |
|---|---|
| `demo.py` | Nested `@observe()` functions with a deliberately failing step. Shows a raised exception, then the same failure swallowed by a caller. |
| `llm_demo.py` | One traced LLM call through headless Claude Code (`claude -p`), with full and broken context. |
| `detector.py` | Asks one question under good, missing and conflicting context, scores each reply and attaches the score to its Langfuse trace. |
| `checks.py` | The scoring: plain regex, no LLM judge. |
| `test_checks.py` | Tests for the scoring. They run offline. |

## Run it

You need Python 3.10+, the [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) on your `PATH`, and a Langfuse project (self-hosted or cloud).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your Langfuse keys
pytest                      # offline, no keys needed
python demo.py              # failing function, one trace
python detector.py --repeats 3
```

`detector.py` makes `3 cases x repeats` Claude calls. They use your Claude Code plan's usage.

## How the detector scores

Each call runs inside its own `@observe()` function, so each reply is its own trace. Two scores are attached:

- `answer_kind` (categorical): `gave_number`, `admitted_ignorance` or `other`.
- `silent_failure` (numeric, 0 or 1): 1 when the context could not support a number and the reply gave one anyway.

In the Langfuse UI, filter traces on `silent_failure = 1` to find the replies that returned normally and looked fine.

## Limitations

- The check is a regex. A reply that declines in unusual wording is scored `other`, and a reply that mentions a number while declining can be misread. It is a starting point, not a judge.
- Headless Claude Code adds its own system prompt, so this is not a raw model call. Input token counts in the trace are unreliable for that reason.
- Results come from one model and one question. Do not read them as a general claim about LLM behaviour.

## License

MIT. See `LICENSE`.
