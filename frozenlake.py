"""FrozenLake helpers: the environment, the optimal-move oracle and a reply parser. No LLM here."""
import re
from collections import deque

import gymnasium as gym

ACTIONS = ["left", "down", "right", "up"]
ACTION_WORD = re.compile(r"\b(left|down|right|up)\b", re.IGNORECASE)
MOVES = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # (row, col) per action


def make_env(slippery):
    return gym.make("FrozenLake-v1", map_name="4x4", is_slippery=slippery)


def desc_rows(env):
    return ["".join(c.decode() for c in row) for row in env.unwrapped.desc]


def optimal_actions(env, state, gamma=0.99, sweeps=500):
    """Actions with the best value under value iteration. Ties all count as optimal."""
    P = env.unwrapped.P

    def q(s, V):
        return [sum(p * (r + gamma * V[s2] * (not done)) for p, s2, r, done in P[s][a]) for a in range(4)]

    V = [0.0] * len(P)
    for _ in range(sweeps):
        V = [max(q(s, V)) for s in range(len(P))]
    qs = q(state, V)
    return {a for a, v in enumerate(qs) if v >= max(qs) - 1e-9}


def shortest_path_length(env):
    """Fewest moves from start to goal if the ice never slipped (BFS on the map)."""
    rows = desc_rows(env)
    n = len(rows)
    queue, seen = deque([(0, 0, 0)]), {(0, 0)}
    while queue:
        r, c, d = queue.popleft()
        if rows[r][c] == "G":
            return d
        for dr, dc in MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and rows[nr][nc] != "H" and (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append((nr, nc, d + 1))


def render(env, state):
    """The map as text with the agent marked A."""
    n = len(desc_rows(env))
    grid = [list(row) for row in desc_rows(env)]
    grid[state // n][state % n] = "A"
    return "\n".join(" ".join(row) for row in grid)


def parse_action(reply):
    """Index of the first action word in the reply, or None."""
    m = ACTION_WORD.search(reply)
    return ACTIONS.index(m.group(1).lower()) if m else None
