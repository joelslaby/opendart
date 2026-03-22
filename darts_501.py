from dataclasses import dataclass
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog
import json
import math
import os

# -------------------------
# Constants
# -------------------------

# order clockwise starting from top
BOARD_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
               3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
DOUBLE_OUT_NUMBERS = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,50]
SAVE_FILE = "darts_save.json"

# -------------------------
# Hit class
# -------------------------
@dataclass
class Hit:
    zone: int
    multiplier: int = 1
    location: tuple = None

# -------------------------
# Player class
# -------------------------

class Player:
    def __init__(self, name):
        self.name = name
        self.hit_history:list[Hit] = []
        self.points_for = 0
        self.darts_thrown = 0

    def add_hit(self, hit: Hit):
        self.darts_thrown += 1
        self.hit_history.append(hit)
        hit.zone


# -------------------------
# Team class
# -------------------------

class Team:
    def __init__(self, name, p1, p2):
        self.name = name
        self.players = [Player(p1), Player(p2)]
        self.score = 501
    
    def add_hit(self, player: Player, hit: Hit):
        player.add_hit(hit)


# -------------------------
# Game State
# -------------------------

class X01Game:

    def __init__(self):

        self.teams = [
            Team("1236", "Jacob", "Joel"),
            Team("930", "Dustin", "Ravi")
        ]

        self.next_player = 0
        self.current_team = 0
        self.current_player = 0
        self.darts_in_turn = 0

    def active_player(self):
        return self.teams[self.current_team].players[self.current_player]

    def opponent_team(self):
        return self.teams[1 - self.current_team]

    def next_turn(self):

        self.darts_in_turn = 0
        self.next_player += 1
        self.next_player %= 4

        self.current_team = self.next_player % 2
        self.current_player = self.next_player // 2


    def register_hit(self, hit: Hit):

        player = self.active_player()
        team = self.teams[self.current_team]

        team.add_hit(player, hit)

        team.score -= hit.multiplier * hit.zone

        self.darts_in_turn += 1

        if team.score == 0 and hit.multiplier == 2:
            print(f"{team.name} wins!")
        elif team.score <= 0:
            team.score += hit.multiplier * hit.zone
            self.next_turn()
        elif self.darts_in_turn == 3:
            self.next_turn()


    def reset(self):

        self.next_player = 0
        self.current_team = 0
        self.current_player = 0
        self.darts_in_turn = 0

        for team in self.teams:
            team.score = 0

# -------------------------
# Dartboard math
# -------------------------

def interpret_click(x, y):

    cx = 300
    cy = 300
    radius = 225

    dx = x - cx
    dy = y - cy

    dist = math.sqrt(dx*dx + dy*dy)

    # outside board
    if dist > radius:
        return 0, 1

    # angle from center
    angle = math.degrees(math.atan2(dy, dx))

    # convert to 0-360
    angle = (angle + 360) % 360

    # rotate so 0° is at top
    angle = (angle + 90 + 9) % 360

    # each wedge = 18 degrees
    index = int(angle / 18)

    if dist <= 309-300:
        return 25, 2
    elif dist <= 320-300:
        return 25, 1
    else:
        board_numbers = [
            20,1,18,4,13,6,10,15,2,17,
            3,19,7,16,8,11,14,9,12,5
        ]

        if 203 <= dist <= 225:
            mult = 2

        elif 127 <= dist <= 150:
            mult = 3

        else:
            mult = 1

        return board_numbers[index], mult


# -------------------------
# GUI
# -------------------------

class DartsApp:

    def __init__(self, root):

        self.root = root
        root.title("501 Darts")

        self.game = X01Game()

        img = Image.open("dartboard.png")
        self.size = 600
        img = img.resize((self.size, self.size))

        self.board_img = ImageTk.PhotoImage(img)

        self.canvas = tk.Canvas(root, width=self.size, height=self.size)
        self.canvas.pack()

        self.canvas.create_image(0,0,anchor=tk.NW,image=self.board_img)

        self.cursor_label = tk.Label(root, text="x: 0  y: 0", font=("Arial",10))
        self.cursor_label.pack(anchor="w")

        self.score_label = tk.Label(root, text="dart score: 0", font=("Arial",10))
        self.score_label.pack(anchor="center")

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)

        self.score_canvas = tk.Canvas(root, width=600, height=150, bg="black")
        self.score_canvas.pack(pady=0)

        self.label = tk.Label(root, font=("Arial",14))
        self.label.pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack()

        tk.Button(btn_frame,text="Undo",command=self.undo).pack(side=tk.LEFT)
        tk.Button(btn_frame,text="Save",command=self.save).pack(side=tk.LEFT)
        tk.Button(btn_frame,text="Load",command=self.load).pack(side=tk.LEFT)
        tk.Button(btn_frame,text="Swap Teams",command=self.swap_teams).pack(side=tk.LEFT)
        tk.Button(btn_frame,text="Swap Players (Team 1)",command=self.swap_players_team_1).pack(side=tk.LEFT)
        tk.Button(btn_frame,text="Swap Players (Team 2)",command=self.swap_players_team_2).pack(side=tk.LEFT)
        tk.Button(btn_frame,text="Reset",command=self.reset).pack(side=tk.LEFT)

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

        self.score_label.config(text=f"dart score: {number}, {mult}")

        if number is None:
            return

        # draw red dot
        if self.game.current_team == 0:
            dot = self.canvas.create_oval(
                event.x-5, event.y-5,
                event.x+5, event.y+5,
                fill="cyan", outline=""
            )
            self.dart_markers_0.append(dot)
        else:
            dot = self.canvas.create_oval(
                event.x-5, event.y-5,
                event.x+5, event.y+5,
                fill="purple", outline=""
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

    def update_label(self):

        g = self.game

        player = g.active_player()

        team = g.teams[g.current_team]

        player0 = self.game.teams[0].players[0]
        player1 = self.game.teams[1].players[0] 
        player2 = self.game.teams[0].players[1]
        player3 = self.game.teams[1].players[1] 

        k = [player0.name, player1.name, player2.name, player3.name].index(player.name)
        arr = [player0.name, player1.name, player2.name, player3.name]

        k = 4 - k
        k %= len(arr)
        # Concatenate the part after the shift point with the part before it
        upcoming_list = arr[-k:] + arr[:-k]
    
        text = f"""
            Current Team: {team.name}
            Player: {player.name}
            Darts this turn: {g.darts_in_turn}
            Next Players: {upcoming_list[1]}, {upcoming_list[2]}, {upcoming_list[3]}
            """

        self.label.config(text=text)

        self.draw_X01_scoreboard()

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
                    fill="cyan", outline=""
                )
                self.dart_markers_0.append(dot)
            else:
                dot = self.canvas.create_oval(
                    hit["x"]-5, hit["y"]-5,
                    hit["x"]+5, hit["y"]+5,
                    fill="purple", outline=""
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
        self.update_label()

    def swap_players_team_1(self):
        self.game.teams[0].players[0], self.game.teams[0].players[1] = self.game.teams[0].players[1], self.game.teams[0].players[0]
        self.update_label()

    def swap_players_team_2(self):
        self.game.teams[1].players[0], self.game.teams[1].players[1] = self.game.teams[1].players[1], self.game.teams[1].players[0]
        self.update_label()

    def draw_X01_scoreboard(self):

        c = self.score_canvas
        c.delete("all")

        col_width = 60
        start_x = 60
        start_y = 40

        # Score column

        score_x = start_x

        c.create_text(score_x,start_y,text="Score",font=("Arial",14,"bold"))

        c.create_text(
            score_x,
            80,
            text=str(self.game.teams[0].score),
            font=("Arial",20,"bold")
        )

        c.create_text(
            score_x,
            130,
            text=str(self.game.teams[1].score),
            font=("Arial",20,"bold")
        )

        # History columns
        hist_x = start_x + 60
        x_gap = 60

        c.create_text(
            hist_x + 5/2*x_gap,
            20,
            text="Previous Throws",
            font=("Arial",14,"bold")
        )

        hist_length = len(self.dart_history)
        num_history = math.ceil(hist_length/6)
        for ii in range(6):
            c.create_text(hist_x + x_gap * ii,start_y,text=str(ii),font=("Arial",14,"bold"))
            if ii < num_history:
                score_0 = 0
                score_1 = 0 
                if ii == 0:
                    set_idxs = hist_length - num_history*6 + 6
                    for nn in range(set_idxs):
                        if self.dart_history[-nn]["team"] == 0:
                            score_0 += self.dart_history[-nn]["number"] * self.dart_history[-nn]["multiplier"]
                        else:
                            score_1 += self.dart_history[-nn]["number"] * self.dart_history[-nn]["multiplier"]
                else:
                    for nn in range(6):
                        if self.dart_history[-set_idxs-nn]["team"] == 0:
                            score_0 += self.dart_history[-set_idxs-nn]["number"] * self.dart_history[-set_idxs-nn]["multiplier"]
                        else:
                            score_1 += self.dart_history[-set_idxs-nn]["number"] * self.dart_history[-set_idxs-nn]["multiplier"]
                for team in range(2):
                    c.create_text(
                        hist_x + x_gap * ii,
                        80 + team*50,
                        text=f"{score_0 if team == 0 else score_1}",
                        font=("Arial",16)
                    )

        # Double out column
        do_x = start_x + 460
        
        c.create_text(do_x,start_y,text="Double Out",font=("Arial",14,"bold"))

        for team in range(2):
            if self.game.teams[team].score in DOUBLE_OUT_NUMBERS:
                if self.game.teams[team].name == "930":
                    c.create_text(
                        do_x,
                        80 + team*50,
                        text="Miss!",
                        font=("Arial",20,"bold")
                    )
                else:
                    c.create_text(
                        do_x,
                            80 + team*50,
                            text=str(int(self.game.teams[team].score/2)),
                        font=("Arial",20,"bold")
                    )
            else:
                c.create_text(
                    do_x,
                    80 + team*50,
                    text="NO",
                    font=("Arial",20,"bold")
                )
            
            

# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DartsApp(root)
root.mainloop()