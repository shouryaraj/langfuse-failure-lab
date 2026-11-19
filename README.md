# Langfuse Failure Lab

**For LLMs you need a score, and the score needs checking too.**

Tracing shows where ordinary code fails. An LLM call can fail without raising anything, and the trace then looks healthy. This repo shows that with small experiments, and builds a **Silent-Failure Detector** that scores replies and attaches the score to the Langfuse trace. It also audits the scorer, because a scorer can be wrong too.

Read [`docs/CONCEPT.md`](docs/CONCEPT.md) for the idea, the detector and the results. [`WRITEUP.md`](WRITEUP.md) is the short article.

## What is in here

| File | What it does |
|---|---|
| `demo.py` | Nested `@observe()` functions with a deliberately failing step. Shows a raised exception, then the same failure swallowed by a caller. |
| `llm_demo.py` | One traced LLM call through headless Claude Code (`claude -p`), with full and broken context. |
| `detector.py` | Asks one question under good, missing and conflicting context, scores each reply and attaches the score to its Langfuse trace. |
| `checks.py` | The scoring: plain regex, no LLM judge. |
| `audit.py` | Checks the scorer against hand-labelled replies. Offline. |
| `test_checks.py` | Tests for the scoring. They run offline. |

## Run it

You need Python 3.10+, the [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) on your `PATH`, and a Langfuse project (self-hosted or cloud).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your Langfuse keys
pytest                      # offline, no keys needed
python audit.py             # offline: where does the scorer disagree with a person?
python demo.py              # failing function, one trace
python detector.py --repeats 3
```

`detector.py` makes `3 cases x repeats` Claude calls. They use your Claude Code plan's usage.

## How the detector scores

Each call runs inside its own `@observe()` function, so each reply is its own trace. Two scores are attached:

- `answer_kind` (categorical): `gave_number`, `admitted_ignorance` or `other`.
- `silent_failure` (numeric, 0 or 1): 1 when the context could not support a number and the reply gave one anyway.

In the Langfuse UI, filter traces on `silent_failure = 1` to find the replies that returned normally and looked fine. Then read them: the score is a pointer, not a verdict.

## Limitations

- The check is a regex. It gave one false alarm in the 9-call run, and `audit.py` lists replies it gets wrong in both directions. It is a starting point, not a judge.
- Headless Claude Code adds its own system prompt, so this is not a raw model call. Input token counts in the trace are unreliable for that reason.
- Results come from one model and one question. Do not read them as a general claim about LLM behaviour.
- Tested with `langfuse` 5.2.0 and a self-hosted Langfuse v4. On that setup the score endpoints could not be read over the API, so check scores in the UI.

## License

MIT. See `LICENSE`.
