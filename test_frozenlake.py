from frozenlake import ACTIONS, make_env, optimal_actions, parse_action, render, shortest_path_length


def names(actions):
    return {ACTIONS[a] for a in actions}


def test_start_has_two_optimal_moves_when_not_slippery():
    assert names(optimal_actions(make_env(False), 0)) == {"down", "right"}


def test_oracle_avoids_the_hole():
    # State 4 is below the start; right of it (5) is a hole.
    assert "right" not in names(optimal_actions(make_env(False), 4))


def test_shortest_path_is_six():
    assert shortest_path_length(make_env(False)) == 6


def test_render_marks_agent():
    assert render(make_env(False), 0).splitlines()[0] == "A F F F"


def test_parse_action():
    assert parse_action("I'll go Down.") == ACTIONS.index("down")
    assert parse_action("no idea") is None
