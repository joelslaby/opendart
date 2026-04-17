import tkinter as tk
from PIL import Image, ImageTk
from tkinter import simpledialog, ttk
import os
from dart_engine.params_cricket_1x1 import Hit, CricketGame
from dart_engine.helpers_cricket_1x1 import get_game_marks_complete, cricket_marks
from dart_engine.helpers_general import interpret_click, swap_players_history, swap_teams_history, get_screen_size_tkinter
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
from datetime import datetime

# -------------------------
# Constants
# -------------------------

# order clockwise starting from top
BOARD_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
               3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
CRICKET_NUMBERS = [20,19,18,17,16,15,25]
CONFIG_FILE = "dart_engine/config.json"
SAVE_FILE = "darts_save.json"
T1_COLOR = "#6a83ff"
T2_COLOR = "#ec6d00"
RECBOARD_BG = "#323232"
SCOREBOARD_BG = "darkolivegreen"
INFOBOARD_BG = "white"
SCOREBOARD_HIGHLIGHT = "olivedrab"

# -------------------------
# GUI
# -------------------------

class DartsApp:

    def __init__(self, root):

        self.root = root
        root.title("Cricket Darts")
        root.attributes('-fullscreen', True)
        x = root.winfo_width()
        y = root.winfo_height()

        self.game = CricketGame()

        self.folder_path, self.player_options = load_app_config(CONFIG_FILE)

        # Set the StringVar so Entry shows it
        self.folder_path_var = tk.StringVar(value=self.folder_path if self.folder_path is not None else "Save directory not set")

        img = Image.open("dartboard_images/dartboard_accurate.png")
        self.size = 600
        img = img.resize((self.size, self.size))

        self.board_img = ImageTk.PhotoImage(img)

        self.canvas = tk.Canvas(root, width=self.size, height=self.size)
        self.canvas.pack()
        
        self.canvas_zoom = tk.Canvas(root, width=x/2-self.size/2-2, height=x/2-self.size/2-2, bg="white")
        self.canvas_zoom.place(x=x/2+self.size/2-3, y=0)

        self.canvas.create_image(0,0,anchor=tk.NW,image=self.board_img)

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)

        self.zoom_label_canvas = tk.Canvas(root, width=100, height=60, bg=RECBOARD_BG)
        self.zoom_label_canvas.place(x=(x-self.size)*3/4+self.size, y=x/2-self.size/2+40,anchor=tk.CENTER)

        self.score_canvas = tk.Canvas(root, width=x/2-self.size/2-2, height=600-2, bg=SCOREBOARD_BG)
        self.score_canvas.place(x=0, y=0)

        self.info_canvas = tk.Canvas(root, width=self.size-7, height=y-600-4, bg=INFOBOARD_BG)
        self.info_canvas.place(x=x/2-self.size/2+1, y=600)

        btn_frame1 = tk.Frame(root)
        btn_frame1.place(x=10, y=630)

        tk.Button(btn_frame1,text="Undo",font=("Arial",30),command=self.undo).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Save",font=("Arial",30),command=self.save).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Load",font=("Arial",30),command=self.load).pack(side=tk.LEFT)
        tk.Button(btn_frame1,text="Reset",font=("Arial",30),command=self.reset).pack(side=tk.LEFT)

        btn_frame2 = tk.Frame(root)
        btn_frame2.place(x=5, y=680)
        tk.Button(btn_frame2,text="Save Setup...",font=("Arial",30),command=self.save_setup).pack(side=tk.LEFT)
        tk.Button(btn_frame2,text="Save As...",font=("Arial",30),command=self.save_as).pack(side=tk.RIGHT)
        
        btn_frame3 = tk.Frame(root)
        btn_frame3.place(x=10, y=730)
        tk.Entry(
            btn_frame3,
            textvariable=self.folder_path_var,
            font=("Arial",16),
            width=40,
        ).pack(side=tk.TOP, pady=10)

        self.team1a_player_var = tk.StringVar(value=self.player_options[0])
        self.team1b_player_var = tk.StringVar(value=self.player_options[1])

        btn_frame4 = tk.Frame(root)
        btn_frame4.place(x=0, y=780)

        tk.Label(btn_frame4, text="Players: ", font=("Arial",20)).pack(side=tk.LEFT, padx=5)
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
        tk.Button(btn_frame4,text="swap",font=("Arial",20),command=self.swap_players).pack(side=tk.LEFT)

        btn_frame6 = tk.Frame(root)
        btn_frame6.place(x=0, y=855)
        tk.Button(btn_frame6,text="Add Player",font=("Arial",20),command=self.add_player).pack(side=tk.LEFT)

        # store markers for current turn (both teams)
        self.dart_markers_0 = []
        self.dart_markers_1 = []

        # store dart history for dataset
        self.dart_history = []

        self.update_label()

    def update_cursor(self, event):
        x = event.x
        y = event.y
        self.draw_zoomboard(x,y)

    def click(self,event):

        number, mult = interpret_click(event.x,event.y)

        if number is None:
            return

        # draw red dot
        if self.game.current_player == 0:
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
            "x": event.x,
            "y": event.y,
            "number": number,
            "multiplier": mult
        })

        self.game.register_hit(Hit(number,mult, (event.x, event.y)))

        # reset board after 3 darts
        if self.game.darts_in_turn == 0:
            self.clear_team_darts()

        self.update_label()

        self.draw_zoomboard(event.x,event.y)

    def update_label(self):
        self.draw_infoboard()
        self.draw_scoreboard()

    def draw_current_dart_marker(self, x, y):
        marker_list = self.dart_markers_0 if self.game.current_player == 0 else self.dart_markers_1
        color = T1_COLOR if self.game.current_player == 0 else T2_COLOR
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
        replay_dart_history(
            self.dart_history,
            reset_game=self.game.reset,
            clear_all_markers=self.clear_all_darts,
            draw_marker=lambda hit: self.draw_current_dart_marker(hit["x"], hit["y"]),
            register_hit=self.register_history_hit,
            clear_turn_markers=self.clear_team_darts,
            is_turn_complete=lambda: self.game.darts_in_turn == 0,
        )
        self.update_label()

    def player_color(self, player):
        return T1_COLOR if self.game.team_index_for_player(player) == 0 else T2_COLOR

    def sync_player_vars_from_game(self):
        self.team1a_player_var.set(self.game.players[0].name)
        self.team1b_player_var.set(self.game.players[1].name)

    def get_player_mark_history(self, player):
        return get_game_marks_complete(self.dart_history, self.game.players, player)

    def load_player_image(self, player, size):
        original_image = Image.open(get_profile_pic_path(player.name))
        resized_image = original_image.resize((size, size))
        return ImageTk.PhotoImage(resized_image)

    def clear_team_darts(self):
        
        if self.game.current_player == 0:
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

        self.filename = f"cricket_{self.game.players[0].name}_vs_{self.game.players[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

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
        player_order = infer_player_turn_order(self.dart_history, 2)

        if player_order:
            self.team1a_player_var.set(player_order[0])
        if len(player_order) > 1:
            self.team1b_player_var.set(player_order[1])

        for player in player_order:
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
        self.update_label()

    def swap_players(self):
        self.game.swap_players()
        # self.dart_history = swap_players_history(self.dart_history,0) # TODO: fix swap player history when game started???
        self.sync_player_vars_from_game()
        self.update_label()

    def update_players(self, player):
        self.game.set_player_names([self.team1a_player_var.get(), self.team1b_player_var.get()])
        self.update_label()

    def add_player(self, dialog_popup=True, name=None):
        if dialog_popup:
            name = simpledialog.askstring("Add Player", "Enter player name:")

        if not add_player_option(self.player_options, name):
            return

        self.dropdown_1a['values'] = self.player_options
        self.dropdown_1b['values'] = self.player_options
        update_app_config(CONFIG_FILE, player_options=self.player_options)

    def draw_scoreboard(self):

        c = self.score_canvas
        c.delete("all")

        size_x = 454
        mid_width = 80
        row_height = 68
        start_y = 90
        highlight_width = 140

        current_player_idx = self.game.current_player
        players = self.game.players

        # Highlight current team
        c.create_rectangle(
            size_x*(1 + 2*current_player_idx)/4-highlight_width/2-mid_width/4 + mid_width*current_player_idx/2,
            0,
            size_x*(1 + 2*current_player_idx)/4+highlight_width/2-mid_width/4 + mid_width*current_player_idx/2,
            600,
            fill=SCOREBOARD_HIGHLIGHT,
            outline=SCOREBOARD_HIGHLIGHT
        )

        # Player labels

        c.create_text(size_x*1/4-mid_width/4,30,text=players[0].name,font=("Arial",40,"bold"))
        c.create_text(size_x*3/4+mid_width/4,30,text=players[1].name,font=("Arial",40,"bold"))

        c.create_line(0, 60, size_x, 60, fill="white", width=2)
        c.create_line(size_x/2-mid_width/2, 0, size_x/2-mid_width/2, 600, fill="white", width=2)
        c.create_line(size_x/2+mid_width/2, 0, size_x/2+mid_width/2, 600, fill="white", width=2)
        

        # Header row (numbers)
        for i,num in enumerate(CRICKET_NUMBERS):

            y = start_y + i*row_height
            c.create_line(0, y + row_height/2, size_x, y + row_height/2, fill="white", width=2, dash=(4, 4))

            c.create_text(
                size_x/2,
                y,
                text="Bull" if num == 25 else str(num),
                font=("Arial",30,"bold")
            )
        
        y = start_y + (i+1)*row_height
        
        c.create_line(0, y - row_height/2, size_x, y - row_height/2, fill="white", width=2)
        c.create_text(
            size_x/2,
            y,
            text="Pts",
            font=("Arial",30,"bold")
        )

        # Player 0 marks

        for i,num in enumerate(CRICKET_NUMBERS):

            hits = players[0].cricket_display[num] + players[0].cricket_tallies[num]

            # hits = max(p.hits[num] for p in self.game.teams[0].players)
            # hits = self.team.cricket_display[num]

            y = start_y + i*row_height

            c.create_text(
                size_x*1/4-mid_width/4,
                y,
                text=cricket_marks(hits),
                font=("Arial",30),
                fill="darkgray" if players[0].cricket_closed[num] and players[1].cricket_closed[num] else "white"
            )

        # Player 1 marks

        for i,num in enumerate(CRICKET_NUMBERS):

            hits = players[1].cricket_display[num] + players[1].cricket_tallies[num]

            y = start_y + i*row_height

            c.create_text(
                size_x*3/4+mid_width/4,
                y,
                text=cricket_marks(hits),
                font=("Arial",30),
                fill="darkgray" if players[0].cricket_closed[num] and players[1].cricket_closed[num] else "white"
            )

        # Score column

        y = start_y + (i+1)*row_height

        c.create_text(
            size_x*1/4-mid_width/4,
            y,
            text=str(players[0].score),
            font=("Arial",30,"bold")
        )

        c.create_text(
            size_x*3/4+mid_width/4,
            y,
            text=str(players[1].score),
            font=("Arial",30,"bold")
        )

    def draw_infoboard(self):
        c = self.info_canvas
        c.delete("all")

        width = 600
        panel_width = int((width)/3)
        screen_width, screen_height = get_screen_size_tkinter()
        if screen_width == 1470:
            panel_height = 162 #174
            pfp_size = 98 #100
        elif screen_width == 1512:
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

        player_list = self.game.rotated_turn_order()
        turn_summary = build_player_turn_summary(
            self.dart_history,
            player_list,
            self.game.active_player().name,
        )
        player_list = self.game.rotated_turn_order(turn_summary["focus_player"])
        turn_summary = build_player_turn_summary(
            self.dart_history,
            player_list,
            self.game.active_player().name,
        )
        current_name = turn_summary["focus_player"]
        p0_current_hits = turn_summary["players"][player_list[0].name]["current_hits"]
        p0_hits = turn_summary["players"][player_list[0].name]["previous_hits"]
        p1_hits = turn_summary["players"][player_list[1].name]["previous_hits"]
        p0_hit_sum = self.get_player_mark_history(player_list[0])[-1]
        p1_hit_sum = self.get_player_mark_history(player_list[1])[-1]

        # Big info panel
        c.create_text(
            10,
            20,
            anchor="w",
            text=current_name,
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
                140,
                anchor="w",
                text=f"Next player: {next_player.name}",
                font=("Arial",30,"bold"),
                fill=self.player_color(next_player)
            )
            c.create_text(
                10,
                140,
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

        # Profile pictures
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        search_dir = "Profile_Pics"

        image_path = []
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                # Check if the search string is in the filename and it is an image file
                if player_list[0].name in fname and fname.lower().endswith(image_extensions):
                    # Construct the full absolute path
                    full_path = os.path.abspath(os.path.join(root, fname))
                    image_path.append(full_path)

        image0 = self.load_player_image(player_list[0], pfp_size)
        self.root.image0 = image0
        
        c.create_image(
            width/2 + panel_width,
            72,
            image=image0
        )

        # Next player panel
        c.create_text(
            width/2 + panel_width,
            12+panel_height,
            text=player_list[1].name,
            font=("Arial",20,"bold"),
            fill=self.player_color(player_list[1])
        )

        image_path = []
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                # Check if the search string is in the filename and it is an image file
                if player_list[1].name in fname and fname.lower().endswith(image_extensions):
                    # Construct the full absolute path
                    full_path = os.path.abspath(os.path.join(root, fname))
                    image_path.append(full_path)

        image1 = self.load_player_image(player_list[1], pfp_size)
        self.root.image1 = image1
        
        c.create_image(
            width/2 + panel_width,
            72+panel_height,
            image=image1
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
            text=f"{p0_hit_sum}M",
            font=("Arial",20),
            fill="black"
        )

        y_pos = panel_height*2 - box_height
        x_pos = width/2 + panel_width*1/2 - panel_width/8
        for pnl in range(1):
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
                x_shift += panel_width/4
                
            if pnl == 0:
                c.create_text(
                    x_pos + x_shift,
                    y_pos+box_height/2,
                    text=f"{p1_hit_sum}M",
                    font=("Arial",20),
                    fill="black"
                )
            x_pos += panel_width

    def draw_zoomboard(self,x,y):
        c = self.canvas_zoom
        c.delete("all")

        zoom_factor = 3
        line_size = 50
        screen_width, screen_height = get_screen_size_tkinter()
        if screen_width == 1470:
            canvas_size = 460
        elif screen_width == 1512:
            canvas_size = 460
        else:
            canvas_size = 460
        img = Image.open("dartboard_images/dartboard_accurate.png")
        img = img.resize((600, 600))
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
                
                if self.game.team_index_for_player(hit["player"]) == 0:
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

# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DartsApp(root)
root.mainloop()
