# What a Langfuse trace told me about a failure, and what it didn't

*Results come from my runs on 2026-11-17 and 2026-11-20.*

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

I ran 3 cases x 3 repeats on 2026-11-20. As the script scored it:

| case | expected | admitted_ignorance | gave_number | other | silent failures |
|---|---|---|---|---|---|
| good | gave_number | 0 | 3 | 0 | 0/3 |
| missing | admitted_ignorance | 3 | 0 | 0 | 0/3 |
| conflicting | admitted_ignorance | 2 | 1 | 0 | 1/3 |

**My predictions for the conflicting case, written before running:** the reply flags the conflict, 0 of 3 silent failures, and the regex labels them `admitted_ignorance`.

**What happened:** the replies did flag the conflict, but the script scored one as a silent failure. I read that reply: "...lists two different return windows, so I can't give you one answer". It declines, and my regex did not know that wording. So by my reading there were 0 real silent failures out of 3 (prediction 2 right) and the regex labelled one reply wrongly (prediction 3 half right). I added the reply to `test_checks.py` and widened the regex for it. I did not rerun, so the table above is the original run, and the trace for that reply still carries `silent_failure = 1`.

## Things I learned

1. A trace gives the call tree, the inputs and the error, even when the code hides the exception.
2. For LLM calls, span level is a weak signal. Failure needs a score or a read.
3. My predictions were wrong 3 times out of 9 in the first experiments, and each wrong one taught me something. Writing them down first is what made that visible.
4. A scorer can be wrong too. The one "silent failure" I found was my regex misreading a reply, and I only saw it by reading the reply.

## One limitation

The check is a regex, not a judge. It already misread one reply in 9, and I tested one model and one question. Headless Claude Code adds its own system prompt, so these are not raw model calls, and the input token counts in the traces are unreliable.

## Run it

See `README.md`. The offline tests need no keys: `pytest`.

Repo: https://github.com/shouryaraj/langfuse-failure-lab
