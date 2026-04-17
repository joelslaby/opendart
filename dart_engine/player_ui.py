import os


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
PROFILE_PIC_DIR = "profile_pics"


def format_hit_label(number: int, multiplier: int) -> str:
    if multiplier == 3:
        return f"T{number}"
    if multiplier == 2:
        return f"D{number}"
    return str(number)


def get_profile_pic_path(player_name: str, search_dir: str = PROFILE_PIC_DIR) -> str:
    default_path = os.path.abspath(os.path.join(search_dir, "default.png"))
    match_path = None

    for root, _, files in os.walk(search_dir):
        for fname in files:
            if player_name in fname and fname.lower().endswith(IMAGE_EXTENSIONS):
                match_path = os.path.abspath(os.path.join(root, fname))
                break
        if match_path:
            break

    return match_path or default_path


def build_player_turn_summary(dart_history, players_in_order, active_player_name):
    turns_by_player = {player.name: [] for player in players_in_order}
    current_player = None
    current_turn = []

    for hit in dart_history:
        if hit["player"] != current_player:
            if current_player is not None and current_player in turns_by_player:
                turns_by_player[current_player].append(current_turn)
            current_player = hit["player"]
            current_turn = []
        current_turn.append(format_hit_label(hit["number"], hit["multiplier"]))

    if current_player in turns_by_player:
        turns_by_player[current_player].append(current_turn)

    last_turn_player = current_player
    focus_player = (
        last_turn_player
        if last_turn_player and last_turn_player != active_player_name
        else active_player_name
    )
    next_player_flag = bool(last_turn_player and last_turn_player != active_player_name)

    summary = {}
    for player in players_in_order:
        turns = turns_by_player[player.name]
        if player.name == focus_player:
            current_hits = turns[-1] if turns else []
            previous_hits = turns[-2] if len(turns) > 1 else []
        else:
            current_hits = []
            previous_hits = turns[-1] if turns else []

        summary[player.name] = {
            "current_hits": current_hits,
            "previous_hits": previous_hits,
        }

    return {
        "focus_player": focus_player,
        "next_player_flag": next_player_flag,
        "players": summary,
    }
