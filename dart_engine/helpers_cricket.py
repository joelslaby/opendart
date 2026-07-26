from dart_engine.cricket_stats import (
    build_cricket_marks_by_turn,
)


def _team_side_lookup(teams) -> dict[str, int]:
    return {
        player.name: side
        for side, team in enumerate(teams)
        for player in team.players
    }


def get_game_marks(hist, teams, player):
    return build_cricket_marks_by_turn(
        hist,
        player.name,
        _team_side_lookup(teams),
    )


def get_game_marks_complete(hist, teams, player):
    return build_cricket_marks_by_turn(
        hist,
        player.name,
        _team_side_lookup(teams),
        complete_turns_only=True,
    )


def get_game_marks_sum(hist, teams, player):
    return build_cricket_marks_by_turn(
        hist,
        player.name,
        _team_side_lookup(teams),
        carry_running_total=True,
    )
