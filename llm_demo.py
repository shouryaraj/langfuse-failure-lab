import json
import subprocess
import tempfile

from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client, observe

SYSTEM_PROMPT = "You are a customer support assistant for an online shop."

POLICY_FULL = """Shop policy:
- Standard shipping takes 3-5 business days.
- Items can be returned within 30 days of delivery.
- Gift cards are not refundable."""

# Same policy with the return-window line removed on purpose.
POLICY_BROKEN = """Shop policy:
- Standard shipping takes 3-5 business days.
- Gift cards are not refundable."""

QUESTION = "How many days do I have to return an item?"


@observe(as_type="generation")
def ask_claude(context, question):
    prompt = f"{context}\n\nQuestion: {question}"
    # Neutral cwd so a project CLAUDE.md is not picked up; tools off so it is a plain model call.
    with tempfile.TemporaryDirectory() as cwd:
        proc = subprocess.run(
            [
                "claude", "-p", prompt,
                "--output-format", "json",
                "--tools", "",
                "--system-prompt", SYSTEM_PROMPT,
                "--no-session-persistence",
            ],
            capture_output=True, text=True, cwd=cwd, timeout=120,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr[:300]}")
    data = json.loads(proc.stdout)
    usage = data.get("usage", {})
    get_client().update_current_generation(
        input=prompt,
        output=data.get("result"),
        model=next(iter(data.get("modelUsage", {})), None),
        usage_details={
            "input": usage.get("input_tokens"),
            "output": usage.get("output_tokens"),
        },
        metadata={"raw_keys": sorted(data.keys()), "cost_usd": data.get("total_cost_usd")},
    )
    return data["result"]


@observe()
def run(label, context):
    answer = ask_claude(context, QUESTION)
    print(f"[{label}] {answer}\n")
    return answer


if __name__ == "__main__":
    try:
        run("full context", POLICY_FULL)
        run("broken context", POLICY_BROKEN)
    finally:
        get_client().flush()
