from __future__ import annotations

import json
import os
import random
from typing import Callable

import tkinter as tk
from tkinter import filedialog

from dart_engine.helpers_general import classify_miss_zone


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


def save_dart_history(file_path: str, dart_history: list[dict], metadata: dict | None = None) -> None:
    payload = {"dart_history": dart_history}
    if metadata:
        payload["metadata"] = metadata
    with open(file_path, "w") as file:
        json.dump(payload, file, indent=2)


def load_saved_game(file_path: str) -> dict:
    with open(file_path, "r") as file:
        payload = json.load(file)

    dart_history = payload["dart_history"]

    for hit in dart_history:
        hit.setdefault("timestamp", None)
        if "offboard" not in hit or "bounce_out" not in hit:
            miss_zone = classify_miss_zone(hit.get("x", -1), hit.get("y", -1)) if hit.get("number") == 0 else {"offboard": False, "bounce_out": False}
            hit.setdefault("offboard", miss_zone["offboard"] or (hit.get("number") == 0 and not miss_zone["bounce_out"]))
            hit.setdefault("bounce_out", miss_zone["bounce_out"])

    payload["dart_history"] = dart_history
    payload.setdefault("metadata", {})
    return payload


def load_dart_history(file_path: str) -> list[dict]:
    return load_saved_game(file_path)["dart_history"]


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


def show_winner_animation(root: tk.Misc, winner_name: str, accent_color: str = "#f08a2b") -> bool:
    dialog = tk.Toplevel(root)
    dialog.title("Game Over")
    dialog.transient(root)
    dialog.grab_set()
    dialog.configure(bg="#171310")
    dialog.resizable(False, False)

    dialog_width = 520
    dialog_height = 380
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_w = root.winfo_width() or root.winfo_screenwidth()
    root_h = root.winfo_height() or root.winfo_screenheight()
    dialog.geometry(
        f"{dialog_width}x{dialog_height}+{root_x + (root_w - dialog_width) // 2}+{root_y + (root_h - dialog_height) // 2}"
    )

    canvas = tk.Canvas(dialog, width=dialog_width, height=240, bg="#171310", highlightthickness=0)
    canvas.pack()
    canvas.create_oval(-120, -80, 180, 170, fill="#221b17", outline="")
    canvas.create_oval(340, -50, 610, 200, fill="#201814", outline="")
    canvas.create_text(
        dialog_width / 2,
        58,
        text="Victory",
        fill="#f7efe2",
        font=("Avenir Next", 34, "bold"),
    )
    canvas.create_text(
        dialog_width / 2,
        108,
        text=f"{winner_name} wins",
        fill=accent_color,
        font=("Avenir Next", 28, "bold"),
    )
    canvas.create_text(
        dialog_width / 2,
        145,
        text="A clean finish deserves a little noise.",
        fill="#c6b5a3",
        font=("Avenir Next", 16),
    )

    particles = []
    palette = [accent_color, "#f5efe6", "#6f8dff", "#f39b44"]
    for _ in range(80):
        x = random.randint(20, dialog_width - 20)
        y = random.randint(-220, 20)
        size = random.randint(4, 10)
        velocity = random.uniform(2.0, 5.4)
        drift = random.uniform(-1.4, 1.4)
        particle_id = canvas.create_oval(x, y, x + size, y + size, fill=random.choice(palette), outline="")
        particles.append({"id": particle_id, "x": x, "y": y, "size": size, "vy": velocity, "vx": drift})

    burst = canvas.create_oval(
        dialog_width / 2 - 10,
        103,
        dialog_width / 2 + 10,
        123,
        outline=accent_color,
        width=3,
    )

    animation_state = {"frame": 0}

    def animate():
        animation_state["frame"] += 1
        frame = animation_state["frame"]
        radius = min(90, 10 + frame * 2.8)
        alpha_width = max(1, 4 - frame // 12)
        canvas.coords(
            burst,
            dialog_width / 2 - radius,
            113 - radius,
            dialog_width / 2 + radius,
            113 + radius,
        )
        canvas.itemconfig(burst, width=alpha_width)

        for particle in particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            if particle["y"] > 240:
                particle["x"] = random.randint(20, dialog_width - 20)
                particle["y"] = random.randint(-120, -10)
            canvas.coords(
                particle["id"],
                particle["x"],
                particle["y"],
                particle["x"] + particle["size"],
                particle["y"] + particle["size"],
            )

        if frame < 75:
            dialog.after(24, animate)

    animate()

    footer = tk.Frame(dialog, bg="#171310", padx=22, pady=18)
    footer.pack(fill=tk.BOTH, expand=True)
    tk.Label(
        footer,
        text="Do you want to save this game?",
        font=("Avenir Next", 16),
        fg="#f7efe2",
        bg="#171310",
    ).pack(pady=(8, 16))

    result = {"save": False}

    button_row = tk.Frame(footer, bg="#171310")
    button_row.pack()

    def close(save_result: bool):
        result["save"] = save_result
        dialog.destroy()

    tk.Button(
        button_row,
        text="Save Game",
        font=("Avenir Next", 16, "bold"),
        bg=accent_color,
        fg="#171310",
        activebackground="#f7efe2",
        activeforeground="#171310",
        bd=0,
        highlightthickness=0,
        padx=20,
        pady=10,
        cursor="hand2",
        command=lambda: close(True),
    ).pack(side=tk.LEFT, padx=8)
    tk.Button(
        button_row,
        text="Close",
        font=("Avenir Next", 16, "bold"),
        bg="#352b25",
        fg="#171310",
        activebackground="#4a3d34",
        activeforeground="#171310",
        bd=0,
        highlightthickness=0,
        padx=20,
        pady=10,
        cursor="hand2",
        command=lambda: close(False),
    ).pack(side=tk.LEFT, padx=8)

    dialog.protocol("WM_DELETE_WINDOW", lambda: close(False))
    dialog.wait_window()
    return result["save"]


def show_save_confirmation(root: tk.Misc, file_path: str) -> None:
    dialog = tk.Toplevel(root)
    dialog.title("Saved")
    dialog.transient(root)
    dialog.grab_set()
    dialog.configure(bg="#171310")
    dialog.resizable(False, False)

    dialog_width = 430
    dialog_height = 220
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_w = root.winfo_width() or root.winfo_screenwidth()
    root_h = root.winfo_height() or root.winfo_screenheight()
    dialog.geometry(
        f"{dialog_width}x{dialog_height}+{root_x + (root_w - dialog_width) // 2}+{root_y + (root_h - dialog_height) // 2}"
    )

    body = tk.Frame(dialog, bg="#171310", padx=28, pady=24)
    body.pack(fill=tk.BOTH, expand=True)
    tk.Label(
        body,
        text="Game Saved",
        font=("Avenir Next", 28, "bold"),
        fg="#f7efe2",
        bg="#171310",
    ).pack()
    tk.Label(
        body,
        text=os.path.basename(file_path),
        font=("Avenir Next", 15, "bold"),
        fg="#f08a2b",
        bg="#171310",
        wraplength=360,
        justify=tk.CENTER,
    ).pack(pady=(12, 6))
    tk.Label(
        body,
        text="Your current game history was written successfully.",
        font=("Avenir Next", 14),
        fg="#c6b5a3",
        bg="#171310",
        wraplength=340,
        justify=tk.CENTER,
    ).pack()
    tk.Button(
        body,
        text="Close",
        font=("Avenir Next", 15, "bold"),
        bg="#f08a2b",
        fg="#171310",
        activebackground="#f7efe2",
        activeforeground="#171310",
        bd=0,
        highlightthickness=0,
        padx=22,
        pady=10,
        cursor="hand2",
        command=dialog.destroy,
    ).pack(pady=(18, 0))

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.wait_window()
