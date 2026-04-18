from dart_engine.cricket_stats import (
    CRICKET_NUMBERS,
    build_cricket_marks_by_turn,
    cricket_marks,
)


def _player_side_lookup(players) -> dict[str, int]:
    return {player.name: index for index, player in enumerate(players)}


def get_game_marks(hist, players, player):
    return build_cricket_marks_by_turn(
        hist,
        player.name,
        _player_side_lookup(players),
    )


def get_game_marks_complete(hist, players, player):
    return build_cricket_marks_by_turn(
        hist,
        player.name,
        _player_side_lookup(players),
        complete_turns_only=True,
    )


def get_game_marks_sum(hist, players, player):
    return build_cricket_marks_by_turn(
        hist,
        player.name,
        _player_side_lookup(players),
        carry_running_total=True,
    )
