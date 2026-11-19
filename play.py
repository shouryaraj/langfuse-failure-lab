"""FrozenLake with a random or LLM policy, traced in Langfuse.

One trace per episode, one span per move. Scores: success, optimal_move (per move),
step_accuracy, extra_steps, looped (per episode).

    python play.py --policy random --episodes 20
    python play.py --policy llm --episodes 5 --slippery
"""
import argparse
import random

from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client, observe, propagate_attributes

from frozenlake import ACTIONS, make_env, optimal_actions, parse_action, render, shortest_path_length
from llm_demo import ask_claude

SYSTEM = "You control an agent on a frozen lake. Reply with exactly one word: left, down, right or up."
QUESTION_TEXT = (
    "Map: S start, F frozen (safe), H hole (episode ends, you lose), G goal. A is you.\n"
    "Reach G without stepping on H. Moves are left, down, right, up. Which move?"
)


def random_policy(env, state, model=None):
    return random.randrange(4), "random"


def llm_policy(env, state, model=None):
    reply = ask_claude(render(env, state), QUESTION_TEXT, system=SYSTEM, model=model)
    action = parse_action(reply)
    if action is None:  # unparseable reply: fall back to random, and say so
        return random.randrange(4), f"invalid reply: {reply!r}"
    return action, reply


POLICIES = {"random": random_policy, "llm": llm_policy}


@observe(capture_input=False)
def decide(policy, env, state, model):
    action, reply = POLICIES[policy](env, state, model)
    best = optimal_actions(env, state)
    get_client().score_current_span(
        name="optimal_move", value=1.0 if action in best else 0.0, data_type="NUMERIC",
        comment=f"chose {ACTIONS[action]}, optimal {sorted(ACTIONS[a] for a in best)}",
    )
    return {"action": action, "optimal": action in best, "reply": reply}


@observe(capture_input=False)
def run_episode(policy, env, seed, max_steps, slippery, model):
    meta = {"policy": policy, "model": str(model), "slippery": str(slippery), "seed": str(seed)}
    state, _ = env.reset(seed=seed)
    visited, optimal_hits, steps, reward = [state], 0, 0, 0.0
    with propagate_attributes(trace_name=f"frozenlake:{policy}", tags=[str(model)], metadata=meta):
        for _ in range(max_steps):
            decision = decide(policy, env, state, model)
            state, reward, terminated, truncated, _ = env.step(decision["action"])
            steps += 1
            optimal_hits += decision["optimal"]
            visited.append(state)
            if terminated or truncated:
                break
    success = reward == 1.0
    looped = len(set(visited)) < len(visited)
    client = get_client()
    client.score_current_trace(name="success", value=1.0 if success else 0.0, data_type="NUMERIC")
    client.score_current_trace(name="step_accuracy", value=optimal_hits / steps, data_type="NUMERIC")
    client.score_current_trace(name="looped", value=1.0 if looped else 0.0, data_type="NUMERIC")
    extra = steps - shortest_path_length(env) if success else None
    if extra is not None:
        client.score_current_trace(name="extra_steps", value=float(extra), data_type="NUMERIC")
    return success, optimal_hits / steps, looped, extra


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=list(POLICIES), default="random")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--slippery", action="store_true")
    parser.add_argument("--model", help="claude model alias, e.g. haiku or sonnet")
    parser.add_argument("--max-steps", type=int, default=20)
    args = parser.parse_args()

    env = make_env(args.slippery)
    results = []
    try:
        for i in range(args.episodes):
            res = run_episode(args.policy, env, i, args.max_steps, args.slippery, args.model)
            results.append(res)
            print(f"episode {i + 1}: success={res[0]} step_accuracy={res[1]:.2f} looped={res[2]} extra_steps={res[3]}")
    finally:
        get_client().flush()

    n = len(results)
    wins = sum(r[0] for r in results)
    print("\n| policy | slippery | episodes | success | mean step accuracy | looped |")
    print("|---|---|---|---|---|---|")
    print(
        f"| {args.policy}/{args.model} | {args.slippery} | {n} | {wins}/{n} "
        f"| {sum(r[1] for r in results) / n:.2f} | {sum(r[2] for r in results)}/{n} |"
    )


if __name__ == "__main__":
    main()
