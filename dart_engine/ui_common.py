import json
import os
from typing import Callable

from tkinter import filedialog


DEFAULT_PLAYERS = ["Jacob", "Joel", "Dustin", "Ravi"]


def load_app_config(config_file: str) -> tuple[str | None, list[str]]:
    if not os.path.exists(config_file):
        return None, DEFAULT_PLAYERS.copy()

    with open(config_file, "r") as file:
        data = json.load(file)

    folder_path = data.get("last_folder")
    player_options = data.get("player_options", DEFAULT_PLAYERS)
    return folder_path, list(player_options)


def update_app_config(config_file: str, **updates) -> dict:
    data = {}
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            data = json.load(file)

    data.update(updates)

    with open(config_file, "w") as file:
        json.dump(data, file)

    return data


def choose_save_directory(current_folder: str | None) -> str | None:
    return filedialog.askdirectory(
        title="Select a Directory to Save",
        initialdir=current_folder or os.getcwd(),
    ) or None


def ask_history_save_path() -> str | None:
    return filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Documents", "*.json"), ("All Files", "*.*")],
    ) or None


def ask_history_load_path(current_folder: str | None = None) -> str | None:
    return filedialog.askopenfilename(
        title="Select a File",
        initialdir=current_folder or os.getcwd(),
        filetypes=(
            ("JSON files", "*.json"),
            ("All files", "*.*"),
        ),
    ) or None


def save_dart_history(file_path: str, dart_history: list[dict]) -> None:
    with open(file_path, "w") as file:
        json.dump({"dart_history": dart_history}, file, indent=2)


def load_dart_history(file_path: str) -> list[dict]:
    with open(file_path, "r") as file:
        return json.load(file)["dart_history"]


def infer_player_turn_order(dart_history: list[dict], expected_players: int) -> list[str]:
    players = []
    last_player = None

    for hit in dart_history:
        player = hit["player"]
        if player != last_player and player not in players:
            players.append(player)
            if len(players) == expected_players:
                break
        last_player = player

    return players


def add_player_option(player_options: list[str], name: str | None) -> bool:
    if not name or name in player_options:
        return False

    player_options.append(name)
    return True


def replay_dart_history(
    dart_history: list[dict],
    *,
    reset_game: Callable[[], None],
    clear_all_markers: Callable[[], None],
    draw_marker: Callable[[dict], None],
    register_hit: Callable[[dict], None],
    clear_turn_markers: Callable[[], None],
    is_turn_complete: Callable[[], bool],
) -> None:
    reset_game()
    clear_all_markers()

    for hit in dart_history:
        draw_marker(hit)
        register_hit(hit)
        if is_turn_complete():
            clear_turn_markers()
