import os
import tkinter as tk
from dart_engine.params_501 import Hit, Game501
from datetime import datetime
from math import hypot
from tkinter import messagebox, simpledialog, ttk

from PIL import Image, ImageTk
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-codex")
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, LinearLocator

from dart_engine.helpers_501 import get_recommended_hits
from dart_engine.helpers_general import classify_miss_zone, interpret_click, swap_players_history, swap_teams_history
from dart_engine.player_ui import build_recent_player_turn_summary, format_hit_label, get_profile_pic_path
from dart_engine.ui_common import (
    add_player_option,
    ask_history_load_path,
    ask_history_save_path,
    choose_save_directory,
    infer_player_turn_order,
    load_app_config,
    load_dart_history,
    load_saved_game,
    save_dart_history,
    update_app_config,
)

# -------------------------
# Constants
# -------------------------

# order clockwise starting from top
BOARD_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
               3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
CRICKET_NUMBERS = [20,19,18,17,16,15,25]
CONFIG_FILE = "dart_engine/config.json"
T1_COLOR = "#6a83ff"
T2_COLOR = "#ec6d00"
SCOREBOARD_BG = "saddlebrown"
SCOREBOARD_HIGHLIGHT = "chocolate"
INFOBOARD_BG = "white"
RECBOARD_BG = "#323232"
REC_FILL = "dimgray"
REC_FILL_RED = "dimgray" # "maroon"
STATS_BG = "#f3efe7"
STATS_PANEL = "#e5ddd0"
STATS_PANEL_ALT = "#ddd3c3"
TEXT_DARK = "#2f2419"
TEXT_LIGHT = "#f5f1ea"

# -------------------------
# GUI
# -------------------------

class DartsApp:

    def __init__(self, root, on_back=None, initial_mode="2v2"):

        self.root = root
        self.on_back = on_back
        root.title("501 Darts")
        root.attributes('-fullscreen', True)
        x = root.winfo_width()
        y = root.winfo_height()

        self.game = Game501()

        self.folder_path, self.player_options = load_app_config(CONFIG_FILE)
            
        # Set the StringVar so Entry shows it
        self.folder_path_var = tk.StringVar(value=self.folder_path if self.folder_path is not None else "Save directory not set")

        img = Image.open("dartboard_images/dartboard_accurate.png")
        self.size = 600
        img = img.resize((self.size, self.size))

        self.board_img = ImageTk.PhotoImage(img)
        self.zoom_source_img = img
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        self.profile_image_cache = {}
        self.infoboard_turn_summary = None
        self.score_history_cache = {}
        self.stats_cache = {}
        self.stats_board_photos = {}
        self.stats_view_var = tk.StringVar(value="Shot Map")
        self.winner_dialog_shown = False

        self.canvas = tk.Canvas(root, width=self.size, height=self.size)
        self.canvas.pack()

        right_column_width = self.screen_width / 2 - self.size / 2 - 2
        right_column_x = self.screen_width / 2 + self.size / 2 - 3
        zoom_height = right_column_width

        self.canvas_zoom = tk.Canvas(root, width=right_column_width, height=zoom_height, bg="white")
        self.canvas_zoom.place(x=right_column_x, y=0)

        self.canvas.create_image(0,0,anchor=tk.NW,image=self.board_img)

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)
        
        self.score_canvas = tk.Canvas(root, width=x/2-self.size/2-2, height=600-2, bg=SCOREBOARD_BG)
        self.score_canvas.place(x=0, y=0)

        self.rec_canvas = tk.Canvas(root, width=x/2-self.size/2-2, height=100-2, bg=RECBOARD_BG)
        self.rec_canvas.place(x=0, y=600)

        self.info_canvas = tk.Canvas(root, width=self.size-7, height=y-600-4, bg=INFOBOARD_BG)
        self.info_canvas.place(x=x/2-self.size/2+1, y=600)

        stats_y = int(zoom_height) + 2
        stats_control_height = 36
        stats_height = self.screen_height - stats_y - stats_control_height - 8
        self.stats_canvas = tk.Canvas(
            root,
            width=right_column_width,
            height=stats_height,
            # bg=INFOBOARD_BG,
            highlightthickness=0,
        )
        self.stats_canvas.place(x=right_column_x, y=stats_y)
        self.stats_view_menu = ttk.Combobox(
            root,
            textvariable=self.stats_view_var,
            values=["Shot Map", "Score Plot", "Grouping Plot"],
            font=("Arial", 14),
            state="readonly",
            width=11,
        )
        self.stats_view_menu.place(x=right_column_x + 160, y=stats_y+450)
        self.stats_view_var.trace_add("write", self.handle_stats_view_change)

        btn_frame1 = tk.Frame(root)
        btn_frame1.place(x=5, y=700)

        if self.on_back:
            tk.Button(btn_frame1,text="Menu",font=("Arial",24),command=self.on_back, padx=0).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Undo",font=("Arial",24),command=self.undo, padx=0).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Load",font=("Arial",24),command=self.load, padx=0).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="New Game",font=("Arial",24),command=self.reset, padx=0).pack(side=tk.LEFT)

        btn_frame2 = tk.Frame(root)
        btn_frame2.place(x=5, y=740)
        tk.Button(btn_frame2,text="Save",font=("Arial",24),command=self.save).pack(side=tk.LEFT)
        tk.Button(btn_frame2,text="Save Setup...",font=("Arial",24),command=self.save_setup).pack(side=tk.LEFT)
        tk.Button(btn_frame2,text="Save As...",font=("Arial",24),command=self.save_as).pack(side=tk.RIGHT)

        btn_frame3 = tk.Frame(root)
        btn_frame3.place(x=50, y=785)
        tk.Entry(
            btn_frame3,
            textvariable=self.folder_path_var,
            font=("Arial",16),
            width=40,
        ).pack(side=tk.TOP, pady=0)

        self.team1a_player_var = tk.StringVar(value=self.player_options[0])
        self.team1b_player_var = tk.StringVar(value=self.player_options[1])
        self.team2a_player_var = tk.StringVar(value=self.player_options[2])
        self.team2b_player_var = tk.StringVar(value=self.player_options[3])
        self.team1_name_var = tk.StringVar(value=self.game.teams[0].name)
        self.team2_name_var = tk.StringVar(value=self.game.teams[1].name)

        btn_frame4 = tk.Frame(root)
        btn_frame4.place(x=0, y=815)

        self.team1_name_button = tk.Button(
            btn_frame4,
            textvariable=self.team1_name_var,
            font=("Arial",20),
            command=lambda: self.prompt_team_name_change(0),
            width=6,
        )
        self.team1_name_button.pack(side=tk.LEFT, padx=(5, 6))
        self.dropdown_1a = ttk.Combobox(
            btn_frame4,
            textvariable=self.team1a_player_var,
            values=self.player_options,
            font=("Arial",20),
            state="readonly",
            width = 6
        )
        self.dropdown_1b = ttk.Combobox(
            btn_frame4,
            textvariable=self.team1b_player_var,
            values=self.player_options,
            font=("Arial",20),
            state="readonly",
            width = 6
        )
        self.dropdown_1a.pack(side=tk.LEFT)
        self.dropdown_1b.pack(side=tk.LEFT)
        self.dropdown_1a.bind("<<ComboboxSelected>>", self.update_players)
        self.dropdown_1b.bind("<<ComboboxSelected>>", self.update_players)
        self.swap_team_1_button = tk.Button(btn_frame4,text="swap",font=("Arial",20),command=self.swap_players_team_1)
        self.swap_team_1_button.pack(side=tk.LEFT)

        btn_frame5 = tk.Frame(root)
        btn_frame5.place(x=0, y=850)
        self.team2_name_button = tk.Button(
            btn_frame5,
            textvariable=self.team2_name_var,
            font=("Arial",20),
            command=lambda: self.prompt_team_name_change(1),
            width=6,
        )
        self.team2_name_button.pack(side=tk.LEFT, padx=(5, 6))
        self.dropdown_2a = ttk.Combobox(
            btn_frame5,
            textvariable=self.team2a_player_var,
            values=self.player_options,
            font=("Arial",20),
            state="readonly",
            width = 6
        )
        self.dropdown_2b = ttk.Combobox(
            btn_frame5,
            textvariable=self.team2b_player_var,
            values=self.player_options,
            font=("Arial",20),
            state="readonly",
            width = 6
        )
        self.dropdown_2a.pack(side=tk.LEFT)
        self.dropdown_2b.pack(side=tk.LEFT)
        self.dropdown_2a.bind("<<ComboboxSelected>>", self.update_players)
        self.dropdown_2b.bind("<<ComboboxSelected>>", self.update_players)
        self.swap_team_2_button = tk.Button(btn_frame5,text="swap",font=("Arial",20),command=self.swap_players_team_2)
        self.swap_team_2_button.pack(side=tk.LEFT)

        btn_frame6 = tk.Frame(root)
        btn_frame6.place(x=0, y=890)
        tk.Button(btn_frame6,text="Swap teams",font=("Arial",20),command=self.swap_teams).pack(side=tk.LEFT)
        tk.Button(btn_frame6,text="Add Player",font=("Arial",20),command=self.add_player).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="2v2")
        ttk.Combobox(
            btn_frame6,
            textvariable=self.mode_var,
            values=["2v2", "2p", "3p", "4p"],
            font=("Arial",18),
            state="readonly",
            width=8,
        ).pack(side=tk.LEFT)
        self.mode_var.trace_add("write", self.handle_mode_change)

        self.dart_markers = {}

        # store dart history for dataset
        self.dart_history = []

        self.set_game_mode(initial_mode, preserve_names=False)

    def update_cursor(self, event):
        self.draw_zoomboard(event.x, event.y)

    def click(self,event):
        if self.game.winner:
            return

        number, mult = interpret_click(event.x,event.y)

        if number is None:
            return

        # Keep the completed 3-dart turn visible until the next dart starts.
        if self.game.darts_in_turn == 0 and self.dart_markers:
            self.clear_all_darts()

        throwing_team = self.game.current_team
        dot = self.canvas.create_oval(
            event.x - 5,
            event.y - 5,
            event.x + 5,
            event.y + 5,
            fill=self.player_color(self.game.active_player()),
            outline="",
        )
        self.dart_markers.setdefault(throwing_team, []).append(dot)

        # save dart data
        player = self.game.active_player()
        miss_zone = classify_miss_zone(event.x, event.y) if number == 0 else {"offboard": False, "bounce_out": False}

        self.dart_history.append({
            "player": player.name,
            "team": self.game.current_team,
            "x": event.x,
            "y": event.y,
            "number": number,
            "multiplier": mult,
            "offboard": miss_zone["offboard"] or (number == 0 and not miss_zone["bounce_out"]),
            "bounce_out": miss_zone["bounce_out"],
        })

        self.game.register_hit(Hit(number,mult, (event.x, event.y)),self.dart_history)

        self.refresh_caches()
        self.update_label()
        self.prompt_save_on_winner()

        self.draw_zoomboard(event.x,event.y)

    def update_label(self):
        self.update_infoboard_turn_summary()
        self.draw_infoboard()
        self.draw_scoreboard()
        self.draw_recboard()
        self.draw_statsboard()

    def draw_current_dart_marker(self, x, y):
        marker_list = self.dart_markers.setdefault(self.game.current_team, [])
        color = self.player_color(self.game.active_player())
        dot = self.canvas.create_oval(
            x - 5,
            y - 5,
            x + 5,
            y + 5,
            fill=color,
            outline="",
        )
        marker_list.append(dot)

    def register_history_hit(self, hit):
        self.game.register_hit(Hit(hit["number"], hit["multiplier"], (hit["x"], hit["y"])))

    def replay_history(self):
        self.game.reset()
        self.clear_all_darts()

        for hit in self.dart_history:
            if self.game.darts_in_turn == 0 and self.dart_markers:
                self.clear_all_darts()
            self.draw_current_dart_marker(hit["x"], hit["y"])
            self.register_history_hit(hit)

        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def player_color(self, player):
        side = self.game.team_index_for_player(player)
        if self.is_team_mode():
            return T1_COLOR if side == 0 else T2_COLOR
        palette = ["#0b5cff", "#d94801", "#148a2a", "#7a3db8"]
        return palette[side % len(palette)]

    def team_name_for_player(self, player):
        return self.game.team_for_player(player).name

    def stats_players_in_display_order(self):
        return [player for team in self.game.teams for player in team.players]

    def is_team_mode(self):
        return self.mode_var.get() == "2v2"

    def is_solo_mode(self):
        return self.mode_var.get() == "2p"

    def is_individual_mode(self):
        return not self.is_team_mode()

    def individual_mode_player_count(self):
        return {"2p": 2, "3p": 3, "4p": 4}.get(self.mode_var.get(), 2)

    def player_slot_vars(self):
        return [
            self.team1a_player_var,
            self.team1b_player_var,
            self.team2a_player_var,
            self.team2b_player_var,
        ]

    def visible_player_slot_indices(self, mode=None):
        mode = self.mode_var.get() if mode is None else mode
        if mode == "2p":
            return [0, 1]
        if mode == "3p":
            return [0, 1, 2]
        return [0, 1, 2, 3]

    def visible_player_names(self, mode=None):
        slot_vars = self.player_slot_vars()
        return [slot_vars[index].get() for index in self.visible_player_slot_indices(mode)]

    def apply_visible_names_to_mode(self, mode, names):
        if mode == "2p":
            if names:
                self.team1a_player_var.set(names[0])
            if len(names) > 1:
                self.team1b_player_var.set(names[1])
            return
        if mode == "3p":
            targets = [self.team1a_player_var, self.team1b_player_var, self.team2a_player_var]
            for var, name in zip(targets, names):
                var.set(name)
            return
        if mode == "4p":
            for var, name in zip(self.player_slot_vars(), names):
                var.set(name)
            return
        for var, name in zip(self.player_slot_vars(), names):
            var.set(name)

    def individual_player_names_from_vars(self):
        names = [
            self.team1a_player_var.get(),
            self.team1b_player_var.get(),
            self.team2a_player_var.get(),
            self.team2b_player_var.get(),
        ]
        return names[: self.individual_mode_player_count()]

    def team_names_from_vars(self):
        if self.is_individual_mode():
            return [[name] for name in self.individual_player_names_from_vars()]
        return [
            [self.team1a_player_var.get(), self.team1b_player_var.get()],
            [self.team2a_player_var.get(), self.team2b_player_var.get()],
        ]

    def apply_player_vars_to_game(self):
        team_names = self.team_names_from_vars()
        for team_index, names in enumerate(team_names):
            self.game.set_team_player_names(team_index, names)
        if self.is_team_mode():
            self.game.set_team_name(0, self.team1_name_var.get().strip() or "Team 1")
            self.game.set_team_name(1, self.team2_name_var.get().strip() or "Team 2")
        else:
            for team_index, names in enumerate(team_names):
                if names:
                    self.game.set_team_name(team_index, names[0])

    def team_player_colors(self, side, count):
        if self.is_individual_mode():
            return [self.player_color(self.game.teams[side].players[0]) for _ in range(max(1, count))]
        palettes = {
            0: ["#0b5cff", "#00a6fb", "#123b8f", "#58c4ff"],
            1: ["#d94801", "#ff8c00", "#8c2f00", "#ffb454"],
        }
        palette = palettes[side]
        return [palette[index % len(palette)] for index in range(max(1, count))]

    def sync_player_vars_from_game(self):
        if self.is_individual_mode():
            for var, name in zip(self.player_slot_vars(), [player.name for player in self.game.players_by_turn_order()]):
                var.set(name)
        else:
            self.team1a_player_var.set(self.game.teams[0].players[0].name)
            self.team1b_player_var.set(self.game.teams[0].players[1].name)
            self.team2a_player_var.set(self.game.teams[1].players[0].name)
            self.team2b_player_var.set(self.game.teams[1].players[1].name)
        self.sync_team_name_vars_from_game()

    def sync_team_name_vars_from_game(self):
        self.team1_name_var.set(self.game.teams[0].name)
        self.team2_name_var.set(self.game.teams[1].name)

    def update_mode_controls(self):
        for widget in (
            self.team1_name_button,
            self.dropdown_1a,
            self.dropdown_1b,
            self.swap_team_1_button,
            self.team2_name_button,
            self.dropdown_2a,
            self.dropdown_2b,
            self.swap_team_2_button,
        ):
            widget.pack_forget()

        if self.is_team_mode():
            self.team1_name_button.pack(side=tk.LEFT, padx=(5, 6))
            self.dropdown_1a.pack(side=tk.LEFT)
            self.dropdown_1b.pack(side=tk.LEFT)
            self.swap_team_1_button.pack(side=tk.LEFT)

            self.team2_name_button.pack(side=tk.LEFT, padx=(5, 6))
            self.dropdown_2a.pack(side=tk.LEFT)
            self.dropdown_2b.pack(side=tk.LEFT)
            self.swap_team_2_button.pack(side=tk.LEFT)
        elif self.mode_var.get() == "2p":
            self.dropdown_1a.pack(side=tk.LEFT)
            self.dropdown_1b.pack(side=tk.LEFT)
        elif self.mode_var.get() == "3p":
            self.dropdown_1a.pack(side=tk.LEFT)
            self.dropdown_1b.pack(side=tk.LEFT)
            self.dropdown_2a.pack(side=tk.LEFT)
        else:
            self.dropdown_1a.pack(side=tk.LEFT)
            self.dropdown_1b.pack(side=tk.LEFT)
            self.dropdown_2a.pack(side=tk.LEFT)
            self.dropdown_2b.pack(side=tk.LEFT)

    def set_game_mode(self, mode, preserve_names=True):
        existing_names = self.team_names_from_vars() if preserve_names else None
        existing_visible_names = self.visible_player_names() if preserve_names else None
        existing_team_names = [self.team1_name_var.get(), self.team2_name_var.get()] if preserve_names else None
        self._setting_mode = True
        self.mode_var.set(mode)
        self._setting_mode = False
        self.game = Game501(mode)
        self.mode = 4 if self.is_team_mode() else self.individual_mode_player_count()

        if preserve_names and existing_names:
            if mode in {"2p", "3p", "4p"}:
                self.apply_visible_names_to_mode(mode, existing_visible_names or [])
            else:
                self.apply_visible_names_to_mode(mode, existing_visible_names or [])
                if existing_team_names:
                    self.team1_name_var.set(existing_team_names[0])
                    self.team2_name_var.set(existing_team_names[1])
            self.apply_player_vars_to_game()

        self.sync_player_vars_from_game()
        self.update_mode_controls()
        self.clear_all_darts()
        self.refresh_caches()
        self.update_label()

    def handle_mode_change(self, *_):
        if self.game is None or getattr(self, "_setting_mode", False):
            return
        self.set_game_mode(self.mode_var.get())

    def get_player_score_history(self, player):
        player_name = player.name if hasattr(player, "name") else player
        return self.score_history_cache.get(player_name, [0])

    def load_player_image(self, player, size):
        cache_key = (player.name, size)
        if cache_key not in self.profile_image_cache:
            original_image = Image.open(get_profile_pic_path(player.name))
            resized_image = original_image.resize((size, size))
            self.profile_image_cache[cache_key] = ImageTk.PhotoImage(resized_image)
        return self.profile_image_cache[cache_key]

    def update_score_history_cache(self):
        players = self.stats_players_in_display_order()
        score_history = {player.name: [] for player in players}
        current_turn_scores = {player.name: 0 for player in players}
        team_score = {side: 501 for side in range(len(self.game.teams))}
        team_turn_start = {side: 501 for side in range(len(self.game.teams))}
        last_player = None

        for hit in self.dart_history:
            player_name = hit["player"]
            side = self.game.team_index_for_player(player_name) if player_name in score_history else hit.get("team", 0)

            if player_name != last_player:
                team_turn_start[side] = team_score[side]
                current_turn_scores[player_name] = 0
                if player_name in score_history:
                    score_history[player_name].append(0)

            points = hit["multiplier"] * hit["number"]
            team_score[side] -= points

            if player_name in score_history and score_history[player_name]:
                current_turn_scores[player_name] += points
                score_history[player_name][-1] = current_turn_scores[player_name]

            if team_score[side] <= 1:
                team_score[side] = team_turn_start[side]
                if player_name in score_history and score_history[player_name]:
                    current_turn_scores[player_name] = 0
                    score_history[player_name][-1] = 0

            last_player = player_name

        self.score_history_cache = {
            player_name: history or [0]
            for player_name, history in score_history.items()
        }

    def draw_inline_stats(self, canvas, x, y, stats, label_font, value_font, color=TEXT_DARK, gap=10):
        cursor_x = x
        for label, value in stats:
            label_id = canvas.create_text(cursor_x, y, anchor="nw", text=label, font=label_font, fill=color)
            bbox = canvas.bbox(label_id)
            cursor_x = (bbox[2] if bbox else cursor_x) + 3
            value_id = canvas.create_text(cursor_x, y, anchor="nw", text=str(value), font=value_font, fill=color)
            bbox = canvas.bbox(value_id)
            cursor_x = (bbox[2] if bbox else cursor_x) + gap

    def previous_turn_grouping(self, turn_hits):
        if len(turn_hits) < 2:
            return 100.0

        max_spread = 0.0
        for idx, hit_a in enumerate(turn_hits):
            for hit_b in turn_hits[idx + 1:]:
                spread = hypot(hit_a["x"] - hit_b["x"], hit_a["y"] - hit_b["y"])
                if spread > max_spread:
                    max_spread = spread

        # Calibrate against the scoring area rather than the full image bounds so
        # wide misses trend much closer to 0 AGI.
        max_effective_spread = self.size * 0.6
        if max_effective_spread == 0:
            return 100.0

        agi = 100.0 * (1.0 - max_spread / max_effective_spread)
        return max(0.0, min(100.0, agi))

    def turn_bull_accuracy(self, turn_hits):
        if not turn_hits:
            return 0.0
        bull_x = self.size / 2
        bull_y = self.size / 2
        return sum(hypot(hit["x"] - bull_x, hit["y"] - bull_y) for hit in turn_hits) / len(turn_hits)

    def contrast_text_color(self, background_color):
        r16, g16, b16 = self.root.winfo_rgb(background_color)
        r = r16 / 65535
        g = g16 / 65535
        b = b16 / 65535
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return TEXT_DARK if luminance > 0.55 else TEXT_LIGHT

    def tk_color_to_hex(self, color):
        r16, g16, b16 = self.root.winfo_rgb(color)
        return f"#{r16 // 256:02x}{g16 // 256:02x}{b16 // 256:02x}"

    def handle_stats_view_change(self, *_):
        self.draw_statsboard()

    def render_score_plot(self, size, player_names, progression, player_colors, text_color, bg_color, axis_limits):
        bg_color = "#ffffff"
        text_color = "#000000"
        fig = Figure(figsize=(size / 100, size / 100), dpi=100, facecolor=bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        legend_handles = []
        legend_labels = []
        for name in player_names:
            series = progression.get(name, [(0, 0)])
            color = player_colors.get(name, "#000000")
            x_vals = [point[0] for point in series]
            y_vals = [point[1] for point in series]
            handle = ax.plot(x_vals, y_vals, color=color, linewidth=2.5, marker="o", markersize=3)[0]
            legend_handles.append(handle)
            legend_labels.append(name)

        ax.legend(legend_handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False, fontsize=8, ncol=2)
        ax.set_xlabel("dt", color=text_color, fontsize=8)
        ax.xaxis.labelpad = 2
        ax.tick_params(axis="x", colors=text_color, labelsize=8)
        ax.tick_params(axis="y", colors=text_color, labelsize=8)
        ax.spines["bottom"].set_color(text_color)
        ax.spines["left"].set_color(text_color)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.set_ylabel("Pts", color=text_color, fontsize=8, fontweight="bold")
        ax.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.4, color=text_color)

        max_x = axis_limits["max_x"]
        min_y = axis_limits["min_y"]
        max_y = axis_limits["max_y"]
        if max_x <= 0:
            max_x = 1
        if max_y == min_y:
            max_y = min_y + 1
        ax.set_xlim(0, max_x)
        ax.set_ylim(min_y, max_y)

        fig.subplots_adjust(left=0.22, right=0.9, bottom=0.26, top=0.95)
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        rgba = canvas.buffer_rgba()
        image = Image.frombuffer("RGBA", canvas.get_width_height(), rgba, "raw", "RGBA", 0, 1)
        return ImageTk.PhotoImage(image)

    def render_grouping_plot(self, size, player_names, grouping_progression, bull_accuracy_progression, player_colors, text_color, bg_color):
        bg_color = "#ffffff"
        text_color = "#000000"
        fig = Figure(figsize=(size / 100, size / 100), dpi=100, facecolor=bg_color)
        ax_left = fig.add_subplot(111)
        ax_right = ax_left.twinx()
        ax_left.set_facecolor(bg_color)
        ax_right.set_facecolor("none")

        player_handles = []
        player_labels = []
        for name in player_names:
            grouping_series = grouping_progression.get(name, [])
            bull_series = bull_accuracy_progression.get(name, [])
            color = player_colors.get(name, "#000000")
            if grouping_series:
                x_vals = [point[0] for point in grouping_series]
                y_vals = [point[1] for point in grouping_series]
                handle = ax_left.plot(x_vals, y_vals, color=color, linewidth=2.5, marker="o", markersize=3)[0]
            else:
                handle = ax_left.plot([], [], color=color, linewidth=2.5)[0]
            if bull_series:
                bull_x = [point[0] for point in bull_series]
                bull_y = [point[1] for point in bull_series]
                ax_right.plot(bull_x, bull_y, color=color, linewidth=2.0, linestyle="--")
            player_handles.append(handle)
            player_labels.append(name)

        legend_handles = [
            ax_left.plot([], [], color="#000000", linewidth=2.5)[0],
            ax_left.plot([], [], color="#000000", linewidth=2.0, linestyle="--")[0],
            *player_handles,
        ]
        legend_labels = ["AGI", "Bull Dist", *player_labels]
        ax_left.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            frameon=False,
            fontsize=8,
            ncol=2,
        )

        max_turn = max(
            [point[0] for series in grouping_progression.values() for point in series]
            + [point[0] for series in bull_accuracy_progression.values() for point in series]
            + [1]
        )
        max_bull_distance = max(
            [point[1] for series in bull_accuracy_progression.values() for point in series]
            + [1.0]
        )

        ax_left.set_xlim(1, max_turn if max_turn > 1 else 2)
        ax_left.set_ylim(0, 100)
        ax_right.set_ylim(0, max_bull_distance * 1.05 if max_bull_distance > 0 else 1.0)
        ax_left.yaxis.set_major_locator(LinearLocator(6))
        ax_right.yaxis.set_major_locator(LinearLocator(6))
        ax_left.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax_right.yaxis.set_minor_locator(AutoMinorLocator(2))

        ax_left.grid(True, axis="y", which="major", linestyle="--", linewidth=0.6, alpha=0.4, color=text_color)
        ax_left.grid(True, axis="y", which="minor", linestyle=":", linewidth=0.45, alpha=0.2, color=text_color)
        ax_left.set_xlabel("Turn", color=text_color, fontsize=8)
        ax_left.set_ylabel("AGI", color=text_color, fontsize=8, fontweight="bold")
        ax_right.set_ylabel("Bull Dist", color=text_color, fontsize=8, fontweight="bold")
        ax_left.xaxis.labelpad = 2
        ax_left.yaxis.labelpad = 2
        ax_right.yaxis.labelpad = 2
        ax_left.tick_params(axis="x", colors=text_color, labelsize=8)
        ax_left.tick_params(axis="y", colors=text_color, labelsize=8)
        ax_right.tick_params(axis="y", colors=text_color, labelsize=8)
        ax_left.spines["bottom"].set_color(text_color)
        ax_left.spines["left"].set_color(text_color)
        ax_left.spines["top"].set_visible(False)
        ax_right.spines["top"].set_visible(False)
        ax_right.spines["left"].set_visible(False)
        ax_right.spines["right"].set_color(text_color)
        fig.subplots_adjust(left=0.24, right=0.78, bottom=0.3, top=0.95)

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        rgba = canvas.buffer_rgba()
        image = Image.frombuffer("RGBA", canvas.get_width_height(), rgba, "raw", "RGBA", 0, 1)
        return ImageTk.PhotoImage(image)

    def update_stats_cache(self):
        players = self.stats_players_in_display_order()
        player_stats = {
            player.name: {
                "name": player.name,
                "side": self.game.team_index_for_player(player),
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "offboard": 0,
                "doubles": 0,
                "triples": 0,
                "score_50_plus": 0,
                "score_75_plus": 0,
                "score_100_plus": 0,
                "previous_grouping": 0.0,
            }
            for player in players
        }
        sides = range(len(self.game.teams))
        team_stats = {
            side: {
                "label": self.game.teams[side].name,
                "score": self.game.teams[side].score,
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "offboard": 0,
                "doubles": 0,
                "triples": 0,
            }
            for side in sides
        }

        team_players = {side: [] for side in sides}
        for player in players:
            side = self.game.team_index_for_player(player)
            team_players[side].append(player.name)

        player_color_lookup = {}
        for side in sides:
            for name, color in zip(team_players[side], self.team_player_colors(side, len(team_players[side]))):
                player_color_lookup[name] = color

        distribution_points = {side: [] for side in sides}
        player_progression = {player.name: [(0, 0)] for player in players}
        grouping_progression = {player.name: [] for player in players}
        bull_accuracy_progression = {player.name: [] for player in players}
        player_darts_progress = {player.name: 0 for player in players}
        completed_turns = {player.name: [] for player in players}
        grouping_turn_index = {player.name: 0 for player in players}
        player_committed = {
            player.name: {
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "offboard": 0,
                "doubles": 0,
                "triples": 0,
            }
            for player in players
        }
        team_committed = {
            side: {
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "offboard": 0,
                "doubles": 0,
                "triples": 0,
            }
            for side in sides
        }
        player_pending = {
            player.name: {
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "offboard": 0,
                "doubles": 0,
                "triples": 0,
            }
            for player in players
        }
        team_pending = {
            side: {
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "offboard": 0,
                "doubles": 0,
                "triples": 0,
            }
            for side in sides
        }
        current_turn_player = None
        current_turn_side = None
        current_turn_hits = []
        team_score = {side: 501 for side in sides}
        team_turn_start = {side: 501 for side in sides}

        def reset_pending(player_name, side):
            for field in player_pending[player_name]:
                player_pending[player_name][field] = 0
            for field in team_pending[side]:
                team_pending[side][field] = 0

        def sync_display(player_name, side):
            for field in ("darts", "scored", "bulls", "offboard", "doubles", "triples"):
                player_stats[player_name][field] = player_committed[player_name][field] + player_pending[player_name][field]
                team_stats[side][field] = team_committed[side][field] + team_pending[side][field]

        def commit_turn(player_name, side):
            for field in ("darts", "scored", "bulls", "offboard", "doubles", "triples"):
                player_committed[player_name][field] += player_pending[player_name][field]
                team_committed[side][field] += team_pending[side][field]
            reset_pending(player_name, side)
            sync_display(player_name, side)

        for hit in self.dart_history:
            player_name = hit["player"]
            side = self.game.team_index_for_player(player_name) if player_name in player_stats else hit.get("team", 0)
            points = hit["multiplier"] * hit["number"]

            if player_name != current_turn_player:
                current_turn_player = player_name
                current_turn_side = side
                current_turn_hits = []
                team_turn_start[side] = team_score[side]
                reset_pending(player_name, side)
            current_turn_hits.append(hit)

            if player_name in player_stats:
                player_darts_progress[player_name] += 1
                player_pending[player_name]["darts"] += 1
                player_pending[player_name]["scored"] += points
                player_pending[player_name]["bulls"] += 1 if hit["number"] == 25 else 0
                player_pending[player_name]["offboard"] += 1 if hit["number"] == 0 else 0
                player_pending[player_name]["doubles"] += 1 if hit["multiplier"] == 2 else 0
                player_pending[player_name]["triples"] += 1 if hit["multiplier"] == 3 else 0
                team_pending[side]["darts"] += 1
                team_pending[side]["scored"] += points
                team_pending[side]["bulls"] += 1 if hit["number"] == 25 else 0
                team_pending[side]["offboard"] += 1 if hit["number"] == 0 else 0
                team_pending[side]["doubles"] += 1 if hit["multiplier"] == 2 else 0
                team_pending[side]["triples"] += 1 if hit["multiplier"] == 3 else 0
                sync_display(player_name, side)

            team_score[side] -= points
            winning_checkout = team_score[side] == 0 and hit["multiplier"] == 2
            bust = team_score[side] <= 1 and not winning_checkout

            if player_name in player_stats:
                progression_score = player_stats[player_name]["scored"]
                if bust:
                    progression_score = player_committed[player_name]["scored"]
                player_progression[player_name].append((player_darts_progress[player_name], progression_score))

            if bust:
                team_score[side] = team_turn_start[side]
                if player_name in player_stats:
                    for idx in range(1, len(current_turn_hits) + 1):
                        x_val = player_progression[player_name][-idx][0]
                        player_progression[player_name][-idx] = (x_val, player_committed[player_name]["scored"])
                    reset_pending(player_name, side)
                    sync_display(player_name, side)
                current_turn_player = None
                current_turn_side = None
                current_turn_hits = []
            else:
                if player_name in player_stats and (len(current_turn_hits) == 3 or winning_checkout):
                    commit_turn(player_name, side)
                    if len(current_turn_hits) == 3:
                        completed_turns[player_name].append(current_turn_hits.copy())
                        grouping_turn_index[player_name] += 1
                        grouping_progression[player_name].append(
                            (grouping_turn_index[player_name], self.previous_turn_grouping(current_turn_hits))
                        )
                        bull_accuracy_progression[player_name].append(
                            (grouping_turn_index[player_name], self.turn_bull_accuracy(current_turn_hits))
                        )
                    current_turn_player = None
                    current_turn_side = None
                    current_turn_hits = []

            distribution_points[side].append(
                {
                    "x": hit["x"],
                    "y": hit["y"],
                    "player": player_name,
                    "color": player_color_lookup.get(player_name, self.player_color(player_name)),
                }
            )

        for player_name, stats in player_stats.items():
            turns = self.score_history_cache.get(player_name, [0])
            stats["avg"] = (stats["scored"] * 3 / stats["darts"]) if stats["darts"] else 0.0
            stats["score_50_plus"] = sum(1 for score in turns if score >= 50)
            stats["score_75_plus"] = sum(1 for score in turns if score >= 75)
            stats["score_100_plus"] = sum(1 for score in turns if score >= 100)
            player_turns = completed_turns.get(player_name, [])
            stats["previous_grouping"] = self.previous_turn_grouping(player_turns[-1]) if player_turns else 0.0

        for side in sides:
            team_stats[side]["avg"] = (
                team_stats[side]["scored"] * 3 / team_stats[side]["darts"]
                if team_stats[side]["darts"]
                else 0.0
            )

        all_score_points = [point[1] for series in player_progression.values() for point in series]
        min_plot_y = min(all_score_points, default=0)
        max_plot_y = max(all_score_points, default=0)
        if min_plot_y == max_plot_y:
            max_plot_y = min_plot_y + 1
        y_margin = max(1, (max_plot_y - min_plot_y) * 0.08)
        plot_limits = {
            "max_x": max((point[0] for series in player_progression.values() for point in series), default=1),
            "min_y": max(0, min_plot_y - y_margin * 0.1),
            "max_y": max_plot_y + y_margin,
        }

        self.stats_cache = {
            "players": [player_stats[player.name] for player in players],
            "teams": [team_stats[side] for side in sides],
            "distribution": distribution_points,
            "player_progression": player_progression,
            "grouping_progression": grouping_progression,
            "bull_accuracy_progression": bull_accuracy_progression,
            "plot_limits": plot_limits,
            "team_players": team_players,
            "player_colors": player_color_lookup,
            "active_player": self.game.active_player().name,
        }

    def update_infoboard_turn_summary(self):
        self.infoboard_turn_summary = build_recent_player_turn_summary(
            self.dart_history,
            self.game.rotated_turn_order(),
            self.game.active_player().name,
        )

    def refresh_caches(self):
        self.update_score_history_cache()
        self.update_stats_cache()

    def panel_turn_hits(self, player, turn_summary):
        player_name = player.name if hasattr(player, "name") else player
        player_summary = turn_summary["players"][player_name]
        if turn_summary["next_player_flag"] and player_name == turn_summary["focus_player"]:
            return player_summary["current_hits"]
        return player_summary["previous_hits"]

    def panel_score_sum(self, player, turn_summary):
        player_name = player.name if hasattr(player, "name") else player
        score_history = self.get_player_score_history(player)
        if turn_summary["next_player_flag"] and player_name == turn_summary["focus_player"]:
            return score_history[-1]
        if player_name == turn_summary["focus_player"]:
            return score_history[-2] if len(score_history) > 1 else 0
        return score_history[-1]

    def clear_team_darts(self, team_index=None):
        team_index = self.game.current_team if team_index is None else team_index
        for marker in self.dart_markers.get(team_index, []):
            self.canvas.delete(marker)
        self.dart_markers.pop(team_index, None)

    def prompt_save_on_winner(self):
        if not self.game.winner or self.winner_dialog_shown:
            return
        self.winner_dialog_shown = True
        should_save = messagebox.askyesno("Game Over", f"{self.game.winner} wins!\n\nDo you want to save this game?")
        if should_save:
            self.save()


    def clear_all_darts(self):
        for marker_list in self.dart_markers.values():
            for marker in marker_list:
                self.canvas.delete(marker)
        self.dart_markers = {}

    def save_setup(self):
        folder_path = choose_save_directory(self.folder_path)
        if not folder_path:
            return

        self.folder_path = folder_path
        self.folder_path_var.set(self.folder_path)
        update_app_config(CONFIG_FILE, last_folder=self.folder_path)

    def save(self):
        if self.is_individual_mode():
            self.filename = f"501_{'_vs_'.join(player.name for player in self.game.players_by_turn_order())}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            metadata = {"game_mode": self.mode_var.get()}
        else:
            self.filename = f"501_{self.game.teams[0].name}_vs_{self.game.teams[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            metadata = {
                "game_mode": self.mode_var.get(),
                "team_names": [self.game.teams[0].name, self.game.teams[1].name],
            }

        if self.folder_path is None:
            self.save_as()
            return

        save_dart_history(
            os.path.join(self.folder_path, self.filename),
            self.dart_history,
            metadata=metadata,
        )

    def save_as(self):
        file_path = ask_history_save_path()
        if not file_path:
            return

        metadata = {"game_mode": self.mode_var.get()}
        if self.is_team_mode():
            metadata["team_names"] = [self.game.teams[0].name, self.game.teams[1].name]

        save_dart_history(
            file_path,
            self.dart_history,
            metadata=metadata,
        )

    def load(self):
        file_path = ask_history_load_path(self.folder_path)
        if not file_path:
            return

        saved_game = load_saved_game(file_path)
        self.dart_history = saved_game["dart_history"]
        metadata = saved_game.get("metadata", {})
        team_names = metadata.get("team_names", [])
        turn_order = infer_player_turn_order(self.dart_history, 4)
        unique_teams = sorted({hit.get("team", 0) for hit in self.dart_history})
        inferred_individual_mode = None
        if len(unique_teams) == len(turn_order):
            inferred_individual_mode = {2: "2p", 3: "3p", 4: "4p"}.get(len(unique_teams))
        mode = metadata.get("game_mode") or inferred_individual_mode or ("2p" if len(turn_order) <= 2 else "2v2")
        self.set_game_mode(mode, preserve_names=False)

        for player in turn_order:
            if player not in self.player_options:
                self.add_player(dialog_popup=False, name=player)

        if self.is_individual_mode():
            for player_var, player_name in zip(self.player_slot_vars(), turn_order):
                player_var.set(player_name)
        else:
            team_order = [turn_order[index] for index in (0, 2, 1, 3) if index < len(turn_order)]
            player_vars = [
                self.team1a_player_var,
                self.team1b_player_var,
                self.team2a_player_var,
                self.team2b_player_var,
            ]
            for player_var, player_name in zip(player_vars, team_order):
                player_var.set(player_name)
            if len(team_names) >= 2:
                self.team1_name_var.set(team_names[0])
                self.team2_name_var.set(team_names[1])

        self.apply_player_vars_to_game()
        self.replay_history()
        self.winner_dialog_shown = False

    def undo(self):
        self.dart_history = self.dart_history[:-1]
        self.replay_history()
        self.winner_dialog_shown = False

    def reset(self):
        self.save_as()
        self.dart_history = []
        self.game.reset()
        self.clear_all_darts()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def swap_teams(self):
        if not self.is_team_mode():
            return
        self.game.swap_teams()
        self.dart_history = swap_teams_history(self.dart_history)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def swap_players_team_1(self):
        if not self.is_team_mode():
            return
        self.game.swap_team_players(0)
        self.dart_history = swap_players_history(self.dart_history,0)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def swap_players_team_2(self):
        if not self.is_team_mode():
            return
        self.game.swap_team_players(1)
        self.dart_history = swap_players_history(self.dart_history,1)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def update_players(self, _event):
        self.apply_player_vars_to_game()
        self.update_team_names(refresh_ui=False)
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def update_team_names(self, event=None, refresh_ui=True):
        if not self.is_team_mode():
            return
        team1_name = self.team1_name_var.get().strip() or "Team 1"
        team2_name = self.team2_name_var.get().strip() or "Team 2"
        self.team1_name_var.set(team1_name)
        self.team2_name_var.set(team2_name)
        self.game.set_team_name(0, team1_name)
        self.game.set_team_name(1, team2_name)
        if refresh_ui:
            self.refresh_caches()
            self.update_label()
            self.winner_dialog_shown = False

    def prompt_team_name_change(self, team_index):
        current_name = self.team1_name_var.get() if team_index == 0 else self.team2_name_var.get()
        new_name = simpledialog.askstring("Team Name", "Enter team name (max 6 chars):", initialvalue=current_name)
        if new_name is None:
            return
        new_name = new_name.strip()[:6]
        if not new_name:
            new_name = f"Team {team_index + 1}"
        if team_index == 0:
            self.team1_name_var.set(new_name)
        else:
            self.team2_name_var.set(new_name)
        self.update_team_names()

    def add_player(self, dialog_popup=True, name=None):
        if dialog_popup:
            name = simpledialog.askstring("Add Player", "Enter player name:")

        if not add_player_option(self.player_options, name):
            return

        self.dropdown_1a['values'] = self.player_options
        self.dropdown_1b['values'] = self.player_options
        self.dropdown_2a['values'] = self.player_options
        self.dropdown_2b['values'] = self.player_options
        update_app_config(CONFIG_FILE, player_options=self.player_options)

    def draw_scoreboard(self):
        if self.is_team_mode():
            self.draw_scoreboard_teams()
        else:
            self.draw_scoreboard_individual()

    def draw_scoreboard_teams(self):
        c = self.score_canvas
        c.delete("all")

        size_x = 454
        size_y = 600
        row_height = 68
        start_y = 90
        highlight_width = 80
        y = start_y + 7 * row_height

        players = self.game.all_players()
        current_player_idx = next(
            index for index, player in enumerate(players) if player.name == self.game.active_player().name
        )

        c.create_rectangle(
            size_x * (1 + 2 * current_player_idx) / 8 - highlight_width / 2,
            60,
            size_x * (1 + 2 * current_player_idx) / 8 + highlight_width / 2,
            start_y + (13 / 2) * row_height,
            fill=SCOREBOARD_HIGHLIGHT,
            outline=SCOREBOARD_HIGHLIGHT,
        )

        c.create_text(size_x * 1 / 4, 30, text=self.game.teams[0].name, font=("Arial", 40, "bold"))
        c.create_text(size_x * 3 / 4, 30, text=self.game.teams[1].name, font=("Arial", 40, "bold"))

        player_x_positions = [size_x * 1 / 8, size_x * 3 / 8, size_x * 5 / 8, size_x * 7 / 8]
        for x_pos, player in zip(player_x_positions, players):
            c.create_text(x_pos, 75, text=player.name, font=("Arial", 20, "bold", "underline"))

        c.create_line(0, 60, size_x, 60, fill="white", width=2)
        c.create_line(size_x / 2, 0, size_x / 2, size_y, fill="white", width=3)
        c.create_line(size_x / 4, 60, size_x / 4, start_y + (13 / 2) * row_height, fill="white", width=2)
        c.create_line(size_x * 3 / 4, 60, size_x * 3 / 4, start_y + (13 / 2) * row_height, fill="white", width=2)

        for x_pos, player in zip(player_x_positions, players):
            for yy, player_score in enumerate(self.get_player_score_history(player)):
                if yy < 13:
                    c.create_text(x_pos, 75 + (yy + 1) * row_height / 2, text=str(player_score), font=("Arial", 20))

        c.create_line(0, y - row_height / 2, size_x, y - row_height / 2, fill="white", width=2)
        c.create_text(size_x * 1 / 4, y, text=str(self.game.teams[0].score), font=("Arial", 40, "bold"))
        c.create_text(size_x * 3 / 4, y, text=str(self.game.teams[1].score), font=("Arial", 40, "bold"))

    def draw_scoreboard_individual(self):
        c = self.score_canvas
        c.delete("all")

        size_x = 454
        size_y = 600
        row_height = 68
        start_y = 90
        y = start_y + 7 * row_height
        players = self.game.players_by_turn_order()
        slot_count = 4 if len(players) >= 3 else len(players)
        col_width = size_x / max(1, slot_count)
        highlight_width = max(70, col_width * 0.72)
        current_side = self.game.current_team

        c.create_rectangle(
            0,
            0,
            size_x,
            60,
            fill="white",
            outline="white",
        )

        c.create_rectangle(
            col_width * current_side + col_width / 2 - highlight_width / 2,
            60,
            col_width * current_side + col_width / 2 + highlight_width / 2,
            start_y + (13 / 2) * row_height,
            fill=SCOREBOARD_HIGHLIGHT,
            outline=SCOREBOARD_HIGHLIGHT,
        )

        c.create_line(0, 60, size_x, 60, fill="white", width=2)
        for index in range(1, slot_count):
            c.create_line(col_width * index, 0, col_width * index, size_y, fill="white", width=3 if len(players) == 2 else 2)

        player_x_positions = [col_width * index + col_width / 2 for index in range(len(players))]
        for x_pos, player in zip(player_x_positions, players):
            c.create_text(x_pos, 30, text=player.name, font=("Arial", 26 if len(players) > 2 else 40, "bold"), fill=self.player_color(player))
            for yy, player_score in enumerate(self.get_player_score_history(player)):
                if yy < 13:
                    c.create_text(x_pos, 75 + (yy + 1) * row_height / 2, text=str(player_score), font=("Arial", 20))

        c.create_line(0, y - row_height / 2, size_x, y - row_height / 2, fill="white", width=2)
        for x_pos, player in zip(player_x_positions, players):
            c.create_text(x_pos, y, text=str(self.game.score_for_player(player)), font=("Arial", 32 if len(players) > 2 else 40, "bold"))

    def draw_infoboard(self):
        if self.is_team_mode():
            self.draw_infoboard_teams()
        else:
            self.draw_infoboard_individual()

    def draw_turn_score_cells(self, canvas, left, top, width, box_height, hits, score_sum):
        canvas.create_line(left, top, left + width, top, fill="black", width=2)
        step = width / 4
        for split_index in range(1, 4):
            split_x = left + step * split_index
            canvas.create_line(split_x, top + box_height, split_x, top, fill="black", width=2)

        for idx, hit in enumerate(hits[:3]):
            canvas.create_text(left + step * (idx + 0.5), top + box_height / 2, text=hit, font=("Arial", 20), fill="black")
        canvas.create_text(left + step * 3.5, top + box_height / 2, text=f"{score_sum}", font=("Arial", 20, "bold"), fill="black")

    def draw_player_turn_card(self, canvas, player, image_center, label_y, image_y, pfp_size, cell_left, cell_top, cell_width, box_height, hits, score_sum, image_attr):
        canvas.create_text(image_center, label_y, text=player.name, font=("Arial", 20, "bold"), fill=self.player_color(player))
        image = self.load_player_image(player, pfp_size)
        setattr(self.root, image_attr, image)
        canvas.create_image(image_center, image_y, image=image)
        self.draw_turn_score_cells(canvas, cell_left, cell_top, cell_width, box_height, hits, score_sum)

    def individual_bottom_card_layouts(self, width, panel_width, panel_height):
        if self.mode == 2:
            return [(
                width / 2 + panel_width,
                12 + panel_height,
                72 + panel_height,
                width / 2 + panel_width / 2,
            )]
        if self.mode == 3:
            return [
                (width / 2, 12 + panel_height, 72 + panel_height, width / 2 - panel_width / 2),
                (width / 2 + panel_width, 12 + panel_height, 72 + panel_height, width / 2 + panel_width / 2),
            ]
        return [
            (width / 2 - panel_width, 12 + panel_height, 72 + panel_height, width / 2 - panel_width * 3 / 2),
            (width / 2, 12 + panel_height, 72 + panel_height, width / 2 - panel_width / 2),
            (width / 2 + panel_width, 12 + panel_height, 72 + panel_height, width / 2 + panel_width / 2),
        ]

    def infoboard_layout(self):
        width = 600
        panel_width = int(width / 3)
        if self.screen_width == 1470:
            panel_height = 162
            pfp_size = 98
        else:
            panel_height = 174
            pfp_size = 100
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

        turn_summary = self.infoboard_turn_summary
        current_name = turn_summary["focus_player"]
        current_team = self.team_name_for_player(current_name)
        player_list = self.game.rotated_turn_order()
        p0_current_hits = turn_summary["players"][current_name]["current_hits"]
        p0_hits = self.panel_turn_hits(player_list[0], turn_summary)
        p1_hits = self.panel_turn_hits(player_list[1], turn_summary)
        p2_hits = self.panel_turn_hits(player_list[2], turn_summary)
        p3_hits = self.panel_turn_hits(player_list[3], turn_summary)
        p0_hit_sum = self.panel_score_sum(player_list[0], turn_summary)
        p1_hit_sum = self.panel_score_sum(player_list[1], turn_summary)
        p2_hit_sum = self.panel_score_sum(player_list[2], turn_summary)
        p3_hit_sum = self.panel_score_sum(player_list[3], turn_summary)

        c.create_text(10, 20, anchor="w", text=current_name, font=("Arial", 30, "bold"), fill=self.player_color(current_name))
        c.create_text(panel_width * 2 - 10, 20, text=current_team, anchor="e", font=("Arial", 30, "bold"), fill=self.player_color(current_name))
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
            c.create_text(10, 140, anchor="w", text=f"Next player: {next_player.name}", font=("Arial", 30, "bold"), fill=self.player_color(next_player))
            c.create_text(panel_width * 2 - 10, 140, anchor="e", text=self.team_name_for_player(next_player), font=("Arial", 30, "bold"), fill=self.player_color(next_player))
            c.create_text(10, 140, anchor="w", text="Next player:", font=("Arial", 30, "bold"), fill="black")

        image_positions = [
            (width / 2 + panel_width, 12, 72),
            (width / 2 - panel_width, 12 + panel_height, 72 + panel_height),
            (width / 2, 12 + panel_height, 72 + panel_height),
            (width / 2 + panel_width, 12 + panel_height, 72 + panel_height),
        ]
        for index, player in enumerate(player_list):
            x_text, y_text, y_img = image_positions[index]
            c.create_text(x_text, y_text, text=player.name, font=("Arial", 20, "bold"), fill=self.player_color(player))
            image = self.load_player_image(player, pfp_size)
            setattr(self.root, f"image{index}", image)
            c.create_image(x_text, y_img, image=image)

        c.create_text(width / 2 + panel_width * 11 / 8, panel_height - box_height / 2, text=f"{p0_hit_sum}", font=("Arial", 20, "bold"), fill="black")
        x_shift = panel_width / 4
        for idx, hit in enumerate(p0_hits[:3]):
            c.create_text(width / 2 + panel_width * 5 / 8 + x_shift * idx, panel_height - box_height / 2, text=hit, font=("Arial", 20), fill="black")

        bottom_rows = [(p1_hits, p1_hit_sum), (p2_hits, p2_hit_sum), (p3_hits, p3_hit_sum)]
        x_pos = width / 2 - panel_width * 3 / 2 - panel_width / 8
        for hits, score_sum in bottom_rows:
            x_shift = panel_width / 4
            for idx, hit in enumerate(hits[:3]):
                c.create_text(x_pos + x_shift * (idx + 1), panel_height * 2 - box_height / 2, text=hit, font=("Arial", 20), fill="black")
            c.create_text(x_pos + x_shift * 4, panel_height * 2 - box_height / 2, text=f"{score_sum}", font=("Arial", 20, "bold"), fill="black")
            x_pos += panel_width

    def draw_infoboard_individual(self):
        c = self.info_canvas
        c.delete("all")
        width, panel_width, panel_height, pfp_size, box_height = self.infoboard_layout()

        # Creates the main borders
        c.create_line(int(width / 2 - panel_width / 2), panel_height, int(width / 2 - panel_width / 2), panel_height * 2, fill="black", width=3)
        c.create_line(int(width / 2 + panel_width / 2), 0, int(width / 2 + panel_width / 2), panel_height * 2, fill="black", width=3)
        c.create_line(0, panel_height, width, panel_height, fill="black", width=3)

        turn_summary = self.infoboard_turn_summary
        current_name = turn_summary["focus_player"]
        focus_player_list = self.game.rotated_turn_order(start_player=current_name)
        side_player_list = [
            player
            for player in self.game.rotated_turn_order(start_player=self.game.active_player())
            if player.name != current_name
        ]
        p0_current_hits = turn_summary["players"][current_name]["current_hits"]
        # Creates current player (focus) boxes + name
        c.create_text(10, 20, anchor="w", text=current_name, font=("Arial", 30, "bold"), fill=self.player_color(current_name))
        c.create_text(panel_width * 2 - 10, 20, anchor="e", text=str(self.game.score_for_player(focus_player_list[0])), font=("Arial", 30, "bold"), fill=self.player_color(current_name))
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
            c.create_text(10, 140, anchor="w", text=f"Next player: {next_player.name}", font=("Arial", 30, "bold"), fill=self.player_color(next_player))
            c.create_text(10, 140, anchor="w", text="Next player:", font=("Arial", 30, "bold"), fill="black")

        current_summary = turn_summary["players"][current_name]
        current_score_history = self.get_player_score_history(focus_player_list[0])
        if turn_summary["next_player_flag"]:
            p0_hits = current_summary["current_hits"]
            p0_hit_sum = current_score_history[-1] if current_score_history else 0
        else:
            p0_hits = current_summary["previous_hits"]
            p0_hit_sum = current_score_history[-2] if len(current_score_history) > 1 else 0

        current_card_player = focus_player_list[0]
        self.draw_player_turn_card(
            c,
            current_card_player,
            width / 2 + panel_width,
            12,
            72,
            pfp_size,
            width / 2 + panel_width / 2,
            panel_height - box_height,
            panel_width,
            box_height,
            p0_hits,
            p0_hit_sum,
            "individual_focus_image",
        )

        remaining_players = side_player_list
        layouts = self.individual_bottom_card_layouts(width, panel_width, panel_height)
        for index, (player, layout) in enumerate(zip(remaining_players, layouts)):
            player_name = player.name if hasattr(player, "name") else player
            hits = turn_summary["players"][player_name]["previous_hits"]
            score_history = self.get_player_score_history(player)
            score_sum = score_history[-1] if score_history else 0
            image_center, label_y, image_y, cell_left = layout
            self.draw_player_turn_card(
                c,
                player,
                image_center,
                label_y,
                image_y,
                pfp_size,
                cell_left,
                panel_height * 2 - box_height,
                panel_width,
                box_height,
                hits,
                score_sum,
                f"individual_image_{index}",
            )
    
    def draw_recboard(self):
        c = self.rec_canvas
        c.delete("all")

        size_x = 454
        size_y = 98
        rec_size_x = 100
        rec_size_y = 60

        score = self.game.score_for_player(self.game.active_player())
        darts_used = self.game.darts_in_turn
        darts_left = 3 if darts_used == 0 else 3 - darts_used
        hits = get_recommended_hits(darts_left, score)

        for hh, hit in enumerate(hits):
            c.create_rectangle(
                (hh+1)*size_x/(len(hits)+1)-rec_size_x/2,
                size_y/2-rec_size_y/2,
                (hh+1)*size_x/(len(hits)+1)+rec_size_x/2,
                size_y/2+rec_size_y/2,
                fill=REC_FILL,
                outline=REC_FILL
            )

            c.create_text(
                (hh+1)*size_x/(len(hits)+1),
                size_y/2,
                text=hit,
                anchor="center",
                font=("Arial",40,"bold"),
                fill="white"
            )

        if not hits:
            c.create_rectangle(
                size_x/2-150,
                size_y/2-rec_size_y/2,
                size_x/2+150,
                size_y/2+rec_size_y/2,
                fill=REC_FILL_RED,
                outline=REC_FILL_RED
            )

            c.create_text(
                size_x/2,
                size_y/2,
                text="No Double Out",
                anchor="center",
                font=("Arial",40,"bold"),
                fill="white"
            )

    def draw_zoomboard(self,x,y):
        c = self.canvas_zoom
        c.delete("all")

        zoom_factor = 3
        line_size = 50
        canvas_size = 460
        img = self.zoom_source_img.copy()
        img = img.crop((int(x-300/zoom_factor),int(y-300/zoom_factor),int(x+300/zoom_factor),int(y+300/zoom_factor)))
        img = img.resize((canvas_size,canvas_size), Image.Resampling.LANCZOS)
        self.zoom_img = ImageTk.PhotoImage(img)
        c.create_image(0,0,anchor=tk.NW,image=self.zoom_img)

        # Dart markers
        hist = self.dart_history[::-1]
        recent_hist = hist[0:6]

        if hist:
            shown_players = []
            for hit in recent_hist:
                if hit["player"] not in shown_players:
                    shown_players.append(hit["player"])
                if len(shown_players) > 2:
                    break
                x_dot = (hit["x"] - x) / 600 * canvas_size * zoom_factor + canvas_size / 2
                y_dot = (hit["y"] - y) / 600 * canvas_size * zoom_factor + canvas_size / 2
                c.create_oval(
                    x_dot - 5, y_dot - 5,
                    x_dot + 5, y_dot + 5,
                    fill=self.player_color(hit["player"]), outline=""
                )

        # Center cross
        active_color = self.player_color(self.game.active_player())
        c.create_line(canvas_size/2-line_size/2,canvas_size/2,canvas_size/2+line_size/2,canvas_size/2,width=4,fill=active_color)
        c.create_line(canvas_size/2,canvas_size/2-line_size/2,canvas_size/2,canvas_size/2+line_size/2,width=4,fill=active_color)

        number, mult = interpret_click(x,y)
        miss_zone = classify_miss_zone(x, y)
        if miss_zone["bounce_out"]:
            hover_label = "BO"
        elif miss_zone["offboard"]:
            hover_label = "OB"
        else:
            hover_label = format_hit_label(number, mult)
        c.create_text(canvas_size/2+75, canvas_size/2, text=hover_label, fill=active_color, font=("Arial",40,"bold"))

    def draw_statsboard(self):
        if self.is_individual_mode():
            self.draw_statsboard_individual()
            return

        c = self.stats_canvas
        c.delete("all")

        width = max(int(c.winfo_width()), int(float(c["width"])))
        height = max(int(c.winfo_height()), int(float(c["height"])))
        if width <= 24 or height <= 24:
            return

        players = self.stats_cache.get("players", [])
        teams = self.stats_cache.get("teams", [])
        distribution = self.stats_cache.get("distribution", {0: [], 1: []})
        player_progression = self.stats_cache.get("player_progression", {})
        grouping_progression = self.stats_cache.get("grouping_progression", {})
        bull_accuracy_progression = self.stats_cache.get("bull_accuracy_progression", {})
        plot_limits = self.stats_cache.get("plot_limits", {"max_x": 1, "min_y": 0, "max_y": 501})
        team_players_lookup = self.stats_cache.get("team_players", {0: [], 1: []})
        player_colors = self.stats_cache.get("player_colors", {})
        active_player = self.stats_cache.get("active_player", "")
        surface_text = self.contrast_text_color(c.cget("bg"))
        current_view = self.stats_view_var.get()
        bg_hex = self.tk_color_to_hex(c.cget("bg"))

        outer_pad = 10
        gutter = 8
        col_width = max(1, (width - outer_pad * 2 - gutter) / 2)
        col_lefts = [outer_pad, outer_pad + col_width + gutter]
        title_y = 10

        c.create_text(width / 2, title_y, anchor="n", text="Live Stats", font=("Arial", 19, "bold"), fill=surface_text)

        team_box_height = 44
        player_box_height = 58
        player_gap = 2
        section_gap = 6
        board_title_gap = 20
        board_gap = 6
        board_bottom_pad = 10
        top_y = title_y + 26

        for side, team in enumerate(teams):
            left = col_lefts[side]
            right = left + col_width
            center_x = left + col_width / 2
            team_players = [player for player in players if player["side"] == side]
            team_color = T1_COLOR if side == 0 else T2_COLOR
            team_fill = STATS_PANEL if side == 0 else STATS_PANEL_ALT
            team_text = self.contrast_text_color(team_fill)

            c.create_rectangle(left, top_y, right, top_y + team_box_height, fill=team_fill, outline="")
            c.create_text(center_x, top_y + 7, anchor="n", text=team["label"], font=("Arial", 14, "bold"), fill=team_color)
            self.draw_inline_stats(
                c,
                left + 8,
                top_y + 24,
                [
                    ("AVG", f"{team['avg']:.2f}"),
                    ("B", team["bulls"]),
                    ("OB", team["offboard"]),
                    ("D", team["doubles"]),
                    ("T", team["triples"]),
                ],
                ("Arial", 10, "bold"),
                ("Arial", 10),
                color=team_text,
            )

            y = top_y + team_box_height + 3
            for player in team_players:
                c.create_rectangle(left, y, right, y + player_box_height, fill=STATS_BG, outline="")
                player_text = self.contrast_text_color(STATS_BG)
                c.create_text(left + 8, y + 7, anchor="nw", text=player["name"], font=("Arial", 12, "bold"), fill=player_colors.get(player["name"], team_color))
                if player["name"] == active_player:
                    badge_w = 80
                    c.create_rectangle(right - badge_w-2, y + 7, right - 12, y + 21, fill=SCOREBOARD_HIGHLIGHT, outline="")
                    c.create_text(right - badge_w / 2 - 8, y + 14, text="THROWING", font=("Arial", 8, "bold"), fill="white")
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 24,
                    [
                        ("dt", player["darts"]),
                        ("Pts", player["scored"]),
                        ("AVG", f"{player['avg']:.2f}"),
                        ("B", player["bulls"]),
                        ("D", player["doubles"]),
                        ("T", player["triples"]),
                    ],
                    ("Arial", 9, "bold"),
                    ("Arial", 9),
                    color=player_text,
                )
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 39,
                    [
                        ("OB", player["offboard"]),
                        ("AGI", f"{player['previous_grouping']:.1f}"),
                        ("50+", player["score_50_plus"]),
                        ("75+", player["score_75_plus"]),
                        ("100+", player["score_100_plus"]),
                    ],
                    ("Arial", 9, "bold"),
                    ("Arial", 9),
                    color=player_text,
                )
                y += player_box_height + player_gap

            c.create_text(center_x, y + section_gap, anchor="n", text=current_view, font=("Arial", 12, "bold"), fill=surface_text)
            board_y = y + section_gap + board_title_gap
            available_board_height = max(1, height - board_y - board_bottom_pad)
            board_size = int(max(1, min(col_width, available_board_height)))
            if current_view == "Shot Map":
                board_img = self.zoom_source_img.resize((board_size, board_size), Image.Resampling.LANCZOS)
                self.stats_board_photos[side] = ImageTk.PhotoImage(board_img)
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[side])

                for hit in distribution.get(side, []):
                    dot_x = left + hit["x"] / 600 * board_size
                    dot_y = board_y + hit["y"] / 600 * board_size
                    c.create_oval(dot_x - 2, dot_y - 2, dot_x + 2, dot_y + 2, fill=hit["color"], outline="")

                legend_y = board_y + board_size + board_gap
                legend_x = left
                for player in team_players:
                    color = player_colors.get(player["name"], team_color)
                    c.create_oval(legend_x, legend_y + 2, legend_x + 8, legend_y + 10, fill=color, outline="")
                    c.create_text(legend_x + 12, legend_y, anchor="nw", text=player["name"], font=("Arial", 9, "bold"), fill=surface_text)
                    legend_x += max(48, 16 + len(player["name"]) * 7)
            elif current_view == "Score Plot":
                self.stats_board_photos[side] = self.render_score_plot(
                    board_size,
                    team_players_lookup.get(side, []),
                    player_progression,
                    player_colors,
                    surface_text,
                    bg_hex,
                    plot_limits,
                )
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[side])
            else:
                self.stats_board_photos[side] = self.render_grouping_plot(
                    board_size,
                    team_players_lookup.get(side, []),
                    grouping_progression,
                    bull_accuracy_progression,
                    player_colors,
                    surface_text,
                    bg_hex,
                )
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[side])

    def draw_statsboard_individual(self):
        c = self.stats_canvas
        c.delete("all")

        width = max(int(c.winfo_width()), int(float(c["width"])))
        height = max(int(c.winfo_height()), int(float(c["height"])))
        if width <= 24 or height <= 24:
            return

        players = self.stats_cache.get("players", [])
        distribution = self.stats_cache.get("distribution", {})
        player_progression = self.stats_cache.get("player_progression", {})
        grouping_progression = self.stats_cache.get("grouping_progression", {})
        bull_accuracy_progression = self.stats_cache.get("bull_accuracy_progression", {})
        plot_limits = self.stats_cache.get("plot_limits", {"max_x": 1, "min_y": 0, "max_y": 501})
        player_colors = self.stats_cache.get("player_colors", {})
        active_player = self.stats_cache.get("active_player", "")
        surface_text = self.contrast_text_color(c.cget("bg"))
        current_view = self.stats_view_var.get()
        bg_hex = self.tk_color_to_hex(c.cget("bg"))

        outer_pad = 10
        gutter = 8
        col_width = max(1, (width - outer_pad * 2 - gutter) / 2)
        col_lefts = [outer_pad, outer_pad + col_width + gutter]
        title_y = 10
        c.create_text(width / 2, title_y, anchor="n", text="Live Stats", font=("Arial", 19, "bold"), fill=surface_text)

        split_index = (len(players) + 1) // 2
        groups = [players[:split_index], players[split_index:]]
        player_box_height = 58
        player_gap = 2
        section_gap = 6
        board_title_gap = 20
        board_gap = 6
        board_bottom_pad = 10
        top_y = title_y + 26

        for column_index, group in enumerate(groups):
            left = col_lefts[column_index]
            right = left + col_width
            center_x = left + col_width / 2
            y = top_y

            for player in group:
                color = player_colors.get(player["name"], self.player_color(player["name"]))
                player_text = self.contrast_text_color(STATS_BG)
                c.create_rectangle(left, y, right, y + player_box_height, fill=STATS_BG, outline="")
                c.create_text(left + 8, y + 7, anchor="nw", text=player["name"], font=("Arial", 12, "bold"), fill=color)
                if player["name"] == active_player:
                    badge_w = 80
                    c.create_rectangle(right - badge_w - 2, y + 7, right - 12, y + 21, fill=SCOREBOARD_HIGHLIGHT, outline="")
                    c.create_text(right - badge_w / 2 - 8, y + 14, text="THROWING", font=("Arial", 8, "bold"), fill="white")
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 24,
                    [
                        ("dt", player["darts"]),
                        ("Pts", player["scored"]),
                        ("AVG", f"{player['avg']:.2f}"),
                        ("B", player["bulls"]),
                        ("D", player["doubles"]),
                        ("T", player["triples"]),
                    ],
                    ("Arial", 9, "bold"),
                    ("Arial", 9),
                    color=player_text,
                )
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 39,
                    [
                        ("OB", player["offboard"]),
                        ("AGI", f"{player['previous_grouping']:.1f}"),
                        ("50+", player["score_50_plus"]),
                        ("75+", player["score_75_plus"]),
                        ("100+", player["score_100_plus"]),
                    ],
                    ("Arial", 9, "bold"),
                    ("Arial", 9),
                    color=player_text,
                )
                y += player_box_height + player_gap

            c.create_text(center_x, y + section_gap, anchor="n", text=current_view, font=("Arial", 12, "bold"), fill=surface_text)
            board_y = y + section_gap + board_title_gap
            available_board_height = max(1, height - board_y - board_bottom_pad)
            board_size = int(max(1, min(col_width, available_board_height)))
            group_names = [player["name"] for player in group]
            if current_view == "Shot Map":
                board_img = self.zoom_source_img.resize((board_size, board_size), Image.Resampling.LANCZOS)
                self.stats_board_photos[column_index] = ImageTk.PhotoImage(board_img)
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[column_index])
                for player in group:
                    for hit in distribution.get(player["side"], []):
                        dot_x = left + hit["x"] / 600 * board_size
                        dot_y = board_y + hit["y"] / 600 * board_size
                        c.create_oval(dot_x - 2, dot_y - 2, dot_x + 2, dot_y + 2, fill=hit["color"], outline="")

                legend_y = board_y + board_size + board_gap
                legend_x = left
                for player_name in group_names:
                    color = player_colors.get(player_name, self.player_color(player_name))
                    c.create_oval(legend_x, legend_y + 2, legend_x + 8, legend_y + 10, fill=color, outline="")
                    c.create_text(legend_x + 12, legend_y, anchor="nw", text=player_name, font=("Arial", 9, "bold"), fill=surface_text)
                    legend_x += max(48, 16 + len(player_name) * 7)
            elif current_view == "Score Plot":
                self.stats_board_photos[column_index] = self.render_score_plot(
                    board_size,
                    group_names,
                    player_progression,
                    player_colors,
                    surface_text,
                    bg_hex,
                    plot_limits,
                )
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[column_index])
            else:
                self.stats_board_photos[column_index] = self.render_grouping_plot(
                    board_size,
                    group_names,
                    grouping_progression,
                    bull_accuracy_progression,
                    player_colors,
                    surface_text,
                    bg_hex,
                )
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[column_index])


if __name__ == "__main__":
    root = tk.Tk()
    app = DartsApp(root)
    root.mainloop()
