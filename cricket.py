import os
import tkinter as tk
from datetime import datetime
from math import ceil, hypot
from tkinter import messagebox, simpledialog, ttk

from PIL import Image, ImageTk
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-codex")
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, LinearLocator

from dart_engine.helpers_cricket import cricket_marks
from dart_engine.cricket_stats import build_all_cricket_marks_by_turn
from dart_engine.helpers_general import (
    classify_miss_zone,
    get_screen_size_tkinter,
    interpret_click,
    swap_players_history,
    swap_teams_history,
)
from dart_engine.params_cricket import CricketGame as TeamCricketGame
from dart_engine.params_cricket import Hit as TeamHit
from dart_engine.params_cricket_1x1 import CricketGame as SoloCricketGame
from dart_engine.params_cricket_1x1 import Hit as SoloHit
from dart_engine.params_cricket_cutthroat import CricketGame as CutthroatCricketGame
from dart_engine.params_cricket_cutthroat import Hit as CutthroatHit
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
    replay_dart_history,
    save_dart_history,
    show_save_confirmation,
    show_winner_animation,
    update_app_config,
)

CRICKET_NUMBERS = [20, 19, 18, 17, 16, 15, 25]
CONFIG_FILE = "dart_engine/config.json"
T1_COLOR = "#6a83ff"
T2_COLOR = "#ec6d00"
T3_COLOR = "#2e9e4f"
SIDE_COLORS = [T1_COLOR, T2_COLOR, T3_COLOR]
SCOREBOARD_BG = "darkolivegreen"
INFOBOARD_BG = "white"
SCOREBOARD_HIGHLIGHT = "olivedrab"
RECBOARD_BG = "#323232"
REC_FILL = "dimgray"
REC_FILL_RED = "dimgray"
STATS_BG = "#f3efe7"
STATS_PANEL = "#e5ddd0"
STATS_PANEL_ALT = "#ddd3c3"
STATS_PANEL_ALT2 = "#d3ddc9"
TEXT_DARK = "#2f2419"
TEXT_LIGHT = "#f5f1ea"
TEXT_LIGHT = "#f5f1ea"


class DartsApp:
    def __init__(self, root, on_back=None, initial_mode="2v2"):
        self.root = root
        self.on_back = on_back
        root.title("Cricket Darts")
        root.attributes("-fullscreen", True)
        x = root.winfo_width()
        y = root.winfo_height()
        self.window_height = y

        # Controls below the board are stacked in 6 rows; space them to fill
        # whatever vertical room this screen actually has instead of assuming
        # one fixed resolution (MacBook Air vs. MacBook Pro differ by ~30px).
        content_top = 700
        row_step = max(30, (y - content_top - 55) / 5)
        self.row_y = [content_top + i * row_step for i in range(6)]

        self.folder_path, self.player_options = load_app_config(CONFIG_FILE)
        self.game = None

        self.folder_path_var = tk.StringVar(
            value=self.folder_path if self.folder_path is not None else "Save directory not set"
        )

        img = Image.open("dartboard_images/dartboard_accurate.png")
        self.size = 600
        img = img.resize((self.size, self.size))
        self.board_img = ImageTk.PhotoImage(img)
        self.zoom_source_img = img
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        self.profile_image_cache = {}
        self.infoboard_turn_summary = None
        self.stats_cache = {}
        self.stats_board_photos = {}
        self.stats_view_var = tk.StringVar(value="Shot Map")
        self.winner_dialog_shown = False

        self.canvas = tk.Canvas(root, width=self.size, height=self.size)
        self.canvas.pack()

        right_column_width = self.screen_width / 2 - self.size / 2 - 2
        right_column_x = self.screen_width / 2 + self.size / 2 - 3
        zoom_height = right_column_width

        self.canvas_zoom = tk.Canvas(
            root,
            width=right_column_width,
            height=zoom_height,
            bg="white",
        )
        self.canvas_zoom.place(x=right_column_x, y=0)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.board_img)

        # self.cursor_label = tk.Label(root, text="x: 0  y: 0", font=("Arial", 10))
        # self.cursor_label.pack(anchor="w")

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)

        self.score_canvas = tk.Canvas(
            root,
            width=x / 2 - self.size / 2 - 2,
            height=600 - 2,
            bg=SCOREBOARD_BG,
        )
        self.score_canvas.place(x=0, y=0)

        self.rec_canvas = tk.Canvas(
            root,
            width=x / 2 - self.size / 2 - 2,
            height=100 - 2,
            bg=RECBOARD_BG,
        )
        self.rec_canvas.place(x=0, y=600)

        self.info_canvas = tk.Canvas(root, width=self.size - 7, height=y - 600 - 4, bg=INFOBOARD_BG)
        self.info_canvas.place(x=x / 2 - self.size / 2 + 1, y=600)

        stats_y = int(zoom_height) + 2
        # stats_control_height = 20 - stats_control_height - 8
        stats_height = self.screen_height - stats_y - 2
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
        btn_frame1.place(x=5, y=self.row_y[0])
        if self.on_back:
            tk.Button(btn_frame1, text="Menu", font=("Arial", 24), command=self.on_back, padx=0).pack(side=tk.LEFT)
        tk.Button(btn_frame1, text="Undo", font=("Arial", 24), command=self.undo, padx=0).pack(side=tk.LEFT)
        tk.Button(btn_frame1, text="Load", font=("Arial", 24), command=self.load, padx=0).pack(side=tk.LEFT)
        tk.Button(btn_frame1, text="New Game", font=("Arial", 24), command=self.reset, padx=0).pack(side=tk.LEFT)

        btn_frame2 = tk.Frame(root)
        btn_frame2.place(x=5, y=self.row_y[1])
        tk.Button(btn_frame2, text="Save", font=("Arial", 24), command=self.save).pack(side=tk.LEFT)
        tk.Button(btn_frame2, text="Save Setup...", font=("Arial", 24), command=self.save_setup).pack(side=tk.LEFT)
        tk.Button(btn_frame2, text="Save As...", font=("Arial", 24), command=self.save_as).pack(side=tk.RIGHT)

        btn_frame3 = tk.Frame(root)
        btn_frame3.place(x=5, y=self.row_y[2])
        tk.Entry(btn_frame3, textvariable=self.folder_path_var, font=("Arial", 16), width=45).pack(
            side=tk.TOP, pady=0
        )

        self.team1a_player_var = tk.StringVar(value=self.player_options[0])
        self.team1b_player_var = tk.StringVar(value=self.player_options[1])
        self.team2a_player_var = tk.StringVar(value=self.player_options[2])
        self.team2b_player_var = tk.StringVar(value=self.player_options[3])
        self.team1_name_var = tk.StringVar(value="1236")
        self.team2_name_var = tk.StringVar(value="930")

        self.team1_frame = tk.Frame(root)
        self.team1_frame.place(x=0, y=self.row_y[3])
        self.team1_name_button = tk.Button(
            self.team1_frame,
            textvariable=self.team1_name_var,
            font=("Arial", 20),
            command=lambda: self.prompt_team_name_change(0),
            width=6,
        )
        self.team1_name_button.pack(side=tk.LEFT, padx=(5, 6))
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
        self.team2_frame.place(x=0, y=self.row_y[4])
        self.team2_name_button = tk.Button(
            self.team2_frame,
            textvariable=self.team2_name_var,
            font=("Arial", 20),
            command=lambda: self.prompt_team_name_change(1),
            width=6,
        )
        self.team2_name_button.pack(side=tk.LEFT, padx=(5, 6))
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

        self.team3a_player_var = tk.StringVar(
            value=self.player_options[1 % len(self.player_options)] if self.player_options else ""
        )
        self.team3_frame = tk.Frame(root)
        self.team3_frame.place(x=360, y=self.row_y[4])
        self.dropdown_3a = ttk.Combobox(
            self.team3_frame,
            textvariable=self.team3a_player_var,
            values=self.player_options,
            font=("Arial", 20),
            state="readonly",
            width=6,
        )
        self.dropdown_3a.pack(side=tk.LEFT, padx=(5, 0))
        self.dropdown_3a.bind("<<ComboboxSelected>>", self.update_players)
        self.team3_frame.place_forget()

        btn_frame6 = tk.Frame(root)
        btn_frame6.place(x=0, y=self.row_y[5])
        self.swap_teams_button = tk.Button(btn_frame6, text="Swap teams", font=("Arial", 20), command=self.swap_teams)
        self.swap_teams_button.pack(side=tk.LEFT)
        tk.Button(btn_frame6, text="Add Player", font=("Arial", 20), command=self.add_player).pack(side=tk.LEFT)

        self.mode_var = tk.StringVar(value="2v2")
        ttk.Combobox(
            btn_frame6,
            textvariable=self.mode_var,
            values=["2v2", "1v1", "cutthroat"],
            font=("Arial", 18),
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT)
        self.mode_var.trace_add("write", self.handle_mode_change)


        self.dart_markers = {0: [], 1: [], 2: []}
        self.dart_history = []
        self.mark_history_cache = {}

        self.set_game_mode(initial_mode, preserve_names=False)

    def is_solo_mode(self):
        return self.mode_var.get() == "1v1"

    def is_cutthroat_mode(self):
        return self.mode_var.get() == "cutthroat"

    def stats_side_count(self):
        return 3 if self.is_cutthroat_mode() else 2

    def side_color(self, side):
        return SIDE_COLORS[side % len(SIDE_COLORS)]

    def current_hit_class(self):
        if self.is_cutthroat_mode():
            return CutthroatHit
        return SoloHit if self.is_solo_mode() else TeamHit

    def active_side(self):
        return self.game.team_index_for_player(self.game.active_player())

    def current_order_size(self):
        if self.is_cutthroat_mode():
            return 3
        return 2 if self.is_solo_mode() else 4

    def team_names_from_vars(self):
        if self.is_cutthroat_mode():
            return [[self.team1a_player_var.get()], [self.team2a_player_var.get()], [self.team3a_player_var.get()]]
        if self.is_solo_mode():
            return [[self.team1a_player_var.get()], [self.team2a_player_var.get()]]
        return [
            [self.team1a_player_var.get(), self.team1b_player_var.get()],
            [self.team2a_player_var.get(), self.team2b_player_var.get()],
        ]

    def apply_player_vars_to_game(self):
        team_names = self.team_names_from_vars()
        if self.is_cutthroat_mode():
            self.game.set_player_names([group[0] for group in team_names])
        elif self.is_solo_mode():
            self.game.set_player_names([team_names[0][0], team_names[1][0]])
        else:
            self.game.set_team_player_names(0, team_names[0])
            self.game.set_team_player_names(1, team_names[1])
            self.game.set_team_name(0, self.team1_name_var.get().strip() or "Team 1")
            self.game.set_team_name(1, self.team2_name_var.get().strip() or "Team 2")

    def sync_player_vars_from_game(self):
        if self.is_cutthroat_mode():
            self.team1a_player_var.set(self.game.players[0].name)
            self.team2a_player_var.set(self.game.players[1].name)
            self.team3a_player_var.set(self.game.players[2].name)
        elif self.is_solo_mode():
            self.team1a_player_var.set(self.game.players[0].name)
            self.team2a_player_var.set(self.game.players[1].name)
        else:
            self.team1a_player_var.set(self.game.teams[0].players[0].name)
            self.team1b_player_var.set(self.game.teams[0].players[1].name)
            self.team2a_player_var.set(self.game.teams[1].players[0].name)
            self.team2b_player_var.set(self.game.teams[1].players[1].name)
            self.team1_name_var.set(self.game.teams[0].name)
            self.team2_name_var.set(self.game.teams[1].name)

    def update_mode_controls(self):
        if self.is_cutthroat_mode():
            for widget in (self.team1_name_button, self.dropdown_1b, self.swap_team_1_button):
                widget.pack_forget()
            self.dropdown_1a.pack_forget()
            self.dropdown_1a.pack(side=tk.LEFT)

            for widget in (self.team2_name_button, self.dropdown_2b, self.swap_team_2_button):
                widget.pack_forget()
            self.dropdown_2a.pack_forget()
            self.dropdown_2a.pack(side=tk.LEFT)

            self.team2_frame.update_idletasks()
            team3_x = self.team2_frame.winfo_x() + self.team2_frame.winfo_reqwidth() + 8
            self.team3_frame.place(x=team3_x, y=self.row_y[4])
        elif self.is_solo_mode():
            self.team1_name_button.pack_forget()
            self.team2_name_button.pack_forget()
            self.dropdown_1b.pack_forget()
            self.dropdown_2b.pack_forget()
            self.swap_team_1_button.pack_forget()
            self.swap_team_2_button.pack_forget()
            self.team3_frame.place_forget()
        else:
            for widget in (self.team1_name_button, self.dropdown_1a, self.dropdown_1b, self.swap_team_1_button):
                widget.pack_forget()
            self.team1_name_button.pack(side=tk.LEFT, padx=(5, 6))
            self.dropdown_1a.pack(side=tk.LEFT)
            self.dropdown_1b.pack(side=tk.LEFT)
            self.swap_team_1_button.pack(side=tk.LEFT)

            for widget in (self.team2_name_button, self.dropdown_2a, self.dropdown_2b, self.swap_team_2_button):
                widget.pack_forget()
            self.team2_name_button.pack(side=tk.LEFT, padx=(5, 6))
            self.dropdown_2a.pack(side=tk.LEFT)
            self.dropdown_2b.pack(side=tk.LEFT)
            self.swap_team_2_button.pack(side=tk.LEFT)
            self.team3_frame.place_forget()

    def set_game_mode(self, mode, preserve_names=True):
        existing_names = self.team_names_from_vars() if preserve_names else None
        existing_team_names = [self.team1_name_var.get(), self.team2_name_var.get()] if preserve_names else None
        self.mode_var.set(mode)
        if mode == "cutthroat":
            self.game = CutthroatCricketGame()
        elif mode == "1v1":
            self.game = SoloCricketGame()
        else:
            self.game = TeamCricketGame()

        if preserve_names and existing_names:
            if mode == "cutthroat":
                names = [group[0] for group in existing_names[:3]]
                while len(names) < 3:
                    names.append(self.player_options[len(names) % len(self.player_options)])
                self.team1a_player_var.set(names[0])
                self.team2a_player_var.set(names[1])
                self.team3a_player_var.set(names[2])
            elif mode == "1v1":
                solo_names = [existing_names[0][0], existing_names[1][0]]
                self.team1a_player_var.set(solo_names[0])
                self.team2a_player_var.set(solo_names[1])
            elif existing_team_names:
                self.team1_name_var.set(existing_team_names[0])
                self.team2_name_var.set(existing_team_names[1])
            self.apply_player_vars_to_game()
        else:
            self.seed_default_players()

        self.sync_player_vars_from_game()
        self.update_mode_controls()
        self.clear_all_darts()
        self.refresh_caches()
        self.update_label()

    def seed_default_players(self):
        names = self.player_options
        if not names:
            return
        n = self.current_order_size()
        default_names = [names[i % len(names)] for i in range(n)]
        if self.is_cutthroat_mode() or self.is_solo_mode():
            self.game.set_player_names(default_names)
        else:
            self.game.set_team_player_names(0, default_names[0:2])
            self.game.set_team_player_names(1, default_names[2:4])

    def handle_mode_change(self, *_):
        if self.game is None:
            return
        self.set_game_mode(self.mode_var.get())

    def update_cursor(self, event):
        # self.cursor_label.config(text=f"x: {event.x}   y: {event.y}")
        self.draw_zoomboard(event.x, event.y)

    def click(self, event):
        if self.game.winner:
            return

        number, mult = interpret_click(event.x, event.y)
        if number is None:
            return

        marker_list = self.dart_markers[self.active_side()]
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
        miss_zone = classify_miss_zone(event.x, event.y) if number == 0 else {"offboard": False, "bounce_out": False}
        self.dart_history.append(
            {
                "player": player.name,
                "team": self.active_side(),
                "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                "x": event.x,
                "y": event.y,
                "number": number,
                "multiplier": mult,
                "offboard": miss_zone["offboard"] or (number == 0 and not miss_zone["bounce_out"]),
                "bounce_out": miss_zone["bounce_out"],
            }
        )

        self.game.register_hit(self.current_hit_class()(number, mult, (event.x, event.y)))
        if self.game.darts_in_turn == 0:
            self.clear_team_darts()

        self.refresh_caches()
        self.update_label()
        self.prompt_save_on_winner()
        self.draw_zoomboard(event.x, event.y)

    def update_label(self):
        self.update_infoboard_turn_summary()
        self.draw_infoboard()
        self.draw_scoreboard()
        self.draw_recboard()
        self.draw_statsboard()

    def draw_current_dart_marker(self, x, y):
        marker_list = self.dart_markers[self.active_side()]
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
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def player_color(self, player):
        return self.side_color(self.game.team_index_for_player(player))

    def team_name_for_player(self, player):
        if self.is_solo_mode() or self.is_cutthroat_mode():
            return ""
        return self.game.team_for_player(player).name

    def stats_players_in_display_order(self):
        if self.is_solo_mode() or self.is_cutthroat_mode():
            return list(self.game.players)
        return [player for team in self.game.teams for player in team.players]

    def team_player_colors(self, side, count):
        palettes = {
            0: ["#0b5cff", "#00a6fb", "#123b8f", "#58c4ff"],
            1: ["#d94801", "#ff8c00", "#8c2f00", "#ffb454"],
            2: ["#1f8a44", "#2fbf5e", "#0f5c2b", "#7bd99a"],
        }
        palette = palettes[side]
        return [palette[index % len(palette)] for index in range(max(1, count))]

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
        max_effective_spread = self.size * 0.8
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

    def scoring_objects_for_side(self, side):
        if self.is_solo_mode():
            return self.game.players[side], self.game.players[1 - side]
        return self.game.teams[side], self.game.teams[1 - side]

    def scoring_label_for_side(self, side):
        if self.is_solo_mode():
            return self.game.players[side].name
        return self.game.teams[side].name

    def bulls_left_to_win(self, side):
        current, opponent = self.scoring_objects_for_side(side)
        bull_marks_to_close = max(0, 3 - current.cricket_display[25])
        if current.score >= opponent.score:
            return bull_marks_to_close

        score_gap = opponent.score - current.score
        scoring_bulls = ceil(score_gap / 25)
        return bull_marks_to_close + scoring_bulls

    def bull_finish_available(self, side):
        current, _ = self.scoring_objects_for_side(side)
        return all(current.cricket_closed[number] for number in CRICKET_NUMBERS if number != 25)

    def draw_inline_stats(self, canvas, x, y, stats, label_font, value_font, color=TEXT_DARK, gap=10):
        cursor_x = x
        for label, value in stats:
            label_id = canvas.create_text(
                cursor_x,
                y,
                anchor="nw",
                text=label,
                font=label_font,
                fill=color,
            )
            bbox = canvas.bbox(label_id)
            cursor_x = (bbox[2] if bbox else cursor_x) + 3
            value_id = canvas.create_text(
                cursor_x,
                y,
                anchor="nw",
                text=str(value),
                font=value_font,
                fill=color,
            )
            bbox = canvas.bbox(value_id)
            cursor_x = (bbox[2] if bbox else cursor_x) + gap

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

    def render_cricket_progress_plot(self, size, player_names, progression, player_colors, text_color, bg_color, axis_limits):
        bg_color = "#ffffff"
        text_color = "#000000"
        fig = Figure(figsize=(size / 100, size / 100), dpi=100, facecolor=bg_color)
        ax_left = fig.add_subplot(111)
        ax_right = ax_left.twinx()
        ax_left.set_facecolor(bg_color)
        ax_right.set_facecolor("none")

        max_x = axis_limits["max_x"]
        max_marks = axis_limits["max_marks"]
        max_points = axis_limits["max_points"]
        if max_x == 0:
            max_x = 1
        if max_marks == 0:
            max_marks = 1
        if max_points == 0:
            max_points = 1

        ax_left.set_xlim(0, max_x)
        ax_left.set_ylim(0, max_marks)
        ax_right.set_ylim(0, max_points)
        ax_left.set_yticks(list(range(0, max_marks + 1, 5)))
        ax_left.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.35, color=text_color)

        right_tick_step = max(10, int(round(max_points / 4 / 10.0) * 10) or 10)
        ax_right.set_yticks(list(range(0, max_points + 1, right_tick_step)))

        for name in player_names:
            series = progression.get(name, {"marks": [(0, 0)], "points": [(0, 0)]})
            color = player_colors.get(name, text_color)
            mark_x = [darts for darts, _ in series["marks"]]
            mark_y = [marks for _, marks in series["marks"]]
            point_x = [darts for darts, _ in series["points"]]
            point_y = [points for _, points in series["points"]]
            ax_left.plot(mark_x, mark_y, color=color, linewidth=2.5, marker="o", markersize=3)
            ax_right.plot(point_x, point_y, color=color, linewidth=2.0, linestyle="--")

        legend_handles = [ax_left.plot([], [], color="#000000", linewidth=2.5)[0], ax_left.plot([], [], color="#000000", linewidth=2.0, linestyle="--")[0]]
        legend_labels = ["Marks", "Points"]
        for name in player_names:
            legend_handles.append(ax_left.plot([], [], color=player_colors.get(name, "#000000"), linewidth=2.5)[0])
            legend_labels.append(name)
        ax_left.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.2),
            frameon=False,
            fontsize=7,
            ncol=2,
        )

        ax_left.set_xlabel("dt", color=text_color, fontsize=8)
        ax_left.xaxis.labelpad = 2
        ax_left.set_ylabel("M", color=text_color, fontsize=8, fontweight="bold")
        ax_right.set_ylabel("Pts", color=text_color, fontsize=8, fontweight="bold")
        ax_left.yaxis.labelpad = 2
        ax_right.yaxis.labelpad = 2
        ax_left.tick_params(axis="x", colors=text_color, labelsize=8)
        ax_left.tick_params(axis="y", colors=text_color, labelsize=8)
        ax_right.tick_params(axis="y", colors=text_color, labelsize=8)
        for spine in ("bottom", "left"):
            ax_left.spines[spine].set_color(text_color)
        ax_left.spines["top"].set_visible(False)
        ax_right.spines["top"].set_visible(False)
        ax_right.spines["left"].set_visible(False)
        ax_right.spines["right"].set_color(text_color)
        fig.subplots_adjust(left=0.24, right=0.76, bottom=0.3, top=0.93)

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        rgba = canvas.buffer_rgba()
        image = Image.frombuffer("RGBA", canvas.get_width_height(), rgba, "raw", "RGBA", 0, 1)
        return ImageTk.PhotoImage(image)

    def render_cricket_grouping_plot(self, size, player_names, grouping_progression, bull_accuracy_progression, player_colors, text_color, bg_color):
        bg_color = "#ffffff"
        text_color = "#000000"
        fig = Figure(figsize=(size / 100, size / 100), dpi=100, facecolor=bg_color)
        ax_left = fig.add_subplot(111)
        ax_right = ax_left.twinx()
        ax_left.set_facecolor(bg_color)
        ax_right.set_facecolor("none")

        legend_handles = []
        legend_labels = []
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
            legend_handles.append(handle)
            legend_labels.append(name)

        legend_handles = [
            ax_left.plot([], [], color="#000000", linewidth=2.5)[0],
            ax_left.plot([], [], color="#000000", linewidth=2.0, linestyle="--")[0],
            *legend_handles,
        ]
        legend_labels = ["AGI", "Bull Dist", *legend_labels]

        ax_left.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.2),
            frameon=False,
            fontsize=7,
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

        ax_left.grid(True, axis="y", which="major", linestyle="--", linewidth=0.6, alpha=0.35, color=text_color)
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
        for spine in ("bottom", "left"):
            ax_left.spines[spine].set_color(text_color)
        ax_left.spines["top"].set_visible(False)
        ax_right.spines["top"].set_visible(False)
        ax_right.spines["left"].set_visible(False)
        ax_right.spines["right"].set_color(text_color)
        fig.subplots_adjust(left=0.24, right=0.78, bottom=0.3, top=0.93)

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        rgba = canvas.buffer_rgba()
        image = Image.frombuffer("RGBA", canvas.get_width_height(), rgba, "raw", "RGBA", 0, 1)
        return ImageTk.PhotoImage(image)

    def get_player_mark_history(self, player):
        player_name = player.name if hasattr(player, "name") else player
        return self.mark_history_cache.get(player_name, [0])

    def update_mark_history_cache(self):
        if self.is_solo_mode() or self.is_cutthroat_mode():
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

    def update_stats_cache(self):
        players = self.stats_players_in_display_order()
        player_stats = {
            player.name: {
                "name": player.name,
                "side": self.game.team_index_for_player(player),
                "darts": 0,
                "marks": 0,
                "scoring_hits": 0,
                "bulls": 0,
                "offboard": 0,
                "doubles": 0,
                "triples": 0,
                "points": 0,
                "previous_grouping": 0.0,
            }
            for player in players
        }

        sides = list(range(self.stats_side_count()))

        if self.is_cutthroat_mode():
            team_labels = [player.name for player in self.game.players]
        elif self.is_solo_mode():
            team_labels = [self.game.players[0].name, self.game.players[1].name]
        else:
            team_labels = [self.game.teams[0].name, self.game.teams[1].name]

        team_stats = {
            side: {
                "label": team_labels[side],
                "darts": 0,
                "marks": 0,
                "scoring_hits": 0,
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
        player_progression = {
            player.name: {"marks": [(0, 0)], "points": [(0, 0)]}
            for player in players
        }
        grouping_progression = {player.name: [] for player in players}
        bull_accuracy_progression = {player.name: [] for player in players}
        completed_turns = {player.name: [] for player in players}
        current_turn_player = None
        current_turn_hits = []
        team_remaining = {side: {number: 3 for number in CRICKET_NUMBERS} for side in sides}
        player_marks_total = {player.name: 0 for player in players}
        player_points_total = {player.name: 0 for player in players}
        player_darts_progress = {player.name: 0 for player in players}
        grouping_turn_index = {player.name: 0 for player in players}

        def side_numbers_closed(side):
            return all(team_remaining[side][number] == 0 for number in CRICKET_NUMBERS if number != 25)

        for hit in self.dart_history:
            player_name = hit["player"]
            side = self.game.team_index_for_player(player_name) if player_name in player_stats else hit.get("team", 0)
            number = hit["number"]
            multiplier = hit["multiplier"]
            points_scored = 0
            marks_scored = 0
            valid_mark_hit = False

            if player_name != current_turn_player:
                if current_turn_player in completed_turns and len(current_turn_hits) == 3:
                    completed_turns[current_turn_player].append(current_turn_hits)
                current_turn_player = player_name
                current_turn_hits = []
            current_turn_hits.append(hit)

            if number in CRICKET_NUMBERS:
                hits_remaining = team_remaining[side][number]
                overflow_hits = max(0, multiplier - hits_remaining)
                if hits_remaining > 0:
                    applied_hits = min(multiplier, hits_remaining)
                    team_remaining[side][number] -= applied_hits
                    marks_scored += applied_hits
                open_opponents = sum(1 for s in sides if s != side and team_remaining[s][number] > 0)
                if team_remaining[side][number] == 0 and open_opponents:
                    points_scored = overflow_hits * number * open_opponents
                    marks_scored += overflow_hits

            valid_mark_hit = marks_scored > 0

            if player_name in player_stats:
                player_stats[player_name]["darts"] += 1
                player_stats[player_name]["marks"] += marks_scored
                player_stats[player_name]["scoring_hits"] += 1 if valid_mark_hit else 0
                player_stats[player_name]["bulls"] += 1 if number == 25 and valid_mark_hit else 0
                player_stats[player_name]["offboard"] += 1 if number == 0 else 0
                player_stats[player_name]["doubles"] += 1 if multiplier == 2 and valid_mark_hit else 0
                player_stats[player_name]["triples"] += 1 if multiplier == 3 and valid_mark_hit else 0
                player_stats[player_name]["points"] += points_scored

            team_stats[side]["darts"] += 1
            team_stats[side]["marks"] += marks_scored
            team_stats[side]["scoring_hits"] += 1 if valid_mark_hit else 0
            team_stats[side]["bulls"] += 1 if number == 25 and valid_mark_hit else 0
            team_stats[side]["offboard"] += 1 if number == 0 else 0
            team_stats[side]["doubles"] += 1 if multiplier == 2 and valid_mark_hit else 0
            team_stats[side]["triples"] += 1 if multiplier == 3 and valid_mark_hit else 0
            if player_name in player_progression:
                player_darts_progress[player_name] += 1
                player_marks_total[player_name] += marks_scored
                player_points_total[player_name] += points_scored
                player_progression[player_name]["marks"].append((player_darts_progress[player_name], player_marks_total[player_name]))
                player_progression[player_name]["points"].append((player_darts_progress[player_name], player_points_total[player_name]))
            distribution_points[side].append(
                {
                    "x": hit["x"],
                    "y": hit["y"],
                    "player": player_name,
                    "color": player_color_lookup.get(player_name, self.side_color(side)),
                }
            )

            if len(current_turn_hits) == 3:
                completed_turns[player_name].append(current_turn_hits.copy())
                if side_numbers_closed(side):
                    grouping_turn_index[player_name] += 1
                    grouping_progression[player_name].append(
                        (grouping_turn_index[player_name], self.previous_turn_grouping(current_turn_hits))
                    )
                    bull_accuracy_progression[player_name].append(
                        (grouping_turn_index[player_name], self.turn_bull_accuracy(current_turn_hits))
                    )
                current_turn_player = None
                current_turn_hits = []

        for stats in player_stats.values():
            stats["mpr"] = (stats["marks"] * 3 / stats["darts"]) if stats["darts"] else 0.0
            stats["hit_rate"] = (stats["scoring_hits"] / stats["darts"] * 100) if stats["darts"] else 0.0
            turns = completed_turns.get(stats["name"], [])
            stats["previous_grouping"] = self.previous_turn_grouping(turns[-1]) if turns else 0.0

        for side in sides:
            team_stats[side]["mpr"] = (
                team_stats[side]["marks"] * 3 / team_stats[side]["darts"]
                if team_stats[side]["darts"]
                else 0.0
            )
            team_stats[side]["hit_rate"] = (
                team_stats[side]["scoring_hits"] / team_stats[side]["darts"] * 100
                if team_stats[side]["darts"]
                else 0.0
            )

        max_plot_x = max(
            (point[0] for series in player_progression.values() for point in series["marks"]),
            default=1,
        )
        max_plot_marks = max(
            (point[1] for series in player_progression.values() for point in series["marks"]),
            default=0,
        )
        max_plot_points = max(
            (point[1] for series in player_progression.values() for point in series["points"]),
            default=0,
        )
        plot_limits = {
            "max_x": max(1, max_plot_x),
            "max_marks": max(5, int(ceil((max_plot_marks + 1) / 5.0) * 5)),
            "max_points": max(10, int(ceil((max_plot_points + 2) / 10.0) * 10)),
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
        self.update_mark_history_cache()
        self.update_stats_cache()

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
        cache_key = (player.name, size)
        if cache_key not in self.profile_image_cache:
            image = Image.open(get_profile_pic_path(player.name))
            self.profile_image_cache[cache_key] = ImageTk.PhotoImage(image.resize((size, size)))
        return self.profile_image_cache[cache_key]

    def clear_team_darts(self):
        markers = self.dart_markers[self.active_side()]
        for marker in markers:
            self.canvas.delete(marker)
        markers.clear()

    def clear_all_darts(self):
        for markers in self.dart_markers.values():
            for marker in markers:
                self.canvas.delete(marker)
            markers.clear()

    def prompt_save_on_winner(self):
        if not self.game.winner or self.winner_dialog_shown:
            return
        self.winner_dialog_shown = True
        should_save = show_winner_animation(
            self.root,
            self.game.winner,
            accent_color=self.player_color(self.game.active_player()),
        )
        if should_save:
            self.save()

    def save_setup(self):
        folder_path = choose_save_directory(self.folder_path)
        if not folder_path:
            return
        self.folder_path = folder_path
        self.folder_path_var.set(self.folder_path)
        update_app_config(CONFIG_FILE, last_folder=self.folder_path)

    def save(self):
        if self.is_cutthroat_mode():
            names = "_vs_".join(player.name for player in self.game.players)
            filename = f"cricket_{names}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        elif self.is_solo_mode():
            filename = f"cricket_{self.game.players[0].name}_vs_{self.game.players[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        else:
            filename = f"cricket_{self.game.teams[0].name}_vs_{self.game.teams[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

        if self.folder_path is None:
            self.save_as()
            return
        metadata = {"game_mode": self.mode_var.get()}
        if not self.is_solo_mode() and not self.is_cutthroat_mode():
            metadata["team_names"] = [self.game.teams[0].name, self.game.teams[1].name]
        file_path = os.path.join(self.folder_path, filename)
        save_dart_history(file_path, self.dart_history, metadata=metadata)
        show_save_confirmation(self.root, file_path)

    def save_as(self):
        file_path = ask_history_save_path()
        if file_path:
            metadata = {"game_mode": self.mode_var.get()}
            if not self.is_solo_mode() and not self.is_cutthroat_mode():
                metadata["team_names"] = [self.game.teams[0].name, self.game.teams[1].name]
            save_dart_history(file_path, self.dart_history, metadata=metadata)
            show_save_confirmation(self.root, file_path)

    def load(self):
        file_path = ask_history_load_path(self.folder_path)
        if not file_path:
            return

        saved_game = load_saved_game(file_path)
        self.dart_history = saved_game["dart_history"]
        metadata = saved_game.get("metadata", {})
        turn_order = infer_player_turn_order(self.dart_history, 4)
        mode = metadata.get("game_mode") or ("1v1" if len(turn_order) <= 2 else "2v2")
        self.set_game_mode(mode, preserve_names=False)

        for player in turn_order:
            if player not in self.player_options:
                self.add_player(dialog_popup=False, name=player)

        if self.is_cutthroat_mode():
            vars_in_order = [self.team1a_player_var, self.team2a_player_var, self.team3a_player_var]
            for var, player in zip(vars_in_order, turn_order):
                var.set(player)
        elif self.is_solo_mode():
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
            team_names = metadata.get("team_names", [])
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
        self.save()
        self.dart_history = []
        self.game.reset()
        self.clear_all_darts()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def swap_teams(self):
        if self.is_cutthroat_mode():
            return
        if self.is_solo_mode():
            self.game.swap_players()
        else:
            self.game.swap_teams()
            self.dart_history = swap_teams_history(self.dart_history)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def swap_team_players(self, team_index):
        if self.is_solo_mode() or self.is_cutthroat_mode():
            return
        self.game.swap_team_players(team_index)
        self.dart_history = swap_players_history(self.dart_history, team_index)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def update_players(self, _event):
        self.apply_player_vars_to_game()
        self.refresh_caches()
        self.update_label()
        self.winner_dialog_shown = False

    def update_team_names(self, _event=None):
        if self.is_solo_mode() or self.is_cutthroat_mode():
            return
        team1_name = self.team1_name_var.get().strip() or "Team 1"
        team2_name = self.team2_name_var.get().strip() or "Team 2"
        self.team1_name_var.set(team1_name)
        self.team2_name_var.set(team2_name)
        self.game.set_team_name(0, team1_name)
        self.game.set_team_name(1, team2_name)
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

        for dropdown in [self.dropdown_1a, self.dropdown_1b, self.dropdown_2a, self.dropdown_2b, self.dropdown_3a]:
            dropdown["values"] = self.player_options
        update_app_config(CONFIG_FILE, player_options=self.player_options)

    def draw_scoreboard(self):
        if self.is_cutthroat_mode():
            self.draw_scoreboard_cutthroat()
        elif self.is_solo_mode():
            self.draw_scoreboard_solo()
        else:
            self.draw_scoreboard_teams()

    def draw_scoreboard_cutthroat(self):
        c = self.score_canvas
        c.delete("all")

        size_x = max(int(c.winfo_width()), int(float(c["width"])))
        row_height = 68
        start_y = 90
        players = self.game.players
        n = len(players)
        col_width = size_x / n
        current_idx = self.game.current_player

        c.create_rectangle(
            current_idx * col_width, 0, (current_idx + 1) * col_width, 600,
            fill=SCOREBOARD_HIGHLIGHT, outline=SCOREBOARD_HIGHLIGHT,
        )

        for i, player in enumerate(players):
            center_x = col_width * (i + 0.5)
            c.create_text(center_x, 30, text=player.name, font=("Arial", 26, "bold"))
            if i > 0:
                c.create_line(col_width * i, 0, col_width * i, 600, fill="white", width=2)
        c.create_line(0, 60, size_x, 60, fill="white", width=2)

        for i, num in enumerate(CRICKET_NUMBERS):
            row_top = start_y + i * row_height
            label_y = row_top - 16
            marks_y = row_top + 4
            against_y = row_top + 26
            c.create_line(0, row_top + row_height / 2, size_x, row_top + row_height / 2, fill="white", width=2, dash=(4, 4))
            c.create_text(size_x / 2, label_y, text="Bull" if num == 25 else str(num), font=("Arial", 20, "bold"))
            for j, player in enumerate(players):
                center_x = col_width * (j + 0.5)
                hits = player.cricket_display[num] + player.cricket_tallies[num]
                c.create_text(
                    center_x,
                    marks_y,
                    text=cricket_marks(hits),
                    font=("Arial", 24),
                    fill="darkgray" if player.cricket_closed[num] else "white",
                )
                against_marks = cricket_marks(player.hits_against[num])
                if against_marks:
                    c.create_text(
                        center_x,
                        against_y,
                        text=against_marks,
                        font=("Arial", 12, "bold"),
                        fill="white",
                    )

        y = start_y + len(CRICKET_NUMBERS) * row_height
        c.create_line(0, y - row_height / 2, size_x, y - row_height / 2, fill="white", width=2)
        c.create_text(size_x / 2, y - 16, text="Pts", font=("Arial", 20, "bold"))
        for i, player in enumerate(players):
            center_x = col_width * (i + 0.5)
            c.create_text(center_x, y + 12, text=str(player.score), font=("Arial", 26, "bold"))

    def draw_scoreboard_teams(self):
        c = self.score_canvas
        c.delete("all")

        size_x = max(int(c.winfo_width()), int(float(c["width"])))
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

        size_x = max(int(c.winfo_width()), int(float(c["width"])))
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
        if self.is_cutthroat_mode():
            self.draw_infoboard_cutthroat()
        elif self.is_solo_mode():
            self.draw_infoboard_solo()
        else:
            self.draw_infoboard_teams()

    def draw_infoboard_cutthroat(self):
        c = self.info_canvas
        c.delete("all")
        width, _, panel_height, pfp_size, box_height = self.infoboard_layout()
        canvas_height = panel_height * 2
        panel_width = width / 3

        panel_player_list = self.game.rotated_turn_order()
        turn_summary = self.infoboard_turn_summary
        current_name = turn_summary["focus_player"]
        current_hits = turn_summary["players"][current_name]["current_hits"]

        for i, player in enumerate(panel_player_list):
            x_left = i * panel_width
            x_center = x_left + panel_width / 2
            if i > 0:
                c.create_line(x_left, 0, x_left, canvas_height, fill="black", width=2)

            is_focus = player.name == current_name
            c.create_text(x_center, 14, text=player.name, font=("Arial", 20, "bold"), fill=self.player_color(player))

            image = self.load_player_image(player, pfp_size)
            setattr(self.root, f"ct_image{i}", image)
            c.create_image(x_center, 24 + pfp_size / 2, image=image)

            hits_y = 44 + pfp_size
            hits = current_hits if is_focus else self.panel_turn_hits(player, turn_summary)
            mark_sum = self.panel_mark_sum(player, turn_summary)
            for idx in range(3):
                slot_x = x_left + panel_width / 4 * (idx + 1)
                c.create_text(
                    slot_x,
                    hits_y,
                    text=hits[idx] if idx < len(hits) else "-",
                    font=("Arial", 20, "bold") if idx == len(hits) - 1 else ("Arial", 20),
                    fill="black",
                )
            c.create_text(x_center, hits_y + box_height / 2, text=f"{mark_sum}M", font=("Arial", 14), fill="black")

        if turn_summary["next_player_flag"]:
            next_player = self.game.active_player()
            c.create_text(
                width / 2,
                canvas_height - 12,
                text=f"Next: {next_player.name}",
                font=("Arial", 16, "bold"),
                fill=self.player_color(next_player),
            )

    def infoboard_layout(self):
        width = 600
        panel_width = int(width / 3)
        # info_canvas is 2 stacked panels tall; size them to whatever room
        # this screen's height actually leaves below the board (was
        # hardcoded for one exact MacBook Air width before).
        panel_height = max(140, int((self.window_height - 604) / 2))
        pfp_size = max(80, int(panel_height * 100 / 174))
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
        turn_summary = self.infoboard_turn_summary
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
            c.create_text(10, 140, anchor="w", text=f"Next player: {next_player.name}", font=("Arial", 30, "bold"), fill=self.player_color(next_player))
            c.create_text(10, 140, anchor="w", text="Next player:", font=("Arial", 30, "bold"), fill="black")
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
        turn_summary = self.infoboard_turn_summary
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

    def draw_recboard(self):
        c = self.rec_canvas
        c.delete("all")

        if self.is_cutthroat_mode():
            c.create_text(
                227, 49,
                anchor="center",
                text="Cutthroat — close all sevens with the lowest score to win",
                font=("Arial", 16, "bold"),
                fill="gray70",
            )
            return

        size_x = max(int(c.winfo_width()), int(float(c["width"])))
        size_y = 98
        rec_size_x = 180
        rec_size_y = 60

        c.create_line(size_x / 2, 10, size_x / 2, size_y - 10, fill="gray55", width=2)

        for side in (0, 1):
            center_x = size_x * (1 + 2 * side) / 4

            if not self.bull_finish_available(side):
                c.create_text(
                    center_x,
                    size_y / 2 + 6,
                    anchor="center",
                    text="",
                    font=("Arial", 22, "bold"),
                    fill="white",
                )
                continue

            bulls_left = self.bulls_left_to_win(side)
            status_text = "1 bull needed" if bulls_left == 1 else f"{bulls_left} bulls needed"

            c.create_rectangle(
                center_x - rec_size_x / 2,
                size_y / 2 - rec_size_y / 2 + 8,
                center_x + rec_size_x / 2,
                size_y / 2 + rec_size_y / 2 + 8,
                fill=REC_FILL_RED,
                outline=REC_FILL_RED,
            )
            c.create_text(
                center_x,
                size_y / 2 + rec_size_y / 4 + 8,
                anchor="s",
                text=status_text,
                font=("Arial", 24, "bold"),
                fill="white",
            )

    def draw_zoomboard(self, x, y):
        c = self.canvas_zoom
        c.delete("all")

        zoom_factor = 3
        line_size = 50
        canvas_size = max(int(c.winfo_width()), int(float(c["width"])))
        img = self.zoom_source_img.copy()
        img = img.crop((int(x - 300 / zoom_factor), int(y - 300 / zoom_factor), int(x + 300 / zoom_factor), int(y + 300 / zoom_factor)))
        img = img.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)
        self.zoom_img = ImageTk.PhotoImage(img)
        c.create_image(0, 0, anchor=tk.NW, image=self.zoom_img)

        hist = self.dart_history[::-1]
        recent_hist = hist[:6]
        if hist:
            current_player = hist[0]["player"]
            side_points = {}
            n_players = 0
            for hh, hit in enumerate(recent_hist):
                if hit["player"] != current_player:
                    n_players += 1
                    current_player = hit["player"]
                if n_players > 1:
                    continue
                xs, ys = side_points.setdefault(hit["team"], ([], []))
                xs.append(hit["x"])
                ys.append(hit["y"])
                if hh == 5:
                    side_points[hit["team"]] = ([], [])

            for side, (x_vals, y_vals) in side_points.items():
                color = self.side_color(side)
                for nn in range(len(x_vals)):
                    x_dot = (x_vals[nn] - x) / 600 * canvas_size * zoom_factor + canvas_size / 2
                    y_dot = (y_vals[nn] - y) / 600 * canvas_size * zoom_factor + canvas_size / 2
                    c.create_oval(x_dot - 5, y_dot - 5, x_dot + 5, y_dot + 5, fill=color, outline="")

        active_color = self.player_color(self.game.active_player())
        c.create_line(canvas_size / 2 - line_size / 2, canvas_size / 2, canvas_size / 2 + line_size / 2, canvas_size / 2, width=4, fill=active_color)
        c.create_line(canvas_size / 2, canvas_size / 2 - line_size / 2, canvas_size / 2, canvas_size / 2 + line_size / 2, width=4, fill=active_color)
        number, mult = interpret_click(x, y)
        miss_zone = classify_miss_zone(x, y)
        if miss_zone["bounce_out"]:
            hover_label = "BO"
        elif miss_zone["offboard"]:
            hover_label = "OB"
        else:
            hover_label = format_hit_label(number, mult)
        c.create_text(canvas_size / 2 + 75, canvas_size / 2, text=hover_label, fill=active_color, font=("Arial", 40, "bold"))

    def draw_statsboard(self):
        c = self.stats_canvas
        c.delete("all")

        width = max(int(c.winfo_width()), int(float(c["width"])))
        height = max(int(c.winfo_height()), int(float(c["height"])))
        if width <= 24 or height <= 24:
            return

        players = self.stats_cache.get("players", [])
        teams = self.stats_cache.get("teams", [])
        distribution = self.stats_cache.get("distribution", {})
        player_progression = self.stats_cache.get("player_progression", {})
        grouping_progression = self.stats_cache.get("grouping_progression", {})
        bull_accuracy_progression = self.stats_cache.get("bull_accuracy_progression", {})
        player_colors = self.stats_cache.get("player_colors", {})
        active_player = self.stats_cache.get("active_player", "")
        surface_text = self.contrast_text_color(c.cget("bg"))
        current_view = self.stats_view_var.get()
        axis_limits = self.stats_cache.get("plot_limits", {"max_x": 1, "max_marks": 5, "max_points": 10})
        bg_hex = self.tk_color_to_hex(c.cget("bg"))

        outer_pad = 10
        gutter = 8
        n_cols = max(1, len(teams))
        col_width = max(1, (width - outer_pad * 2 - gutter * (n_cols - 1)) / n_cols)
        # Inline stat rows ("DCT 2  M 2  MPR 3.00  HIT 0%") are sized for a
        # ~210px-wide card; narrower cards (more players/columns, smaller
        # screens) shrink the stat font so the row keeps fitting instead of
        # overflowing off the card.
        stat_scale = max(0.6, min(1.0, col_width / 210))
        col_lefts = [outer_pad + i * (col_width + gutter) for i in range(n_cols)]
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
            team_color = self.side_color(side)
            team_fill = [STATS_PANEL, STATS_PANEL_ALT, STATS_PANEL_ALT2][side % 3]
            team_text = self.contrast_text_color(team_fill)

            if self.is_solo_mode() or self.is_cutthroat_mode():
                y = top_y
            else:
                c.create_rectangle(left, top_y, right, top_y + team_box_height, fill=team_fill, outline="")
                c.create_text(center_x, top_y + 7, anchor="n", text=team["label"], font=("Arial", 14, "bold"), fill=team_color)
                self.draw_inline_stats(
                    c,
                    left + 8,
                    top_y + 24,
                    [
                        ("M", team["marks"]),
                        ("MPR", f"{team['mpr']:.2f}"),
                        ("HIT", f"{team['hit_rate']:.0f}%"),
                        ("OB", team["offboard"]),
                        ("D", team["doubles"]),
                        ("T", team["triples"]),
                    ],
                    ("Arial", max(7, round(10 * stat_scale)), "bold"),
                    ("Arial", max(7, round(10 * stat_scale))),
                    color=team_text,
                    gap=round(10 * stat_scale),
                )
                y = top_y + team_box_height + 3

            for player in team_players:
                c.create_rectangle(left, y, right, y + player_box_height, fill=STATS_BG, outline="")
                player_text = self.contrast_text_color(STATS_BG)
                c.create_text(
                    left + 8,
                    y + 7,
                    anchor="nw",
                    text=player["name"],
                    font=("Arial", 12, "bold"),
                    fill=player_colors.get(player["name"], team_color),
                )
                if player["name"] == active_player:
                    badge_w = 80
                    c.create_rectangle(right - badge_w-2, y + 7, right - 12, y + 21, fill=SCOREBOARD_HIGHLIGHT, outline="")
                    c.create_text(right - badge_w / 2 - 8, y + 14, text="THROWING", font=("Arial", 8, "bold"), fill="white")
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 24,
                    [
                        ("DCT", player["darts"]),
                        ("M", player["marks"]),
                        ("MPR", f"{player['mpr']:.2f}"),
                        ("HIT", f"{player['hit_rate']:.0f}%"),
                    ],
                    ("Arial", max(7, round(9 * stat_scale)), "bold"),
                    ("Arial", max(7, round(9 * stat_scale))),
                    color=player_text,
                    gap=round(10 * stat_scale),
                )
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 39,
                    [
                        ("OB", player["offboard"]),
                        ("D", player["doubles"]),
                        ("T", player["triples"]),
                        ("PTS", player["points"]),
                        ("AGI", f"{player['previous_grouping']:.1f}"),
                    ],
                    ("Arial", max(7, round(9 * stat_scale)), "bold"),
                    ("Arial", max(7, round(9 * stat_scale))),
                    color=player_text,
                    gap=round(10 * stat_scale),
                )
                y += player_box_height + player_gap

            c.create_text(left, y + section_gap, anchor="nw", text=current_view, font=("Arial", 12, "bold"), fill=surface_text)
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
                self.stats_board_photos[side] = self.render_cricket_progress_plot(
                    board_size,
                    [player["name"] for player in team_players],
                    player_progression,
                    player_colors,
                    surface_text,
                    bg_hex,
                    axis_limits,
                )
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[side])
            else:
                self.stats_board_photos[side] = self.render_cricket_grouping_plot(
                    board_size,
                    [player["name"] for player in team_players],
                    grouping_progression,
                    bull_accuracy_progression,
                    player_colors,
                    surface_text,
                    bg_hex,
                )
                c.create_image(left, board_y, anchor=tk.NW, image=self.stats_board_photos[side])

if __name__ == "__main__":
    root = tk.Tk()
    app = DartsApp(root)
    root.mainloop()
