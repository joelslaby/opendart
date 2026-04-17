CRICKET_NUMBERS = [20, 19, 18, 17, 16, 15, 25]


def cricket_marks(hits: int) -> str:
    if hits <= 0:
        return ""
    if hits == 1:
        return "/"
    if hits == 2:
        return "X"
    if hits == 3:
        return "Ⓧ"
    return "Ⓧ " + "|" * (hits - 3)


def build_cricket_marks_by_turn(
    history: list[dict],
    player_name: str,
    side_lookup: dict[str, int],
    carry_running_total: bool = False,
    complete_turns_only: bool = False,
) -> list[int]:
    remaining = {
        0: {number: 3 for number in CRICKET_NUMBERS},
        1: {number: 3 for number in CRICKET_NUMBERS},
    }

    if complete_turns_only:
        history = history[: len(history) - (len(history) % 3)]

    marks: list[int] = []
    current_turn_marks = 0
    running_total = 0
    last_player = None

    def start_turn() -> None:
        nonlocal current_turn_marks
        current_turn_marks = running_total if carry_running_total else 0
        marks.append(current_turn_marks)

    for hit in history:
        hit_player = hit["player"]

        if hit_player == player_name and hit_player != last_player:
            start_turn()

        number = hit["number"]
        if number in CRICKET_NUMBERS:
            side = side_lookup[hit_player]
            opponent = 1 - side
            hits_remaining = remaining[side][number]

            if hits_remaining > 0:
                applied_hits = min(hit["multiplier"], hits_remaining)
                remaining[side][number] -= applied_hits
                if hit_player == player_name and marks:
                    current_turn_marks += applied_hits

            if (
                hit_player == player_name
                and marks
                and remaining[side][number] == 0
                and remaining[opponent][number] > 0
            ):
                overflow_hits = max(0, hit["multiplier"] - hits_remaining)
                current_turn_marks += overflow_hits

            if marks:
                marks[-1] = current_turn_marks
                running_total = current_turn_marks

        last_player = hit_player

    return [int(mark) for mark in (marks or [0])]
