# What a Langfuse trace told me about a failure, and what it didn't

*Draft. Sections marked TODO need results from `detector.py`, which has not been run yet. Everything else comes from my runs on 2026-11-17.*

I wanted to know whether tracing can explain a failed execution. I started with a Python function that fails on purpose and worked up to an LLM call that fails without raising anything.

## Four ideas that did the work

- A **trace** is the record of one run. A **span** is one timed step inside it. Spans nest, so a trace is a tree of who called whom.
- Each span can carry **inputs and outputs**. That is what a plain traceback lacks.
- An exception is recorded on the span where it was **raised**, whether or not a caller catches it.
- A **score** is a judgement you attach to a trace after the fact. It is how you find a bad answer when nothing raised an error.

## 1. A function that raises

`main` calls `price_per_item`, which calls `parse_order` and then `validate_quantity`. With `quantity: 0`, `validate_quantity` raises `ValueError: quantity must be > 0`.

I predicted `parse_order` would be the error span. I was wrong: it returns `0` before validation runs, so it stays clean. The trace showed the failing span, the message and the input in one view. The plain traceback showed none of the inputs.

What the trace did not show was where the `0` came from. It shows where a bad value flows, not where it entered.

## 2. The same error, swallowed

I wrapped the call in `try/except ValueError: return None`. The program printed `None` and exited with code 0.

I predicted `validate_quantity` would no longer show an error. I was wrong again: the error stays on the span where it was raised. `price_per_item` and `main` looked fine. So the failure is in the trace, but only inside the span tree. A view that shows only the top-level status would report success.

## 3. A model call that raises nothing

I asked a shop-policy question through headless Claude Code, once with the return-window line in the policy and once without. I predicted the model would invent an answer. It said "I don't have a return window in the shop policy... I don't want to guess."

Both calls returned normally and both spans were `DEFAULT` level. The two traces had the same shape and differed only in content. With an LLM, a bad or missing answer is not an error, so the span level says little. You have to read the content or score it.

## 4. Scoring it: the Silent-Failure Detector

`detector.py` runs the same question under good, missing and conflicting context. A regex labels each reply `gave_number`, `admitted_ignorance` or `other`. A second score, `silent_failure`, is 1 when the context could not support a number and the reply gave one anyway. Both scores attach to the trace, so a filter on `silent_failure = 1` finds replies that looked fine.

TODO: results table, 3 cases x 3 repeats, from `python detector.py --repeats 3`.

TODO: my predictions for the conflicting case, written before running, next to what happened.

## Three things I learned

1. A trace gives the call tree, the inputs and the error, even when the code hides the exception.
2. For LLM calls, span level is a weak signal. Failure needs a score or a read.
3. My predictions were wrong 3 times out of 9, and each wrong one taught me something. Writing them down first is what made that visible.

## One limitation

The check is a regex, not a judge. It will misread unusual wording, and I tested one model and one question. Headless Claude Code adds its own system prompt, so these are not raw model calls, and the input token counts in the traces are unreliable.

## Run it

See `README.md`. The offline tests need no keys: `pytest`.

TODO: repo link.
