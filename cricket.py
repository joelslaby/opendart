import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter import ttk
import json
import os
from dart_engine.params_cricket import Hit, CricketGame, Player
from dart_engine.helpers_cricket import get_game_marks_complete, cricket_marks
from dart_engine.helpers_general import interpret_click, swap_players_history, swap_teams_history, get_screen_size_tkinter
from datetime import datetime

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

        self.game: CricketGame = CricketGame()

        # Load last folder if it exists
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                self.folder_path = data.get("last_folder", None)
                self.player_options = data.get("player_options", ['Jacob', 'Joel', 'Dustin', 'Ravi'])
        else:
            self.folder_path = None
            self.player_options = ["Jacob", "Joel", "Dustin", "Ravi"]

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

        self.cursor_label = tk.Label(root, text="x: 0  y: 0", font=("Arial",10))
        self.cursor_label.pack(anchor="w")

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)

        self.score_canvas = tk.Canvas(root, width=x/2-self.size/2-2, height=600-2, bg=SCOREBOARD_BG)
        self.score_canvas.place(x=0, y=0)

        self.info_canvas = tk.Canvas(root, width=self.size-7, height=y-600-4, bg=INFOBOARD_BG)
        self.info_canvas.place(x=x/2-self.size/2+1, y=600)

        self.label = tk.Label(root, font=("Arial",14))
        self.label.pack(anchor="se")

        btn_frame1 = tk.Frame(root)
        btn_frame1.place(x=5, y=630)

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
        self.team2a_player_var = tk.StringVar(value=self.player_options[2])
        self.team2b_player_var = tk.StringVar(value=self.player_options[3])

        btn_frame4 = tk.Frame(root)
        btn_frame4.place(x=0, y=780)

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
        btn_frame5.place(x=0, y=820)
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
        btn_frame6.place(x=0, y=855)
        tk.Button(btn_frame6,text="Swap teams",font=("Arial",20),command=self.swap_teams).pack(side=tk.LEFT)
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
        self.cursor_label.config(text=f"x: {x}   y: {y}")
        self.draw_zoomboard(x,y)

    def click(self,event):

        number, mult = interpret_click(event.x,event.y)

        # self.score_label.config(text=f"dart score: {number}, {mult}")

        if number is None:
            return

        # draw red dot
        if self.game.current_team == 0:
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

        self.game.register_hit(Hit(number,mult, (event.x, event.y)))

        # reset board after 3 darts
        if self.game.darts_in_turn == 0:
            self.clear_team_darts()

        self.update_label()

        self.draw_zoomboard(event.x,event.y)

    def update_label(self):

        self.draw_infoboard()
        self.draw_scoreboard()

    def clear_team_darts(self):
        
        if self.game.current_team == 0:
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

        if self.folder_path is not None:
            initialdir = self.folder_path
        else:
            initialdir = os.getcwd()

        self.folder_path = filedialog.askdirectory(
            title="Select a Directory to Save",
            initialdir=initialdir
        )

        # Check if the user cancelled the dialog
        if not self.folder_path:
            return
        
        self.folder_path_var.set(self.folder_path)

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data:dict = json.load(f)
                data.update({"last_folder": self.folder_path})
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        else:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"last_folder": self.folder_path}, f)

    def save(self):

        self.filename = f"cricket_{self.game.teams[0].name}_vs_{self.game.teams[1].name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

        data = {
            "dart_history": self.dart_history
        }

        if self.folder_path is None:
            self.save_as()
            return

        with open(os.path.join(self.folder_path, self.filename),"w") as f:
            json.dump(data,f,indent=2)

    def save_as(self):
        self.file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Documents", "*.json"), ("All Files", "*.*")]
        )

        # Check if the user cancelled the dialog
        if not self.file_path:
            return

        data = {
            "dart_history": self.dart_history
        }

        with open(self.file_path,"w") as f:
            json.dump(data,f,indent=2)


    def load(self):

        file_path = filedialog.askopenfilename(
            title="Select a File",
            initialdir=os.getcwd(), # Start in the current working directory
            filetypes=(
                ("Text files", "*.json"), 
                ("Python files", "*.py"), 
                ("All files", "*.*")
            )
        )

        with open(file_path) as f:
            data = json.load(f)

        self.dart_history = data["dart_history"]

        unique_players = []
        unique_players.append(self.dart_history[0]["player"])
        unique_players.append(self.dart_history[6]["player"])
        unique_players.append(self.dart_history[3]["player"])
        unique_players.append(self.dart_history[9]["player"])

        self.team1a_player_var.set(unique_players[0])
        self.team1b_player_var.set(unique_players[1])
        self.team2a_player_var.set(unique_players[2])
        self.team2b_player_var.set(unique_players[3])

        for player in unique_players:
            if player not in self.player_options:
                self.add_player(dialog_popup=False, name=player)

        self.update_team(None)

        self.game.reset()

        for hit in self.dart_history:
            self.game.register_hit(Hit(hit["number"], hit["multiplier"], (hit["x"], hit["y"])))

        self.update_label()

    def undo(self):

        self.dart_history = self.dart_history[:-1]

        self.game.reset()

        self.clear_all_darts()

        for hit in self.dart_history:
            # draw red dot
            if self.game.current_team == 0:
                dot = self.canvas.create_oval(
                    hit["x"]-5, hit["y"]-5,
                    hit["x"]+5, hit["y"]+5,
                    fill=T1_COLOR, outline=""
                )
                self.dart_markers_0.append(dot)
            else:
                dot = self.canvas.create_oval(
                    hit["x"]-5, hit["y"]-5,
                    hit["x"]+5, hit["y"]+5,
                    fill=T2_COLOR, outline=""
                )
                self.dart_markers_1.append(dot)
            self.game.register_hit(Hit(hit["number"], hit["multiplier"], (hit["x"], hit["y"])))

            if self.game.darts_in_turn == 0:
                self.clear_team_darts()

        self.update_label()

    def reset(self):
        self.save_as()
        self.dart_history = []
        self.game.reset()
        self.clear_all_darts()
        self.update_label()

    def swap_teams(self):
        self.game.teams[0], self.game.teams[1] = self.game.teams[1], self.game.teams[0]
        self.dart_history = swap_teams_history(self.dart_history)
        self.team1a_player_var.set(self.game.teams[0].players[0].name)
        self.team1b_player_var.set(self.game.teams[0].players[1].name)
        self.team2a_player_var.set(self.game.teams[1].players[0].name)
        self.team2b_player_var.set(self.game.teams[1].players[1].name)
        self.update_label()

    def swap_players_team_1(self):
        self.game.teams[0].players[0], self.game.teams[0].players[1] = self.game.teams[0].players[1], self.game.teams[0].players[0]
        self.dart_history = swap_players_history(self.dart_history,0)
        self.team1a_player_var.set(self.game.teams[0].players[0].name)
        self.team1b_player_var.set(self.game.teams[0].players[1].name)
        self.update_label()

    def swap_players_team_2(self):
        self.game.teams[1].players[0], self.game.teams[1].players[1] = self.game.teams[1].players[1], self.game.teams[1].players[0]
        self.dart_history = swap_players_history(self.dart_history,1)
        self.team2a_player_var.set(self.game.teams[1].players[0].name)
        self.team2b_player_var.set(self.game.teams[1].players[1].name)
        self.update_label()

    def update_team(self, player):
        self.game.teams[0].players[0] = Player(self.team1a_player_var.get())
        self.game.teams[0].players[1] = Player(self.team1b_player_var.get())
        self.game.teams[1].players[0] = Player(self.team2a_player_var.get())
        self.game.teams[1].players[1] = Player(self.team2b_player_var.get())
        self.update_label()

    def add_player(self, dialog_popup=True, name=None):
        # Implementation for adding a new player
        if dialog_popup:
            dialog = tk.simpledialog.askstring("Add Player", "Enter player name:")
            if dialog:
                self.player_options.append(dialog)
        elif name:
            self.player_options.append(name)

        self.dropdown_1a['values'] = self.player_options
        self.dropdown_1b['values'] = self.player_options
        self.dropdown_2a['values'] = self.player_options
        self.dropdown_2b['values'] = self.player_options

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data:dict = json.load(f)
                data.update({"player_options": self.player_options})
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        else:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"player_options": self.player_options}, f)

    def draw_scoreboard(self):

        c = self.score_canvas
        c.delete("all")

        size_x = 454
        mid_width = 80
        row_height = 68
        start_y = 90
        highlight_width = 140

        current_team_idx = self.game.current_team

        # Highlight current team
        c.create_rectangle(
            size_x*(1 + 2*current_team_idx)/4-highlight_width/2-mid_width/4 + mid_width*current_team_idx/2,
            0,
            size_x*(1 + 2*current_team_idx)/4+highlight_width/2-mid_width/4 + mid_width*current_team_idx/2,
            600,
            fill=SCOREBOARD_HIGHLIGHT,
            outline=SCOREBOARD_HIGHLIGHT
        )

        # Team labels

        c.create_text(size_x*1/4-mid_width/4,30,text=self.game.teams[0].name,font=("Arial",40,"bold"))
        c.create_text(size_x*3/4+mid_width/4,30,text=self.game.teams[1].name,font=("Arial",40,"bold"))

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

        # Team A marks

        for i,num in enumerate(CRICKET_NUMBERS):

            hits = self.game.teams[0].cricket_display[num] + self.game.teams[0].cricket_tallies[num]

            y = start_y + i*row_height

            c.create_text(
                size_x*1/4-mid_width/4,
                y,
                text=cricket_marks(hits),
                font=("Arial",30),
                fill="darkgray" if self.game.teams[0].cricket_closed[num] and self.game.teams[1].cricket_closed[num] else "white"
            )

        # Team B marks

        for i,num in enumerate(CRICKET_NUMBERS):

            hits = self.game.teams[1].cricket_display[num] + self.game.teams[1].cricket_tallies[num]

            y = start_y + i*row_height

            c.create_text(
                size_x*3/4+mid_width/4,
                y,
                text=cricket_marks(hits),
                font=("Arial",30),
                fill="darkgray" if self.game.teams[0].cricket_closed[num] and self.game.teams[1].cricket_closed[num] else "white"
            )

        # Score column

        y = start_y + (i+1)*row_height

        c.create_text(
            size_x*1/4-mid_width/4,
            y,
            text=str(self.game.teams[0].score),
            font=("Arial",30,"bold")
        )

        c.create_text(
            size_x*3/4+mid_width/4,
            y,
            text=str(self.game.teams[1].score),
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

        g = self.game

        player = g.active_player()

        player0 = self.game.teams[0].players[0]
        player1 = self.game.teams[1].players[0] 
        player2 = self.game.teams[0].players[1]
        player3 = self.game.teams[1].players[1] 

        k = [player0.name, player1.name, player2.name, player3.name].index(player.name)
        arr = [player0.name, player1.name, player2.name, player3.name]
        k = 4 - k
        k %= len(arr)
        player_list = [player0, player1, player2, player3]
        player_list = player_list[-k:] + player_list[:-k]

        hist = self.dart_history[::-1]

        p0_hit_number = 0
        p0_current_hits = []
        p0_hits = []
        p1_hit_number = 0
        p1_hits = []
        p2_hit_number = 0
        p2_hits = []
        p3_hit_number = 0
        p3_hits = []
        current_name = player_list[0].name   
        next_player_flag = False
        for hh,hit in enumerate(hist):
            if hit["player"] == player_list[0].name:
                if p0_hit_number > 2:
                    continue
                if hh > 2:
                    p0_hits.append(f"{hit['number']}") if hit["multiplier"] == 1 else p0_hits.append(f"D{hit['number']}") if hit["multiplier"] == 2 else p0_hits.append(f"T{hit['number']}")
                    p0_hit_number += 1
                else:
                    p0_current_hits.append(f"{hit['number']}") if hit["multiplier"] == 1 else p0_current_hits.append(f"D{hit['number']}") if hit["multiplier"] == 2 else p0_current_hits.append(f"T{hit['number']}")
            elif hit["player"] == player_list[1].name:
                if p1_hit_number > 2:
                    continue
                p1_hits.append(f"{hit['number']}") if hit["multiplier"] == 1 else p1_hits.append(f"D{hit['number']}") if hit["multiplier"] == 2 else p1_hits.append(f"T{hit['number']}")
                p1_hit_number += 1
            elif hit["player"] == player_list[2].name:
                if p2_hit_number > 2:
                    continue
                p2_hits.append(f"{hit['number']}") if hit["multiplier"] == 1 else p2_hits.append(f"D{hit['number']}") if hit["multiplier"] == 2 else p2_hits.append(f"T{hit['number']}")
                p2_hit_number += 1
            elif hit["player"] == player_list[3].name:
                if hh <= 2 and hist[0]["player"] == player_list[3].name:
                    p0_current_hits.append(f"{hit['number']}") if hit["multiplier"] == 1 else p0_current_hits.append(f"D{hit['number']}") if hit["multiplier"] == 2 else p0_current_hits.append(f"T{hit['number']}")
                    current_name = player_list[3].name
                    next_player_flag = True
                elif hist[0]["player"] == player_list[3].name:
                    current_name = player_list[3].name
                    next_player_flag = True
                else:
                    current_name = player_list[0].name   
                    next_player_flag = False
                if p3_hit_number > 2:
                    continue
                p3_hits.append(f"{hit['number']}") if hit["multiplier"] == 1 else p3_hits.append(f"D{hit['number']}") if hit["multiplier"] == 2 else p3_hits.append(f"T{hit['number']}")
                p3_hit_number += 1

        team_1_flag = current_name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name]
        if team_1_flag:
            current_team = self.game.teams[0].name
            next_team = self.game.teams[1].name
        else:
            current_team = self.game.teams[1].name
            next_team = self.game.teams[0].name

        p0_hits = p0_hits[::-1]
        p1_hits = p1_hits[::-1]
        p2_hits = p2_hits[::-1]
        p3_hits = p3_hits[::-1]
        p0_current_hits = p0_current_hits[::-1]

        p0_hit_sum = get_game_marks_complete(self.dart_history,self.game.teams,player_list[0])[-1]
        p1_hit_sum = get_game_marks_complete(self.dart_history,self.game.teams,player_list[1])[-1]
        p2_hit_sum = get_game_marks_complete(self.dart_history,self.game.teams,player_list[2])[-1]
        p3_hit_sum = get_game_marks_complete(self.dart_history,self.game.teams,player_list[3])[-1]
        
        # Profile pictures
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        search_dir = "Profile_Pics"

        # Big info panel
        c.create_text(
            10,
            20,
            anchor="w",
            text=current_name,
            font=("Arial",30,"bold"),
            fill=T1_COLOR if current_name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

        c.create_text(
            panel_width*2 - 10,
            20,
            text=current_team,
            anchor="e",
            font=("Arial",30,"bold"),
            fill=T1_COLOR if current_name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
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

        if next_player_flag:
            c.create_text(
                10,
                140,
                anchor="w",
                text=f"Next player: {player_list[0].name}",
                font=("Arial",30,"bold"),
                fill=T1_COLOR if player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
            )
            c.create_text(
                panel_width*2 - 10,
                140,
                anchor="e",
                text=f"{next_team}",
                font=("Arial",30,"bold"),
                fill=T1_COLOR if player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
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
            fill=T1_COLOR if player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

        def get_profile_pic(player_index):
            for root, _, files in os.walk(search_dir):
                image_path = None
                for fname in files:
                    if player_list[player_index].name in fname and fname.lower().endswith(image_extensions):
                        image_path = os.path.abspath(os.path.join(root, fname))
            if image_path is None:
                image_path = os.path.abspath(os.path.join(root, "default.png"))

            return image_path
        
        original_image = Image.open(get_profile_pic(0))
        resized_image = original_image.resize((pfp_size,pfp_size))
        image0 = ImageTk.PhotoImage(resized_image)
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
            fill=T1_COLOR if player_list[1].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

        original_image = Image.open(get_profile_pic(1))
        resized_image = original_image.resize((pfp_size,pfp_size))
        image1 = ImageTk.PhotoImage(resized_image)
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
            fill=T1_COLOR if player_list[2].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

        original_image = Image.open(get_profile_pic(2))
        resized_image = original_image.resize((pfp_size,pfp_size))
        image2 = ImageTk.PhotoImage(resized_image)
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
            fill=T1_COLOR if player_list[3].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

        original_image = Image.open(get_profile_pic(3))
        resized_image = original_image.resize((pfp_size,pfp_size))
        image3 = ImageTk.PhotoImage(resized_image)
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
            text=f"{p0_hit_sum}M",
            font=("Arial",20),
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
                    text=f"{p1_hit_sum}M",
                    font=("Arial",20),
                    fill="black"
                )
            elif pnl == 1:
                c.create_text(
                    x_pos + x_shift,
                    y_pos+box_height/2,
                    text=f"{p2_hit_sum}M",
                    font=("Arial",20),
                    fill="black"
                )
            elif pnl == 2:
                c.create_text(
                    x_pos + x_shift,
                    y_pos+box_height/2,
                    text=f"{p3_hit_sum}M",
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
        c.create_line(canvas_size/2-line_size/2,canvas_size/2,canvas_size/2+line_size/2,canvas_size/2,width=4,fill=T1_COLOR if self.game.active_player().name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR)
        c.create_line(canvas_size/2,canvas_size/2-line_size/2,canvas_size/2,canvas_size/2+line_size/2,width=4,fill=T1_COLOR if self.game.active_player().name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR)

        number, mult = interpret_click(x,y)
        c.create_text(canvas_size/2+75, canvas_size/2, text=f"T{number}" if mult == 3 else f"D{number}" if mult == 2 else f"{number}", fill=T1_COLOR if self.game.active_player().name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR, font=("Arial",40,"bold"))


# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DartsApp(root)
root.mainloop()