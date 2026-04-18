import os
import tkinter as tk
from dart_engine.params_501 import Hit, Game501
from datetime import datetime
from tkinter import simpledialog, ttk

from PIL import Image, ImageTk

from dart_engine.helpers_501 import get_recommended_hits
from dart_engine.helpers_general import interpret_click, swap_players_history, swap_teams_history
from dart_engine.player_ui import build_recent_player_turn_summary, format_hit_label, get_profile_pic_path
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

# -------------------------
# GUI
# -------------------------

class DartsApp:

    def __init__(self, root):

        self.root = root
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
        self.last_replayed_team = None

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
        stats_height = self.screen_height - stats_y - 2
        self.stats_canvas = tk.Canvas(
            root,
            width=right_column_width,
            height=stats_height,
            bg=INFOBOARD_BG,
            highlightthickness=0,
        )
        self.stats_canvas.place(x=right_column_x, y=stats_y)

        btn_frame1 = tk.Frame(root)
        btn_frame1.place(x=5, y=690)

        tk.Button(btn_frame1,text="Undo",font=("Arial",30),command=self.undo).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Save",font=("Arial",30),command=self.save).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Load",font=("Arial",30),command=self.load).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Reset",font=("Arial",30),command=self.reset).pack(side=tk.LEFT)

        btn_frame2 = tk.Frame(root)
        btn_frame2.place(x=5, y=740)
        tk.Button(btn_frame2,text="Save Setup...",font=("Arial",30),command=self.save_setup).pack(side=tk.LEFT)
        tk.Button(btn_frame2,text="Save As...",font=("Arial",30),command=self.save_as).pack(side=tk.RIGHT)

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

        btn_frame4 = tk.Frame(root)
        btn_frame4.place(x=0, y=815)

        tk.Label(btn_frame4, text="Team 1: ", font=("Arial",20)).pack(side=tk.LEFT, padx=5)
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
        self.dropdown_1a.bind("<<ComboboxSelected>>", self.update_team)
        self.dropdown_1b.bind("<<ComboboxSelected>>", self.update_team)
        tk.Button(btn_frame4,text="swap",font=("Arial",20),command=self.swap_players_team_1).pack(side=tk.LEFT)

        btn_frame5 = tk.Frame(root)
        btn_frame5.place(x=0, y=850)
        tk.Label(btn_frame5, text="Team 2: ", font=("Arial",20)).pack(side=tk.LEFT, padx=5)
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
        self.dropdown_2a.bind("<<ComboboxSelected>>", self.update_team)
        self.dropdown_2b.bind("<<ComboboxSelected>>", self.update_team)
        tk.Button(btn_frame5,text="swap",font=("Arial",20),command=self.swap_players_team_2).pack(side=tk.LEFT)

        btn_frame6 = tk.Frame(root)
        btn_frame6.place(x=0, y=890)
        tk.Button(btn_frame6,text="Swap teams",font=("Arial",20),command=self.swap_teams).pack(side=tk.LEFT)
        tk.Button(btn_frame6,text="Add Player",font=("Arial",20),command=self.add_player).pack(side=tk.LEFT)

        # store markers for current turn (both teams)
        self.dart_markers_0 = []
        self.dart_markers_1 = []

        # store dart history for dataset
        self.dart_history = []

        self.refresh_caches()
        self.update_label()

    def update_cursor(self, event):
        self.draw_zoomboard(event.x, event.y)

    def click(self,event):

        number, mult = interpret_click(event.x,event.y)

        if number is None:
            return

        # draw red dot
        throwing_team = self.game.current_team
        if throwing_team == 0:
            dot = self.canvas.create_oval(
                event.x-5, event.y-5,
                event.x+5, event.y+5,
                fill=T1_COLOR, outline=""
            )
            self.dart_markers_0.append(dot)
        else:
            dot = self.canvas.create_oval(
                event.x-5, event.y-5,
                event.x+5, event.y+5,
                fill=T2_COLOR, outline=""
            )
            self.dart_markers_1.append(dot)

        # save dart data
        player = self.game.active_player()

        self.dart_history.append({
            "player": player.name,
            "team": self.game.current_team,
            "x": event.x,
            "y": event.y,
            "number": number,
            "multiplier": mult
        })

        self.game.register_hit(Hit(number,mult, (event.x, event.y)),self.dart_history)

        # reset board after 3 darts
        if self.game.darts_in_turn == 0:
            self.clear_team_darts(throwing_team)

        self.refresh_caches()
        self.update_label()

        self.draw_zoomboard(event.x,event.y)

    def update_label(self):
        self.update_infoboard_turn_summary()
        self.draw_infoboard()
        self.draw_scoreboard()
        self.draw_recboard()
        self.draw_statsboard()

    def draw_current_dart_marker(self, x, y):
        marker_list = self.dart_markers_0 if self.game.current_team == 0 else self.dart_markers_1
        color = T1_COLOR if self.game.current_team == 0 else T2_COLOR
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
        self.last_replayed_team = hit["team"]
        self.game.register_hit(Hit(hit["number"], hit["multiplier"], (hit["x"], hit["y"])))

    def replay_history(self):
        replay_dart_history(
            self.dart_history,
            reset_game=self.game.reset,
            clear_all_markers=self.clear_all_darts,
            draw_marker=lambda hit: self.draw_current_dart_marker(hit["x"], hit["y"]),
            register_hit=self.register_history_hit,
            clear_turn_markers=lambda: self.clear_team_darts(self.last_replayed_team),
            is_turn_complete=lambda: self.game.darts_in_turn == 0,
        )
        self.refresh_caches()
        self.update_label()

    def player_color(self, player):
        return T1_COLOR if self.game.team_index_for_player(player) == 0 else T2_COLOR

    def team_name_for_player(self, player):
        return self.game.team_for_player(player).name

    def stats_players_in_display_order(self):
        return [player for team in self.game.teams for player in team.players]

    def team_player_colors(self, side, count):
        palettes = {
            0: ["#6a83ff", "#2f52d6", "#94a6ff", "#4c66ff"],
            1: ["#ec6d00", "#b24a00", "#ff9b45", "#d85c00"],
        }
        palette = palettes[side]
        return [palette[index % len(palette)] for index in range(max(1, count))]

    def sync_player_vars_from_game(self):
        self.team1a_player_var.set(self.game.teams[0].players[0].name)
        self.team1b_player_var.set(self.game.teams[0].players[1].name)
        self.team2a_player_var.set(self.game.teams[1].players[0].name)
        self.team2b_player_var.set(self.game.teams[1].players[1].name)

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
        team_score = {0: 501, 1: 501}
        team_turn_start = {0: 501, 1: 501}
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

    def update_stats_cache(self):
        players = self.stats_players_in_display_order()
        player_stats = {
            player.name: {
                "name": player.name,
                "side": self.game.team_index_for_player(player),
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "triples": 0,
                "ton_plus": 0,
                "oneforty_plus": 0,
                "oneeighty": 0,
            }
            for player in players
        }
        team_stats = {
            side: {
                "label": self.game.teams[side].name,
                "score": self.game.teams[side].score,
                "darts": 0,
                "scored": 0,
                "bulls": 0,
                "triples": 0,
            }
            for side in (0, 1)
        }

        team_players = {0: [], 1: []}
        for player in players:
            side = self.game.team_index_for_player(player)
            team_players[side].append(player.name)

        player_color_lookup = {}
        for side in (0, 1):
            for name, color in zip(team_players[side], self.team_player_colors(side, len(team_players[side]))):
                player_color_lookup[name] = color

        distribution_points = {0: [], 1: []}
        for hit in self.dart_history:
            player_name = hit["player"]
            side = self.game.team_index_for_player(player_name) if player_name in player_stats else hit.get("team", 0)
            points = hit["multiplier"] * hit["number"]

            if player_name in player_stats:
                player_stats[player_name]["darts"] += 1
                player_stats[player_name]["scored"] += points
                player_stats[player_name]["bulls"] += 1 if hit["number"] == 25 else 0
                player_stats[player_name]["triples"] += 1 if hit["multiplier"] == 3 else 0

            team_stats[side]["darts"] += 1
            team_stats[side]["scored"] += points
            team_stats[side]["bulls"] += 1 if hit["number"] == 25 else 0
            team_stats[side]["triples"] += 1 if hit["multiplier"] == 3 else 0
            distribution_points[side].append(
                {
                    "x": hit["x"],
                    "y": hit["y"],
                    "player": player_name,
                    "color": player_color_lookup.get(player_name, T1_COLOR if side == 0 else T2_COLOR),
                }
            )

        for player_name, stats in player_stats.items():
            turns = self.score_history_cache.get(player_name, [0])
            stats["avg"] = (stats["scored"] * 3 / stats["darts"]) if stats["darts"] else 0.0
            stats["ton_plus"] = sum(1 for score in turns if score >= 50)
            stats["oneforty_plus"] = sum(1 for score in turns if score >= 100)
            stats["oneeighty"] = sum(1 for score in turns if score >= 150)

        for side in (0, 1):
            team_stats[side]["avg"] = (
                team_stats[side]["scored"] * 3 / team_stats[side]["darts"]
                if team_stats[side]["darts"]
                else 0.0
            )

        self.stats_cache = {
            "players": [player_stats[player.name] for player in players],
            "teams": [team_stats[0], team_stats[1]],
            "distribution": distribution_points,
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
        if team_index == 0:
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
        self.dart_markers_0 = []
        for marker in self.dart_markers_1:
            self.canvas.delete(marker)
        self.dart_markers_1 = []

    def save_setup(self):
        folder_path = choose_save_directory(self.folder_path)
        if not folder_path:
            return

        self.folder_path = folder_path
        self.folder_path_var.set(self.folder_path)
        update_app_config(CONFIG_FILE, last_folder=self.folder_path)

    def save(self):

        self.filename = f"501_{self.game.teams[0].name}_vs_{self.game.teams[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

        if self.folder_path is None:
            self.save_as()
            return

        save_dart_history(os.path.join(self.folder_path, self.filename), self.dart_history)

    def save_as(self):
        file_path = ask_history_save_path()
        if not file_path:
            return

        save_dart_history(file_path, self.dart_history)

    def load(self):
        file_path = ask_history_load_path(self.folder_path)
        if not file_path:
            return

        self.dart_history = load_dart_history(file_path)
        turn_order = infer_player_turn_order(self.dart_history, 4)
        team_order = [turn_order[index] for index in (0, 2, 1, 3) if index < len(turn_order)]
        player_vars = [
            self.team1a_player_var,
            self.team1b_player_var,
            self.team2a_player_var,
            self.team2b_player_var,
        ]

        for player_var, player_name in zip(player_vars, team_order):
            player_var.set(player_name)

        for player in turn_order:
            if player not in self.player_options:
                self.add_player(dialog_popup=False, name=player)

        self.update_team(None)
        self.replay_history()

    def undo(self):
        self.dart_history = self.dart_history[:-1]
        self.replay_history()

    def reset(self):
        self.save_as()
        self.dart_history = []
        self.game.reset()
        self.clear_all_darts()
        self.refresh_caches()
        self.update_label()

    def swap_teams(self):
        self.game.swap_teams()
        self.dart_history = swap_teams_history(self.dart_history)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()

    def swap_players_team_1(self):
        self.game.swap_team_players(0)
        self.dart_history = swap_players_history(self.dart_history,0)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()

    def swap_players_team_2(self):
        self.game.swap_team_players(1)
        self.dart_history = swap_players_history(self.dart_history,1)
        self.sync_player_vars_from_game()
        self.refresh_caches()
        self.update_label()

    def update_team(self, player):
        self.game.set_team_player_names(0, [self.team1a_player_var.get(), self.team1b_player_var.get()])
        self.game.set_team_player_names(1, [self.team2a_player_var.get(), self.team2b_player_var.get()])
        self.refresh_caches()
        self.update_label()

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

        c = self.score_canvas
        c.delete("all")

        size_x = 454
        size_y = 600
        row_height = 68
        start_y = 90
        highlight_width = 80

        y = start_y + (7)*row_height

        players = self.game.all_players()
        current_player_idx = next(
            index for index, player in enumerate(players) if player.name == self.game.active_player().name
        )

        # Highlight current player
        c.create_rectangle(
            size_x*(1 + 2*current_player_idx)/8-highlight_width/2,
            60,
            size_x*(1 + 2*current_player_idx)/8+highlight_width/2,
            start_y + (13/2)*row_height,
            fill=SCOREBOARD_HIGHLIGHT,
            outline=SCOREBOARD_HIGHLIGHT
        )

        # Team labels

        c.create_text(size_x*1/4,30,text=self.game.teams[0].name,font=("Arial",40,"bold"))
        c.create_text(size_x*3/4,30,text=self.game.teams[1].name,font=("Arial",40,"bold"))

        player_x_positions = [size_x*1/8, size_x*3/8, size_x*5/8, size_x*7/8]
        for x_pos, player in zip(player_x_positions, players):
            c.create_text(x_pos,75,text=player.name,font=("Arial",20,"bold","underline"))

        c.create_line(0, 60, size_x, 60, fill="white", width=2)
        c.create_line(size_x/2, 0, size_x/2, size_y, fill="white", width=3)

        c.create_line(size_x/4, 60, size_x/4, start_y + (13/2)*row_height, fill="white", width=2)
        c.create_line(size_x*3/4, 60, size_x*3/4, start_y + (13/2)*row_height, fill="white", width=2)
        

        for x_pos, player in zip(player_x_positions, players):
            for yy, player_score in enumerate(self.get_player_score_history(player)):
                if yy < 13:
                    c.create_text(x_pos,75 + (yy+1)*row_height/2,text=str(player_score),font=("Arial",20))


        # Score column
        
        c.create_line(0, y - row_height/2, size_x, y - row_height/2, fill="white", width=2)

        c.create_text(
            size_x*1/4,
            y,
            text=str(self.game.teams[0].score),
            font=("Arial",40,"bold")
        )

        c.create_text(
            size_x*3/4,
            y,
            text=str(self.game.teams[1].score),
            font=("Arial",40,"bold")
        )

    def draw_infoboard(self):
        c = self.info_canvas
        c.delete("all")

        width = 600
        panel_width = int((width)/3)
        if self.screen_width == 1470:
            panel_height = 162 #174
            pfp_size = 98 #100
        elif self.screen_width == 1512:
            panel_height = 174
            pfp_size = 100
        else:
            panel_height = 174
            pfp_size = 100
        box_height = 40

        # Make lines to seperate panels
        c.create_line(int(width/2-panel_width/2), panel_height, int(width/2-panel_width/2), panel_height*2, fill="black", width=3)
        c.create_line(int(width/2+panel_width/2), 0, int(width/2+panel_width/2), panel_height*2, fill="black", width=3)
        c.create_line(0, panel_height, width, panel_height, fill="black", width=3)

        y_pos = panel_height*2 - box_height
        x_pos = width/2 - panel_width*3/2
        for pnl in range(3):
            c.create_line(x_pos, y_pos, x_pos+panel_width, y_pos, fill="black", width=2)
            x_shift = panel_width/4
            for l in range(3):
                c.create_line(x_pos + x_shift, y_pos+box_height, x_pos + x_shift, y_pos, fill="black", width=2)
                x_shift += panel_width/4
            x_pos += panel_width

        y_pos = panel_height - box_height
        x_pos = width/2 + panel_width/2
        c.create_line(x_pos, y_pos, x_pos+panel_width, y_pos, fill="black", width=2)
        x_shift = panel_width/4
        for l in range(3):
            c.create_line(x_pos + x_shift, y_pos+box_height, x_pos + x_shift, y_pos, fill="black", width=2)
            x_shift += panel_width/4
        x_pos += panel_width

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

        # Big info panel
        c.create_text(
            10,
            20,
            anchor="w",
            text=current_name,
            font=("Arial",30,"bold"),
            fill=self.player_color(current_name)
        )

        c.create_text(
            panel_width*2 - 10,
            20,
            text=current_team,
            anchor="e",
            font=("Arial",30,"bold"),
            fill=self.player_color(current_name)
        )

        # Current throws
        c.create_line(panel_width*1/4, 40, panel_width*7/4, 40, fill="black", width=2)
        c.create_line(panel_width*1/4, 120, panel_width*7/4, 120, fill="black", width=2)
        c.create_line(panel_width*1/4, 40, panel_width*1/4, 120, fill="black", width=2)
        c.create_line(panel_width*3/4, 40, panel_width*3/4, 120, fill="black", width=2)
        c.create_line(panel_width*5/4, 40, panel_width*5/4, 120, fill="black", width=2)
        c.create_line(panel_width*7/4, 40, panel_width*7/4, 120, fill="black", width=2)

        c.create_text(
            panel_width*1/2,
            60,
            text=f"1",
            font=("Arial",20,"underline","bold"),
            fill="black"
        )
        c.create_text(
            panel_width,
            60,
            text=f"2",
            font=("Arial",20,"underline","bold"),
            fill="black"
        )
        c.create_text(
            panel_width*3/2,
            60,
            text=f"3",
            font=("Arial",20,"underline","bold"),
            fill="black"
        )

        for ii in range(3):
            c.create_text(
                panel_width/2 + ii*panel_width/2,
                100,
                text=f"{p0_current_hits[ii] if ii < len(p0_current_hits) else '-'}",
                font=("Arial",30,"bold") if ii == len(p0_current_hits)-1 else ("Arial",30),
                fill="black"
            )

        if turn_summary["next_player_flag"]:
            next_player = self.game.active_player()
            c.create_text(
                10,
                150,
                anchor="w",
                text=f"Next player: {next_player.name}",
                font=("Arial",30,"bold"),
                fill=self.player_color(next_player)
            )
            c.create_text(
                panel_width*2 - 10,
                150,
                anchor="e",
                text=self.team_name_for_player(next_player),
                font=("Arial",30,"bold"),
                fill=self.player_color(next_player)
            )
            c.create_text(
                10,
                150,
                anchor="w",
                text=f"Next player:",
                font=("Arial",30,"bold"),
                fill="black"
            )

        # Current player panel
        c.create_text(
            width/2 + panel_width,
            12,
            text=player_list[0].name,
            font=("Arial",20,"bold"),
            fill=self.player_color(player_list[0])
        )
        image0 = self.load_player_image(player_list[0], pfp_size)
        self.root.image0 = image0
        
        c.create_image(
            width/2 + panel_width,
            72,
            image=image0
        )

        # Next player panel
        c.create_text(
            width/2 - panel_width,
            12+panel_height,
            text=player_list[1].name,
            font=("Arial",20,"bold"),
            fill=self.player_color(player_list[1])
        )
        image1 = self.load_player_image(player_list[1], pfp_size)
        self.root.image1 = image1
        
        c.create_image(
            width/2 - panel_width,
            72+panel_height,
            image=image1
        )

        #Next next player panel
        c.create_text(
            width/2,
            12+panel_height,
            text=player_list[2].name,
            font=("Arial",20,"bold"),
            fill=self.player_color(player_list[2])
        )
        image2 = self.load_player_image(player_list[2], pfp_size)
        self.root.image2 = image2
        
        c.create_image(
            width/2,
            72 + panel_height,
            image=image2
        )

        #Next next next player panel
        c.create_text(
            width/2 + panel_width,
            12+panel_height,
            text=player_list[3].name,
            font=("Arial",20,"bold"),
            fill=self.player_color(player_list[3])
        )
        image3 = self.load_player_image(player_list[3], pfp_size)
        self.root.image3 = image3
        
        c.create_image(
            width/2 + panel_width,
            72+panel_height,
            image=image3
        )

        # add text boxes for prior turn hits

        y_pos = panel_height - box_height
        x_pos = width/2 + panel_width/2 - panel_width/8
        x_shift = panel_width/4
        for l in range(3):
            c.create_text(
                x_pos + x_shift,
                y_pos+box_height/2,
                text=p0_hits[l] if l < len(p0_hits) else "-",
                font=("Arial",20),
                fill="black"
            )
            x_shift += panel_width/4
        c.create_text(
            x_pos + x_shift,
            y_pos+box_height/2,
            text=f"{p0_hit_sum}",
            font=("Arial",20,"bold"),
            fill="black"
        )

        y_pos = panel_height*2 - box_height
        x_pos = width/2 - panel_width*3/2 - panel_width/8
        for pnl in range(3):
            x_shift = panel_width/4
            for l in range(3):
                if pnl == 0:
                    c.create_text(
                        x_pos + x_shift,
                        y_pos+box_height/2,
                        text=p1_hits[l] if l < len(p1_hits) else "-",
                        font=("Arial",20),
                        fill="black"
                    )
                elif pnl == 1:
                    c.create_text(
                        x_pos + x_shift,
                        y_pos+box_height/2,
                        text=p2_hits[l] if l < len(p2_hits) else "-",
                        font=("Arial",20),
                        fill="black"
                    )
                elif pnl == 2:
                    c.create_text(
                        x_pos + x_shift,
                        y_pos+box_height/2,
                        text=p3_hits[l] if l < len(p3_hits) else "-",
                        font=("Arial",20),
                        fill="black"
                    )
                x_shift += panel_width/4
                
            if pnl == 0:
                c.create_text(
                    x_pos + x_shift,
                    y_pos+box_height/2,
                    text=f"{p1_hit_sum}",
                    font=("Arial",20,"bold"),
                    fill="black"
                )
            elif pnl == 1:
                c.create_text(
                    x_pos + x_shift,
                    y_pos+box_height/2,
                    text=f"{p2_hit_sum}",
                    font=("Arial",20,"bold"),
                    fill="black"
                )
            elif pnl == 2:
                c.create_text(
                    x_pos + x_shift,
                    y_pos+box_height/2,
                    text=f"{p3_hit_sum}",
                    font=("Arial",20,"bold"),
                    fill="black"
                )
            x_pos += panel_width
    
    def draw_recboard(self):
        c = self.rec_canvas
        c.delete("all")

        size_x = 454
        size_y = 98
        rec_size_x = 100
        rec_size_y = 60

        score = self.game.score_for_player(self.game.active_player())

        hits = get_recommended_hits(self.game.darts_in_turn,score)

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
            current_player = hist[0]["player"]
            x0 = []
            y0 = []
            x1 = []
            y1 = []
            n_players = 0
            for hh,hit in enumerate(recent_hist):
                if hit["player"] != current_player:
                    n_players +=1
                    current_player = hit["player"]
                if n_players > 1:
                    continue
                
                if hit["team"] == 0:
                    x0.append(hit["x"])
                    y0.append(hit["y"])
                    if hh == 5:
                        x0 = []
                        y0 = []
                else:
                    x1.append(hit["x"])
                    y1.append(hit["y"])
                    if hh == 5:
                        x1 = []
                        y1 = []


            for nn in range(len(x0)):
                x_dot = (x0[nn] - x)/600*canvas_size*zoom_factor+canvas_size/2
                y_dot = (y0[nn] - y)/600*canvas_size*zoom_factor+canvas_size/2
                c.create_oval(
                    x_dot-5, y_dot-5,
                    x_dot+5, y_dot+5,
                    fill=T1_COLOR, outline=""
                )
            for nn in range(len(x1)):
                x_dot = (x1[nn] - x)/600*canvas_size*zoom_factor+canvas_size/2
                y_dot = (y1[nn] - y)/600*canvas_size*zoom_factor+canvas_size/2
                c.create_oval(
                    x_dot-5, y_dot-5,
                    x_dot+5, y_dot+5,
                    fill=T2_COLOR, outline=""
                )

        # Center cross
        active_color = self.player_color(self.game.active_player())
        c.create_line(canvas_size/2-line_size/2,canvas_size/2,canvas_size/2+line_size/2,canvas_size/2,width=4,fill=active_color)
        c.create_line(canvas_size/2,canvas_size/2-line_size/2,canvas_size/2,canvas_size/2+line_size/2,width=4,fill=active_color)

        number, mult = interpret_click(x,y)
        c.create_text(canvas_size/2+75, canvas_size/2, text=format_hit_label(number, mult), fill=active_color, font=("Arial",40,"bold"))

    def draw_statsboard(self):
        c = self.stats_canvas
        c.delete("all")

        width = max(int(c.winfo_width()), int(float(c["width"])))
        height = max(int(c.winfo_height()), int(float(c["height"])))
        if width <= 24 or height <= 24:
            return

        players = self.stats_cache.get("players", [])
        teams = self.stats_cache.get("teams", [])
        distribution = self.stats_cache.get("distribution", {0: [], 1: []})
        player_colors = self.stats_cache.get("player_colors", {})
        active_player = self.stats_cache.get("active_player", "")

        outer_pad = 10
        gutter = 8
        col_width = max(1, (width - outer_pad * 2 - gutter) / 2)
        col_lefts = [outer_pad, outer_pad + col_width + gutter]
        title_y = 10

        c.create_text(outer_pad, title_y, anchor="nw", text="Live Stats", font=("Arial", 19, "bold"), fill=TEXT_DARK)

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
            team_players = [player for player in players if player["side"] == side]
            team_color = T1_COLOR if side == 0 else T2_COLOR
            team_fill = STATS_PANEL if side == 0 else STATS_PANEL_ALT

            c.create_rectangle(left, top_y, right, top_y + team_box_height, fill=team_fill, outline="")
            c.create_text(left + 8, top_y + 7, anchor="nw", text=team["label"], font=("Arial", 14, "bold"), fill=team_color)
            self.draw_inline_stats(
                c,
                left + 8,
                top_y + 24,
                [
                    ("Avg", f"{team['avg']:.2f}"),
                    ("Bull", team["bulls"]),
                    ("T", team["triples"]),
                ],
                ("Arial", 10, "bold"),
                ("Arial", 10),
            )

            y = top_y + team_box_height + 3
            for player in team_players:
                c.create_rectangle(left, y, right, y + player_box_height, fill=STATS_BG, outline="")
                c.create_text(left + 8, y + 7, anchor="nw", text=player["name"], font=("Arial", 12, "bold"), fill=player_colors.get(player["name"], team_color))
                if player["name"] == active_player:
                    badge_w = 42
                    c.create_rectangle(right - badge_w - 8, y + 7, right - 8, y + 21, fill=SCOREBOARD_HIGHLIGHT, outline="")
                    c.create_text(right - badge_w / 2 - 8, y + 14, text="LIVE", font=("Arial", 8, "bold"), fill="white")
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 24,
                    [
                        ("dt", player["darts"]),
                        ("Pts", player["scored"]),
                        ("Avg", f"{player['avg']:.2f}"),
                    ],
                    ("Arial", 9, "bold"),
                    ("Arial", 9),
                )
                self.draw_inline_stats(
                    c,
                    left + 8,
                    y + 39,
                    [
                        ("50+", player["ton_plus"]),
                        ("100+", player["oneforty_plus"]),
                        ("150+", player["oneeighty"]),
                    ],
                    ("Arial", 9, "bold"),
                    ("Arial", 9),
                )
                y += player_box_height + player_gap

            c.create_text(left, y + section_gap, anchor="nw", text="Shot Map", font=("Arial", 12, "bold"), fill=TEXT_DARK)
            board_y = y + section_gap + board_title_gap
            available_board_height = max(1, height - board_y - board_bottom_pad)
            board_size = int(max(1, min(col_width, available_board_height)))
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
                c.create_text(legend_x + 12, legend_y, anchor="nw", text=player["name"], font=("Arial", 9, "bold"), fill=TEXT_DARK)
                legend_x += max(48, 16 + len(player["name"]) * 7)


# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DartsApp(root)
root.mainloop()
