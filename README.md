# Langfuse Failure Lab

**For LLMs you need a score, and the score needs checking too.**

A trace shows where ordinary code fails. An LLM call can fail without raising anything, and the trace then looks healthy. This repo shows that, and scores the replies so you can find the bad ones.

## The idea in four lines

1. Ask a shop-policy question: "How many days do I have to return an item?"
2. Change the policy: return window present, missing, or contradicting itself.
3. A regex scores each reply and attaches the score to its Langfuse trace.
4. Check the scorer against replies a person has read, because it can be wrong too.

## Run it

Needs Python 3.10+, the [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) and a Langfuse project.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your Langfuse keys
pytest                      # offline
python audit.py             # offline: where does the scorer fail?
python detector.py --repeats 3
```

The detector makes `3 x repeats` Claude calls on your plan. Use `--cases conflicting` to run one case.

## Files

- `detector.py`: runs the cases and attaches scores
- `checks.py`: the scoring regex
- `audit.py`: checks the scorer
- `demo.py`, `llm_demo.py`: the traced failure demos
- `concepts/`: [how it works](concepts/how-it-works.md) and [terminology](concepts/terminology.md)
- `WRITEUP.md`: the short article

## Limits

One model, one question. The check is a regex and can be wrong in both directions. Headless Claude Code adds its own system prompt, so token counts are unreliable. Scores could not be read over the API on a self-hosted Langfuse v4, so check them in the UI.

MIT license.
