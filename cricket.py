import os
import tkinter as tk
from datetime import datetime
from tkinter import simpledialog, ttk

from PIL import Image, ImageTk

from dart_engine.helpers_cricket import cricket_marks
from dart_engine.cricket_stats import build_all_cricket_marks_by_turn
from dart_engine.helpers_general import (
    get_screen_size_tkinter,
    interpret_click,
    swap_players_history,
    swap_teams_history,
)
from dart_engine.params_cricket import CricketGame as TeamCricketGame
from dart_engine.params_cricket import Hit as TeamHit
from dart_engine.params_cricket_1x1 import CricketGame as SoloCricketGame
from dart_engine.params_cricket_1x1 import Hit as SoloHit
from dart_engine.player_ui import build_player_turn_summary, format_hit_label, get_profile_pic_path
from dart_engine.ui_common import (
    add_player_option,
    ask_history_load_path,
    ask_history_save_path,
    choose_save_directory,
    infer_player_turn_order,
    load_app_config,
    load_dart_history,
    replay_dart_history,
    save_dart_history,
    update_app_config,
)

CRICKET_NUMBERS = [20, 19, 18, 17, 16, 15, 25]
CONFIG_FILE = "dart_engine/config.json"
T1_COLOR = "#6a83ff"
T2_COLOR = "#ec6d00"
SCOREBOARD_BG = "darkolivegreen"
INFOBOARD_BG = "white"
SCOREBOARD_HIGHLIGHT = "olivedrab"


class DartsApp:
    def __init__(self, root):
        self.root = root
        root.title("Cricket Darts")
        root.attributes("-fullscreen", True)
        x = root.winfo_width()
        y = root.winfo_height()

        self.folder_path, self.player_options = load_app_config(CONFIG_FILE)
        self.mode_var = tk.StringVar(value="teams")
        self.game = None

        self.folder_path_var = tk.StringVar(
            value=self.folder_path if self.folder_path is not None else "Save directory not set"
        )

        img = Image.open("dartboard_images/dartboard_accurate.png")
        self.size = 600
        img = img.resize((self.size, self.size))
        self.board_img = ImageTk.PhotoImage(img)

        self.canvas = tk.Canvas(root, width=self.size, height=self.size)
        self.canvas.pack()

        self.canvas_zoom = tk.Canvas(
            root,
            width=x / 2 - self.size / 2 - 2,
            height=x / 2 - self.size / 2 - 2,
            bg="white",
        )
        self.canvas_zoom.place(x=x / 2 + self.size / 2 - 3, y=0)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.board_img)

        self.cursor_label = tk.Label(root, text="x: 0  y: 0", font=("Arial", 10))
        self.cursor_label.pack(anchor="w")

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)

        self.score_canvas = tk.Canvas(
            root,
            width=x / 2 - self.size / 2 - 2,
            height=600 - 2,
            bg=SCOREBOARD_BG,
        )
        self.score_canvas.place(x=0, y=0)

        self.info_canvas = tk.Canvas(root, width=self.size - 7, height=y - 600 - 4, bg=INFOBOARD_BG)
        self.info_canvas.place(x=x / 2 - self.size / 2 + 1, y=600)

        btn_frame1 = tk.Frame(root)
        btn_frame1.place(x=5, y=630)
        tk.Button(btn_frame1, text="Undo", font=("Arial", 30), command=self.undo).pack(side=tk.LEFT)
        tk.Button(btn_frame1, text="Save", font=("Arial", 30), command=self.save).pack(side=tk.LEFT)
        tk.Button(btn_frame1, text="Load", font=("Arial", 30), command=self.load).pack(side=tk.LEFT)
        tk.Button(btn_frame1, text="Reset", font=("Arial", 30), command=self.reset).pack(side=tk.LEFT)

        btn_frame2 = tk.Frame(root)
        btn_frame2.place(x=5, y=680)
        tk.Button(btn_frame2, text="Save Setup...", font=("Arial", 30), command=self.save_setup).pack(side=tk.LEFT)
        tk.Button(btn_frame2, text="Save As...", font=("Arial", 30), command=self.save_as).pack(side=tk.RIGHT)

        btn_frame3 = tk.Frame(root)
        btn_frame3.place(x=10, y=730)
        tk.Entry(btn_frame3, textvariable=self.folder_path_var, font=("Arial", 16), width=40).pack(
            side=tk.TOP, pady=10
        )

        mode_frame = tk.Frame(root)
        mode_frame.place(x=10, y=770)
        tk.Label(mode_frame, text="Format:", font=("Arial", 20)).pack(side=tk.LEFT, padx=5)
        ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["teams", "solo"],
            font=("Arial", 18),
            state="readonly",
            width=8,
        ).pack(side=tk.LEFT)
        self.mode_var.trace_add("write", self.handle_mode_change)

        self.team1a_player_var = tk.StringVar(value=self.player_options[0])
        self.team1b_player_var = tk.StringVar(value=self.player_options[1])
        self.team2a_player_var = tk.StringVar(value=self.player_options[2])
        self.team2b_player_var = tk.StringVar(value=self.player_options[3])

        self.team1_frame = tk.Frame(root)
        self.team1_frame.place(x=0, y=810)
        tk.Label(self.team1_frame, text="Team 1: ", font=("Arial", 20)).pack(side=tk.LEFT, padx=5)
        self.dropdown_1a = ttk.Combobox(
            self.team1_frame,
            textvariable=self.team1a_player_var,
            values=self.player_options,
            font=("Arial", 20),
            state="readonly",
            width=6,
        )
        self.dropdown_1b = ttk.Combobox(
            self.team1_frame,
            textvariable=self.team1b_player_var,
            values=self.player_options,
            font=("Arial", 20),
            state="readonly",
            width=6,
        )
        self.dropdown_1a.pack(side=tk.LEFT)
        self.dropdown_1b.pack(side=tk.LEFT)
        self.dropdown_1a.bind("<<ComboboxSelected>>", self.update_players)
        self.dropdown_1b.bind("<<ComboboxSelected>>", self.update_players)
        self.swap_team_1_button = tk.Button(
            self.team1_frame, text="swap", font=("Arial", 20), command=lambda: self.swap_team_players(0)
        )
        self.swap_team_1_button.pack(side=tk.LEFT)

        self.team2_frame = tk.Frame(root)
        self.team2_frame.place(x=0, y=850)
        tk.Label(self.team2_frame, text="Team 2: ", font=("Arial", 20)).pack(side=tk.LEFT, padx=5)
        self.dropdown_2a = ttk.Combobox(
            self.team2_frame,
            textvariable=self.team2a_player_var,
            values=self.player_options,
            font=("Arial", 20),
            state="readonly",
            width=6,
        )
        self.dropdown_2b = ttk.Combobox(
            self.team2_frame,
            textvariable=self.team2b_player_var,
            values=self.player_options,
            font=("Arial", 20),
            state="readonly",
            width=6,
        )
        self.dropdown_2a.pack(side=tk.LEFT)
        self.dropdown_2b.pack(side=tk.LEFT)
        self.dropdown_2a.bind("<<ComboboxSelected>>", self.update_players)
        self.dropdown_2b.bind("<<ComboboxSelected>>", self.update_players)
        self.swap_team_2_button = tk.Button(
            self.team2_frame, text="swap", font=("Arial", 20), command=lambda: self.swap_team_players(1)
        )
        self.swap_team_2_button.pack(side=tk.LEFT)

        btn_frame6 = tk.Frame(root)
        btn_frame6.place(x=0, y=890)
        self.swap_teams_button = tk.Button(btn_frame6, text="Swap teams", font=("Arial", 20), command=self.swap_teams)
        self.swap_teams_button.pack(side=tk.LEFT)
        tk.Button(btn_frame6, text="Add Player", font=("Arial", 20), command=self.add_player).pack(side=tk.LEFT)

        self.dart_markers_0 = []
        self.dart_markers_1 = []
        self.dart_history = []
        self.mark_history_cache = {}

        self.set_game_mode("teams", preserve_names=False)

    def is_solo_mode(self):
        return self.mode_var.get() == "solo"

    def current_hit_class(self):
        return SoloHit if self.is_solo_mode() else TeamHit

    def active_side(self):
        return self.game.team_index_for_player(self.game.active_player())

    def current_order_size(self):
        return 2 if self.is_solo_mode() else 4

    def team_names_from_vars(self):
        if self.is_solo_mode():
            return [[self.team1a_player_var.get()], [self.team2a_player_var.get()]]
        return [
            [self.team1a_player_var.get(), self.team1b_player_var.get()],
            [self.team2a_player_var.get(), self.team2b_player_var.get()],
        ]

    def apply_player_vars_to_game(self):
        team_names = self.team_names_from_vars()
        if self.is_solo_mode():
            self.game.set_player_names([team_names[0][0], team_names[1][0]])
        else:
            self.game.set_team_player_names(0, team_names[0])
            self.game.set_team_player_names(1, team_names[1])

    def sync_player_vars_from_game(self):
        if self.is_solo_mode():
            self.team1a_player_var.set(self.game.players[0].name)
            self.team2a_player_var.set(self.game.players[1].name)
        else:
            self.team1a_player_var.set(self.game.teams[0].players[0].name)
            self.team1b_player_var.set(self.game.teams[0].players[1].name)
            self.team2a_player_var.set(self.game.teams[1].players[0].name)
            self.team2b_player_var.set(self.game.teams[1].players[1].name)

    def update_mode_controls(self):
        if self.is_solo_mode():
            self.dropdown_1b.pack_forget()
            self.dropdown_2b.pack_forget()
            self.swap_team_1_button.pack_forget()
            self.swap_team_2_button.pack_forget()
        else:
            if not self.dropdown_1b.winfo_manager():
                self.dropdown_1b.pack(side=tk.LEFT)
            if not self.dropdown_2b.winfo_manager():
                self.dropdown_2b.pack(side=tk.LEFT)
            if not self.swap_team_1_button.winfo_manager():
                self.swap_team_1_button.pack(side=tk.LEFT)
            if not self.swap_team_2_button.winfo_manager():
                self.swap_team_2_button.pack(side=tk.LEFT)

    def set_game_mode(self, mode, preserve_names=True):
        existing_names = self.team_names_from_vars() if preserve_names else None
        self.mode_var.set(mode)
        self.game = SoloCricketGame() if mode == "solo" else TeamCricketGame()

        if preserve_names and existing_names:
            if mode == "solo":
                solo_names = [existing_names[0][0], existing_names[1][0]]
                self.team1a_player_var.set(solo_names[0])
                self.team2a_player_var.set(solo_names[1])
            self.apply_player_vars_to_game()

        self.sync_player_vars_from_game()
        self.update_mode_controls()
        self.clear_all_darts()
        self.update_mark_history_cache()
        self.update_label()

    def handle_mode_change(self, *_):
        if self.game is None:
            return
        new_mode = self.mode_var.get()
        expected_mode = "solo" if self.is_solo_mode() else "teams"
        if new_mode != expected_mode:
            return
        self.set_game_mode(new_mode)

    def update_cursor(self, event):
        self.cursor_label.config(text=f"x: {event.x}   y: {event.y}")
        self.draw_zoomboard(event.x, event.y)

    def click(self, event):
        number, mult = interpret_click(event.x, event.y)
        if number is None:
            return

        marker_list = self.dart_markers_0 if self.active_side() == 0 else self.dart_markers_1
        marker_list.append(
            self.canvas.create_oval(
                event.x - 5,
                event.y - 5,
                event.x + 5,
                event.y + 5,
                fill=self.player_color(self.game.active_player()),
                outline="",
            )
        )

        player = self.game.active_player()
        self.dart_history.append(
            {
                "player": player.name,
                "team": self.active_side(),
                "x": event.x,
                "y": event.y,
                "number": number,
                "multiplier": mult,
            }
        )

        self.game.register_hit(self.current_hit_class()(number, mult, (event.x, event.y)))
        if self.game.darts_in_turn == 0:
            self.clear_team_darts()

        self.update_mark_history_cache()
        self.update_label()
        self.draw_zoomboard(event.x, event.y)

    def update_label(self):
        self.draw_infoboard()
        self.draw_scoreboard()

    def draw_current_dart_marker(self, x, y):
        marker_list = self.dart_markers_0 if self.active_side() == 0 else self.dart_markers_1
        marker_list.append(
            self.canvas.create_oval(
                x - 5,
                y - 5,
                x + 5,
                y + 5,
                fill=self.player_color(self.game.active_player()),
                outline="",
            )
        )

    def register_history_hit(self, hit):
        self.game.register_hit(self.current_hit_class()(hit["number"], hit["multiplier"], (hit["x"], hit["y"])))

    def replay_history(self):
        replay_dart_history(
            self.dart_history,
            reset_game=self.game.reset,
            clear_all_markers=self.clear_all_darts,
            draw_marker=lambda hit: self.draw_current_dart_marker(hit["x"], hit["y"]),
            register_hit=self.register_history_hit,
            clear_turn_markers=self.clear_team_darts,
            is_turn_complete=lambda: self.game.darts_in_turn == 0,
        )
        self.update_mark_history_cache()
        self.update_label()

    def player_color(self, player):
        return T1_COLOR if self.game.team_index_for_player(player) == 0 else T2_COLOR

    def team_name_for_player(self, player):
        if self.is_solo_mode():
            return ""
        return self.game.team_for_player(player).name

    def get_player_mark_history(self, player):
        player_name = player.name if hasattr(player, "name") else player
        return self.mark_history_cache.get(player_name, [0])

    def update_mark_history_cache(self):
        if self.is_solo_mode():
            side_lookup = {player.name: index for index, player in enumerate(self.game.players)}
        else:
            side_lookup = {
                player.name: side
                for side, team in enumerate(self.game.teams)
                for player in team.players
            }

        self.mark_history_cache = build_all_cricket_marks_by_turn(
            self.dart_history,
            side_lookup,
            complete_turns_only=True,
        )

    def previous_turn_mark_sum(self, player, end_of_turn):
        mark_history = self.get_player_mark_history(player)
        if end_of_turn:
            return mark_history[-2] if len(mark_history) > 1 else 0
        return mark_history[-1]

    def panel_turn_hits(self, player, turn_summary):
        player_name = player.name if hasattr(player, "name") else player
        player_summary = turn_summary["players"][player_name]
        if turn_summary["next_player_flag"] and player_name == turn_summary["focus_player"]:
            return player_summary["current_hits"]
        return player_summary["previous_hits"]

    def panel_mark_sum(self, player, turn_summary):
        player_name = player.name if hasattr(player, "name") else player
        mark_history = self.get_player_mark_history(player)
        if turn_summary["next_player_flag"] and player_name == turn_summary["focus_player"]:
            return mark_history[-1]
        if player_name == turn_summary["focus_player"]:
            return mark_history[-2] if len(mark_history) > 1 else 0
        return mark_history[-1]

    def load_player_image(self, player, size):
        image = Image.open(get_profile_pic_path(player.name))
        return ImageTk.PhotoImage(image.resize((size, size)))

    def clear_team_darts(self):
        if self.active_side() == 0:
            for marker in self.dart_markers_0:
                self.canvas.delete(marker)
            self.dart_markers_0 = []
        else:
            for marker in self.dart_markers_1:
                self.canvas.delete(marker)
            self.dart_markers_1 = []

    def clear_all_darts(self):
        for marker in self.dart_markers_0:
            self.canvas.delete(marker)
        for marker in self.dart_markers_1:
            self.canvas.delete(marker)
        self.dart_markers_0 = []
        self.dart_markers_1 = []

    def save_setup(self):
        folder_path = choose_save_directory(self.folder_path)
        if not folder_path:
            return
        self.folder_path = folder_path
        self.folder_path_var.set(self.folder_path)
        update_app_config(CONFIG_FILE, last_folder=self.folder_path)

    def save(self):
        if self.is_solo_mode():
            filename = f"cricket_{self.game.players[0].name}_vs_{self.game.players[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        else:
            filename = f"cricket_{self.game.teams[0].name}_vs_{self.game.teams[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

        if self.folder_path is None:
            self.save_as()
            return
        save_dart_history(os.path.join(self.folder_path, filename), self.dart_history)

    def save_as(self):
        file_path = ask_history_save_path()
        if file_path:
            save_dart_history(file_path, self.dart_history)

    def load(self):
        file_path = ask_history_load_path(self.folder_path)
        if not file_path:
            return

        self.dart_history = load_dart_history(file_path)
        turn_order = infer_player_turn_order(self.dart_history, 4)
        mode = "solo" if len(turn_order) <= 2 else "teams"
        self.set_game_mode(mode, preserve_names=False)

        for player in turn_order:
            if player not in self.player_options:
                self.add_player(dialog_popup=False, name=player)

        if self.is_solo_mode():
            if turn_order:
                self.team1a_player_var.set(turn_order[0])
            if len(turn_order) > 1:
                self.team2a_player_var.set(turn_order[1])
        else:
            team_order = [turn_order[index] for index in (0, 2, 1, 3) if index < len(turn_order)]
            vars_in_order = [
                self.team1a_player_var,
                self.team1b_player_var,
                self.team2a_player_var,
                self.team2b_player_var,
            ]
            for var, player in zip(vars_in_order, team_order):
                var.set(player)

        self.apply_player_vars_to_game()
        self.replay_history()

    def undo(self):
        self.dart_history = self.dart_history[:-1]
        self.replay_history()

    def reset(self):
        self.save_as()
        self.dart_history = []
        self.game.reset()
        self.clear_all_darts()
        self.update_mark_history_cache()
        self.update_label()

    def swap_teams(self):
        if self.is_solo_mode():
            self.game.swap_players()
        else:
            self.game.swap_teams()
            self.dart_history = swap_teams_history(self.dart_history)
        self.sync_player_vars_from_game()
        self.update_mark_history_cache()
        self.update_label()

    def swap_team_players(self, team_index):
        if self.is_solo_mode():
            return
        self.game.swap_team_players(team_index)
        self.dart_history = swap_players_history(self.dart_history, team_index)
        self.sync_player_vars_from_game()
        self.update_mark_history_cache()
        self.update_label()

    def update_players(self, _event):
        self.apply_player_vars_to_game()
        self.update_mark_history_cache()
        self.update_label()

    def add_player(self, dialog_popup=True, name=None):
        if dialog_popup:
            name = simpledialog.askstring("Add Player", "Enter player name:")
        if not add_player_option(self.player_options, name):
            return

        for dropdown in [self.dropdown_1a, self.dropdown_1b, self.dropdown_2a, self.dropdown_2b]:
            dropdown["values"] = self.player_options
        update_app_config(CONFIG_FILE, player_options=self.player_options)

    def draw_scoreboard(self):
        if self.is_solo_mode():
            self.draw_scoreboard_solo()
        else:
            self.draw_scoreboard_teams()

    def draw_scoreboard_teams(self):
        c = self.score_canvas
        c.delete("all")

        size_x = 454
        mid_width = 80
        row_height = 68
        start_y = 90
        highlight_width = 140
        current_team_idx = self.game.current_team
        teams = self.game.teams

        c.create_rectangle(
            size_x * (1 + 2 * current_team_idx) / 4 - highlight_width / 2 - mid_width / 4 + mid_width * current_team_idx / 2,
            0,
            size_x * (1 + 2 * current_team_idx) / 4 + highlight_width / 2 - mid_width / 4 + mid_width * current_team_idx / 2,
            600,
            fill=SCOREBOARD_HIGHLIGHT,
            outline=SCOREBOARD_HIGHLIGHT,
        )

        c.create_text(size_x * 1 / 4 - mid_width / 4, 30, text=teams[0].name, font=("Arial", 40, "bold"))
        c.create_text(size_x * 3 / 4 + mid_width / 4, 30, text=teams[1].name, font=("Arial", 40, "bold"))
        c.create_line(0, 60, size_x, 60, fill="white", width=2)
        c.create_line(size_x / 2 - mid_width / 2, 0, size_x / 2 - mid_width / 2, 600, fill="white", width=2)
        c.create_line(size_x / 2 + mid_width / 2, 0, size_x / 2 + mid_width / 2, 600, fill="white", width=2)

        for i, num in enumerate(CRICKET_NUMBERS):
            y = start_y + i * row_height
            c.create_line(0, y + row_height / 2, size_x, y + row_height / 2, fill="white", width=2, dash=(4, 4))
            c.create_text(size_x / 2, y, text="Bull" if num == 25 else str(num), font=("Arial", 30, "bold"))

            left_hits = teams[0].cricket_display[num] + teams[0].cricket_tallies[num]
            right_hits = teams[1].cricket_display[num] + teams[1].cricket_tallies[num]
            shared_closed = teams[0].cricket_closed[num] and teams[1].cricket_closed[num]
            c.create_text(
                size_x * 1 / 4 - mid_width / 4,
                y,
                text=cricket_marks(left_hits),
                font=("Arial", 30),
                fill="darkgray" if shared_closed else "white",
            )
            c.create_text(
                size_x * 3 / 4 + mid_width / 4,
                y,
                text=cricket_marks(right_hits),
                font=("Arial", 30),
                fill="darkgray" if shared_closed else "white",
            )

        y = start_y + len(CRICKET_NUMBERS) * row_height
        c.create_line(0, y - row_height / 2, size_x, y - row_height / 2, fill="white", width=2)
        c.create_text(size_x / 2, y, text="Pts", font=("Arial", 30, "bold"))
        c.create_text(size_x * 1 / 4 - mid_width / 4, y, text=str(teams[0].score), font=("Arial", 30, "bold"))
        c.create_text(size_x * 3 / 4 + mid_width / 4, y, text=str(teams[1].score), font=("Arial", 30, "bold"))

    def draw_scoreboard_solo(self):
        c = self.score_canvas
        c.delete("all")

        size_x = 454
        mid_width = 80
        row_height = 68
        start_y = 90
        highlight_width = 140
        players = self.game.players
        current_player_idx = self.game.current_player

        c.create_rectangle(
            size_x * (1 + 2 * current_player_idx) / 4 - highlight_width / 2 - mid_width / 4 + mid_width * current_player_idx / 2,
            0,
            size_x * (1 + 2 * current_player_idx) / 4 + highlight_width / 2 - mid_width / 4 + mid_width * current_player_idx / 2,
            600,
            fill=SCOREBOARD_HIGHLIGHT,
            outline=SCOREBOARD_HIGHLIGHT,
        )

        c.create_text(size_x * 1 / 4 - mid_width / 4, 30, text=players[0].name, font=("Arial", 40, "bold"))
        c.create_text(size_x * 3 / 4 + mid_width / 4, 30, text=players[1].name, font=("Arial", 40, "bold"))
        c.create_line(0, 60, size_x, 60, fill="white", width=2)
        c.create_line(size_x / 2 - mid_width / 2, 0, size_x / 2 - mid_width / 2, 600, fill="white", width=2)
        c.create_line(size_x / 2 + mid_width / 2, 0, size_x / 2 + mid_width / 2, 600, fill="white", width=2)

        for i, num in enumerate(CRICKET_NUMBERS):
            y = start_y + i * row_height
            c.create_line(0, y + row_height / 2, size_x, y + row_height / 2, fill="white", width=2, dash=(4, 4))
            c.create_text(size_x / 2, y, text="Bull" if num == 25 else str(num), font=("Arial", 30, "bold"))
            left_hits = players[0].cricket_display[num] + players[0].cricket_tallies[num]
            right_hits = players[1].cricket_display[num] + players[1].cricket_tallies[num]
            shared_closed = players[0].cricket_closed[num] and players[1].cricket_closed[num]
            c.create_text(
                size_x * 1 / 4 - mid_width / 4,
                y,
                text=cricket_marks(left_hits),
                font=("Arial", 30),
                fill="darkgray" if shared_closed else "white",
            )
            c.create_text(
                size_x * 3 / 4 + mid_width / 4,
                y,
                text=cricket_marks(right_hits),
                font=("Arial", 30),
                fill="darkgray" if shared_closed else "white",
            )

        y = start_y + len(CRICKET_NUMBERS) * row_height
        c.create_line(0, y - row_height / 2, size_x, y - row_height / 2, fill="white", width=2)
        c.create_text(size_x / 2, y, text="Pts", font=("Arial", 30, "bold"))
        c.create_text(size_x * 1 / 4 - mid_width / 4, y, text=str(players[0].score), font=("Arial", 30, "bold"))
        c.create_text(size_x * 3 / 4 + mid_width / 4, y, text=str(players[1].score), font=("Arial", 30, "bold"))

    def draw_infoboard(self):
        if self.is_solo_mode():
            self.draw_infoboard_solo()
        else:
            self.draw_infoboard_teams()

    def infoboard_layout(self):
        width = 600
        panel_width = int(width / 3)
        screen_width, _ = get_screen_size_tkinter()
        panel_height = 162 if screen_width == 1470 else 174
        pfp_size = 98 if screen_width == 1470 else 100
        return width, panel_width, panel_height, pfp_size, 40

    def draw_infoboard_teams(self):
        c = self.info_canvas
        c.delete("all")
        width, panel_width, panel_height, pfp_size, box_height = self.infoboard_layout()

        c.create_line(int(width / 2 - panel_width / 2), panel_height, int(width / 2 - panel_width / 2), panel_height * 2, fill="black", width=3)
        c.create_line(int(width / 2 + panel_width / 2), 0, int(width / 2 + panel_width / 2), panel_height * 2, fill="black", width=3)
        c.create_line(0, panel_height, width, panel_height, fill="black", width=3)

        y_pos = panel_height * 2 - box_height
        x_pos = width / 2 - panel_width * 3 / 2
        for _ in range(3):
            c.create_line(x_pos, y_pos, x_pos + panel_width, y_pos, fill="black", width=2)
            x_shift = panel_width / 4
            for _ in range(3):
                c.create_line(x_pos + x_shift, y_pos + box_height, x_pos + x_shift, y_pos, fill="black", width=2)
                x_shift += panel_width / 4
            x_pos += panel_width

        y_pos = panel_height - box_height
        x_pos = width / 2 + panel_width / 2
        c.create_line(x_pos, y_pos, x_pos + panel_width, y_pos, fill="black", width=2)
        x_shift = panel_width / 4
        for _ in range(3):
            c.create_line(x_pos + x_shift, y_pos + box_height, x_pos + x_shift, y_pos, fill="black", width=2)
            x_shift += panel_width / 4

        panel_player_list = self.game.rotated_turn_order()
        turn_summary = build_player_turn_summary(self.dart_history, panel_player_list, self.game.active_player().name)
        current_name = turn_summary["focus_player"]
        current_team = self.team_name_for_player(current_name)
        p0_current_hits = turn_summary["players"][current_name]["current_hits"]
        p0_hits = self.panel_turn_hits(panel_player_list[0], turn_summary)
        p1_hits = self.panel_turn_hits(panel_player_list[1], turn_summary)
        p2_hits = self.panel_turn_hits(panel_player_list[2], turn_summary)
        p3_hits = self.panel_turn_hits(panel_player_list[3], turn_summary)
        mark_sums = [
            self.panel_mark_sum(panel_player_list[0], turn_summary),
            self.panel_mark_sum(panel_player_list[1], turn_summary),
            self.panel_mark_sum(panel_player_list[2], turn_summary),
            self.panel_mark_sum(panel_player_list[3], turn_summary),
        ]

        c.create_text(10, 20, anchor="w", text=current_name, font=("Arial", 30, "bold"), fill=self.player_color(current_name))
        c.create_text(panel_width * 2 - 10, 20, anchor="e", text=current_team, font=("Arial", 30, "bold"), fill=self.player_color(current_name))

        for x1, x2 in [(panel_width * 1 / 4, panel_width * 7 / 4)]:
            c.create_line(x1, 40, x2, 40, fill="black", width=2)
            c.create_line(x1, 120, x2, 120, fill="black", width=2)
        for x in [panel_width * 1 / 4, panel_width * 3 / 4, panel_width * 5 / 4, panel_width * 7 / 4]:
            c.create_line(x, 40, x, 120, fill="black", width=2)

        for ii, label in enumerate(["1", "2", "3"]):
            c.create_text(panel_width * (1 + ii) / 2, 60, text=label, font=("Arial", 20, "underline", "bold"), fill="black")
            c.create_text(
                panel_width / 2 + ii * panel_width / 2,
                100,
                text=p0_current_hits[ii] if ii < len(p0_current_hits) else "-",
                font=("Arial", 30, "bold") if ii == len(p0_current_hits) - 1 else ("Arial", 30),
                fill="black",
            )

        if turn_summary["next_player_flag"]:
            next_player = self.game.active_player()
            c.create_text(10, 140, anchor="w", text="Next player:", font=("Arial", 30, "bold"), fill="black")
            c.create_text(10, 140, anchor="w", text=f"Next player: {next_player.name}", font=("Arial", 30, "bold"), fill=self.player_color(next_player))
            c.create_text(panel_width * 2 - 10, 140, anchor="e", text=self.team_name_for_player(next_player), font=("Arial", 30, "bold"), fill=self.player_color(next_player))

        image_positions = [
            (width / 2 + panel_width, 12, 72),
            (width / 2 - panel_width, 12 + panel_height, 72 + panel_height),
            (width / 2, 12 + panel_height, 72 + panel_height),
            (width / 2 + panel_width, 12 + panel_height, 72 + panel_height),
        ]
        for index, player in enumerate(panel_player_list):
            x_text, y_text, y_img = image_positions[index]
            c.create_text(x_text, y_text, text=player.name, font=("Arial", 20, "bold"), fill=self.player_color(player))
            image = self.load_player_image(player, pfp_size)
            setattr(self.root, f"image{index}", image)
            c.create_image(x_text, y_img, image=image)

        c.create_text(width / 2 + panel_width * 5 / 8 + 3 * panel_width / 4, panel_height - box_height / 2, text=f"{mark_sums[0]}M", font=("Arial", 20), fill="black")
        x_shift = panel_width / 4
        for idx, hit in enumerate(p0_hits[:3]):
            c.create_text(width / 2 + 3 * panel_width / 8 + x_shift * (idx + 1), panel_height - box_height / 2, text=hit, font=("Arial", 20), fill="black")

        bottom_rows = [p1_hits, p2_hits, p3_hits]
        x_pos = width / 2 - panel_width * 3 / 2 - panel_width / 8
        for row_index, hits in enumerate(bottom_rows):
            x_shift = panel_width / 4
            for idx, hit in enumerate(hits[:3]):
                c.create_text(x_pos + x_shift * (idx + 1), panel_height * 2 - box_height / 2, text=hit, font=("Arial", 20), fill="black")
            c.create_text(x_pos + x_shift * 4, panel_height * 2 - box_height / 2, text=f"{mark_sums[row_index + 1]}M", font=("Arial", 20), fill="black")
            x_pos += panel_width

    def draw_infoboard_solo(self):
        c = self.info_canvas
        c.delete("all")
        width, panel_width, panel_height, pfp_size, box_height = self.infoboard_layout()

        c.create_line(int(width / 2 - panel_width / 2), panel_height, int(width / 2 - panel_width / 2), panel_height * 2, fill="black", width=3)
        c.create_line(int(width / 2 + panel_width / 2), 0, int(width / 2 + panel_width / 2), panel_height * 2, fill="black", width=3)
        c.create_line(0, panel_height, width, panel_height, fill="black", width=3)

        y_pos = panel_height * 2 - box_height
        x_pos = width / 2 + panel_width / 2
        c.create_line(x_pos, panel_height - box_height, x_pos + panel_width, panel_height - box_height, fill="black", width=2)
        c.create_line(x_pos, y_pos, x_pos + panel_width, y_pos, fill="black", width=2)
        x_shift = panel_width / 4
        for _ in range(3):
            c.create_line(x_pos + x_shift, panel_height, x_pos + x_shift, panel_height - box_height, fill="black", width=2)
            c.create_line(x_pos + x_shift, y_pos + box_height, x_pos + x_shift, y_pos, fill="black", width=2)
            x_shift += panel_width / 4

        panel_player_list = self.game.rotated_turn_order()
        turn_summary = build_player_turn_summary(self.dart_history, panel_player_list, self.game.active_player().name)
        current_name = turn_summary["focus_player"]
        p0_current_hits = turn_summary["players"][current_name]["current_hits"]
        p0_hits = self.panel_turn_hits(panel_player_list[0], turn_summary)
        p1_hits = self.panel_turn_hits(panel_player_list[1], turn_summary)
        mark_sums = [
            self.panel_mark_sum(panel_player_list[0], turn_summary),
            self.panel_mark_sum(panel_player_list[1], turn_summary),
        ]

        c.create_text(10, 20, anchor="w", text=current_name, font=("Arial", 30, "bold"), fill=self.player_color(current_name))
        c.create_line(panel_width * 1 / 4, 40, panel_width * 7 / 4, 40, fill="black", width=2)
        c.create_line(panel_width * 1 / 4, 120, panel_width * 7 / 4, 120, fill="black", width=2)
        for x in [panel_width * 1 / 4, panel_width * 3 / 4, panel_width * 5 / 4, panel_width * 7 / 4]:
            c.create_line(x, 40, x, 120, fill="black", width=2)

        for ii, label in enumerate(["1", "2", "3"]):
            c.create_text(panel_width * (1 + ii) / 2, 60, text=label, font=("Arial", 20, "underline", "bold"), fill="black")
            c.create_text(
                panel_width / 2 + ii * panel_width / 2,
                100,
                text=p0_current_hits[ii] if ii < len(p0_current_hits) else "-",
                font=("Arial", 30, "bold") if ii == len(p0_current_hits) - 1 else ("Arial", 30),
                fill="black",
            )

        if turn_summary["next_player_flag"]:
            next_player = self.game.active_player()
            c.create_text(10, 140, anchor="w", text="Next player:", font=("Arial", 30, "bold"), fill="black")
            c.create_text(10, 140, anchor="w", text=f"Next player: {next_player.name}", font=("Arial", 30, "bold"), fill=self.player_color(next_player))

        positions = [
            (width / 2 + panel_width, 12, 72),
            (width / 2 + panel_width, 12 + panel_height, 72 + panel_height),
        ]
        for index, player in enumerate(panel_player_list):
            x_text, y_text, y_img = positions[index]
            c.create_text(x_text, y_text, text=player.name, font=("Arial", 20, "bold"), fill=self.player_color(player))
            image = self.load_player_image(player, pfp_size)
            setattr(self.root, f"image{index}", image)
            c.create_image(x_text, y_img, image=image)

        x_start = width / 2 + panel_width / 2 - panel_width / 8
        for idx, hit in enumerate(p0_hits[:3]):
            c.create_text(x_start + panel_width / 4 * (idx + 1), panel_height - box_height / 2, text=hit, font=("Arial", 20), fill="black")
        c.create_text(x_start + panel_width, panel_height - box_height / 2, text=f"{mark_sums[0]}M", font=("Arial", 20), fill="black")

        for idx, hit in enumerate(p1_hits[:3]):
            c.create_text(x_start + panel_width / 4 * (idx + 1), panel_height * 2 - box_height / 2, text=hit, font=("Arial", 20), fill="black")
        c.create_text(x_start + panel_width, panel_height * 2 - box_height / 2, text=f"{mark_sums[1]}M", font=("Arial", 20), fill="black")

    def draw_zoomboard(self, x, y):
        c = self.canvas_zoom
        c.delete("all")

        zoom_factor = 3
        line_size = 50
        canvas_size = 460
        img = Image.open("dartboard_images/dartboard_accurate.png")
        img = img.resize((600, 600))
        img = img.crop((int(x - 300 / zoom_factor), int(y - 300 / zoom_factor), int(x + 300 / zoom_factor), int(y + 300 / zoom_factor)))
        img = img.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)
        self.zoom_img = ImageTk.PhotoImage(img)
        c.create_image(0, 0, anchor=tk.NW, image=self.zoom_img)

        hist = self.dart_history[::-1]
        recent_hist = hist[:6]
        if hist:
            current_player = hist[0]["player"]
            x0, y0, x1, y1 = [], [], [], []
            n_players = 0
            for hh, hit in enumerate(recent_hist):
                if hit["player"] != current_player:
                    n_players += 1
                    current_player = hit["player"]
                if n_players > 1:
                    continue
                if hit["team"] == 0:
                    x0.append(hit["x"])
                    y0.append(hit["y"])
                    if hh == 5:
                        x0, y0 = [], []
                else:
                    x1.append(hit["x"])
                    y1.append(hit["y"])
                    if hh == 5:
                        x1, y1 = [], []

            for x_vals, y_vals, color in [(x0, y0, T1_COLOR), (x1, y1, T2_COLOR)]:
                for nn in range(len(x_vals)):
                    x_dot = (x_vals[nn] - x) / 600 * canvas_size * zoom_factor + canvas_size / 2
                    y_dot = (y_vals[nn] - y) / 600 * canvas_size * zoom_factor + canvas_size / 2
                    c.create_oval(x_dot - 5, y_dot - 5, x_dot + 5, y_dot + 5, fill=color, outline="")

        active_color = self.player_color(self.game.active_player())
        c.create_line(canvas_size / 2 - line_size / 2, canvas_size / 2, canvas_size / 2 + line_size / 2, canvas_size / 2, width=4, fill=active_color)
        c.create_line(canvas_size / 2, canvas_size / 2 - line_size / 2, canvas_size / 2, canvas_size / 2 + line_size / 2, width=4, fill=active_color)
        number, mult = interpret_click(x, y)
        c.create_text(canvas_size / 2 + 75, canvas_size / 2, text=format_hit_label(number, mult), fill=active_color, font=("Arial", 40, "bold"))


root = tk.Tk()
app = DartsApp(root)
root.mainloop()
