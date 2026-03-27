import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog
import json
import os
from dart_engine.params_501 import Hit, Game501
from dart_engine.helpers_501 import get_past_scores
from dart_engine.helpers_general import interpret_click, swap_players_history, swap_teams_history

# -------------------------
# Constants
# -------------------------

# order clockwise starting from top
BOARD_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
               3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
CRICKET_NUMBERS = [20,19,18,17,16,15,25]
SAVE_FILE = "darts_save.json"
T1_COLOR = "dodgerblue"
T2_COLOR = "blueviolet"
SCOREBOARD_BG = "saddlebrown"
INFOBOARD_BG = "white"

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

        print(f"Screen size: {x}x{y}")

        self.game = Game501()

        img = Image.open("dartboard_images/dartboard.png")
        self.size = 600
        img = img.resize((self.size, self.size))

        self.board_img = ImageTk.PhotoImage(img)

        self.canvas = tk.Canvas(root, width=self.size, height=self.size)
        self.canvas.pack()

        self.canvas.create_image(0,0,anchor=tk.NW,image=self.board_img)

        self.cursor_label = tk.Label(root, text="x: 0  y: 0", font=("Arial",10))
        self.cursor_label.pack(anchor="w")

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)

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
        btn_frame2.place(x=50, y=680)
        tk.Button(btn_frame2,text="Swap Teams",font=("Arial",30),command=self.swap_teams).pack(side=tk.TOP)
        tk.Button(btn_frame2,text="Swap Players (Team 1)",font=("Arial",30),command=self.swap_players_team_1).pack(side=tk.TOP)
        tk.Button(btn_frame2,text="Swap Players (Team 2)",font=("Arial",30),command=self.swap_players_team_2).pack(side=tk.TOP)

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

    def click(self,event):

        number, mult = interpret_click(event.x,event.y)

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

        self.game.register_hit(Hit(number,mult, (event.x, event.y)),self.dart_history)

        # reset board after 3 darts
        if self.game.darts_in_turn == 0:
            self.clear_team_darts()

        self.update_label()

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

    def save(self):
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Documents", "*.json"), ("All Files", "*.*")]
        )

    # Check if the user cancelled the dialog
        if not file_path:
            return

        self.game.save()

        data = {
            "dart_history": self.dart_history
        }

        with open(file_path,"w") as f:
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
        self.save()
        self.dart_history = []
        self.game.reset()
        self.clear_all_darts()
        self.update_label()

    def swap_teams(self):
        self.game.teams[0], self.game.teams[1] = self.game.teams[1], self.game.teams[0]
        self.dart_history = swap_teams_history(self.dart_history)
        self.update_label()

    def swap_players_team_1(self):
        self.game.teams[0].players[0], self.game.teams[0].players[1] = self.game.teams[0].players[1], self.game.teams[0].players[0]
        self.dart_history = swap_players_history(self.dart_history,0)
        self.update_label()

    def swap_players_team_2(self):
        self.game.teams[1].players[0], self.game.teams[1].players[1] = self.game.teams[1].players[1], self.game.teams[1].players[0]
        self.dart_history = swap_players_history(self.dart_history,1)
        self.update_label()

    def draw_scoreboard(self):

        c = self.score_canvas
        c.delete("all")

        size_x = 454
        size_y = 600
        row_height = 68
        start_y = 90

        # Team labels

        c.create_text(size_x*1/4,30,text=self.game.teams[0].name,font=("Arial",40,"bold"))
        c.create_text(size_x*3/4,30,text=self.game.teams[1].name,font=("Arial",40,"bold"))

        c.create_text(size_x*1/8,75,text=self.game.teams[0].players[0].name,font=("Arial",20,"bold","underline"))
        c.create_text(size_x*3/8,75,text=self.game.teams[0].players[1].name,font=("Arial",20,"bold","underline"))
        c.create_text(size_x*5/8,75,text=self.game.teams[1].players[0].name,font=("Arial",20,"bold","underline"))
        c.create_text(size_x*7/8,75,text=self.game.teams[1].players[1].name,font=("Arial",20,"bold","underline"))

        c.create_line(0, 60, size_x, 60, fill="white", width=2)
        c.create_line(size_x/2, 0, size_x/2, size_y, fill="white", width=3)

        c.create_line(size_x/4, 60, size_x/4, start_y + (13/2)*row_height, fill="white", width=2)
        c.create_line(size_x*3/4, 60, size_x*3/4, start_y + (13/2)*row_height, fill="white", width=2)
        

        player_scores_0 = get_past_scores(self.dart_history,self.game.teams[0].players[0].name,0)
        player_scores_1 = get_past_scores(self.dart_history,self.game.teams[0].players[1].name,0)
        player_scores_2 = get_past_scores(self.dart_history,self.game.teams[1].players[0].name,1)
        player_scores_3 = get_past_scores(self.dart_history,self.game.teams[1].players[1].name,1)

        for yy, player_score_0 in enumerate(player_scores_0):
            if yy < 13:
                c.create_text(size_x*1/8,75 + (yy+1)*row_height/2,text=str(player_score_0),font=("Arial",20))
        for yy, player_score_1 in enumerate(player_scores_1):
            if yy < 13:
                c.create_text(size_x*3/8,75 + (yy+1)*row_height/2,text=str(player_score_1),font=("Arial",20))
        for yy, player_score_2 in enumerate(player_scores_2):
            if yy < 13:
                c.create_text(size_x*5/8,75 + (yy+1)*row_height/2,text=str(player_score_2),font=("Arial",20))
        for yy, player_score_3 in enumerate(player_scores_3):
            if yy < 13:
                c.create_text(size_x*7/8,75 + (yy+1)*row_height/2,text=str(player_score_3),font=("Arial",20))


        # Score column

        y = start_y + (7)*row_height
        
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
        panel_height = 174
        panel_width = int((width)/3)
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
            next_team = self.game.teams[1].name

        p0_hits = p0_hits[::-1]
        p1_hits = p1_hits[::-1]
        p2_hits = p2_hits[::-1]
        p3_hits = p3_hits[::-1]
        p0_current_hits = p0_current_hits[::-1]

        team_1_flag_0 = player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name]
        team_1_flag_1 = player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name]
        team_1_flag_2 = player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name]
        team_1_flag_3 = player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name]

        p0_hit_sum = get_past_scores(self.dart_history,player_list[0].name,team_1_flag_0)[-1]
        p1_hit_sum = get_past_scores(self.dart_history,player_list[1].name,team_1_flag_1)[-1]
        p2_hit_sum = get_past_scores(self.dart_history,player_list[2].name,team_1_flag_2)[-1]
        p3_hit_sum = get_past_scores(self.dart_history,player_list[3].name,team_1_flag_3)[-1]
        
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
                150,
                anchor="w",
                text=f"Next player: {player_list[0].name}",
                font=("Arial",30,"bold"),
                fill=T1_COLOR if player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
            )
            c.create_text(
                panel_width*2 - 10,
                150,
                anchor="e",
                text=f"{next_team}",
                font=("Arial",30,"bold"),
                fill=T1_COLOR if player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
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
            fill=T1_COLOR if player_list[0].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

        image_path = []
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                # Check if the search string is in the filename and it is an image file
                if player_list[0].name in fname and fname.lower().endswith(image_extensions):
                    # Construct the full absolute path
                    full_path = os.path.abspath(os.path.join(root, fname))
                    image_path.append(full_path)

        original_image = Image.open(image_path[0])
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

        image_path = []
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                # Check if the search string is in the filename and it is an image file
                if player_list[1].name in fname and fname.lower().endswith(image_extensions):
                    # Construct the full absolute path
                    full_path = os.path.abspath(os.path.join(root, fname))
                    image_path.append(full_path)

        original_image = Image.open(image_path[0])
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

        image_path = []
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                # Check if the search string is in the filename and it is an image file
                if player_list[2].name in fname and fname.lower().endswith(image_extensions):
                    # Construct the full absolute path
                    full_path = os.path.abspath(os.path.join(root, fname))
                    image_path.append(full_path)

        original_image = Image.open(image_path[0])
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

        image_path = []
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                # Check if the search string is in the filename and it is an image file
                if player_list[3].name in fname and fname.lower().endswith(image_extensions):
                    # Construct the full absolute path
                    full_path = os.path.abspath(os.path.join(root, fname))
                    image_path.append(full_path)

        original_image = Image.open(image_path[0])
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

# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DartsApp(root)
root.mainloop()