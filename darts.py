from dataclasses import dataclass
import tkinter as tk
from PIL import Image, ImageTk
import json
import math
import os

# -------------------------
# Constants
# -------------------------

# order clockwise starting from top
BOARD_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
               3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
CRICKET_NUMBERS = [20,19,18,17,16,15,"BULL"]
SAVE_FILE = "darts_save.json"

def cricket_marks(hits):

    if hits == 0:
        return ""

    if hits == 1:
        return "/"

    if hits == 2:
        return "X"

    if hits == 3:
        return "Ⓧ"

    # extra hits
    extra = hits - 3
    return "Ⓧ " + "|" * extra

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

        if hit.zone not in CRICKET_NUMBERS:
            return 0
        else:
            return hit.zone


# -------------------------
# Team class
# -------------------------

class Team:
    def __init__(self, name, p1, p2):
        self.name = name
        self.players = [Player(p1), Player(p2)]
        self.cricket_display = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_tallies = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_closed = {num: False for num in CRICKET_NUMBERS}
        self.score = 0

    def has_closed(self, number):
        if sum(p.hits[number] for p in self.players) >= 3:
            self.cricket_closed[number] = True
        return self.cricket_closed[number]
    
    def add_hit(self, player: Player, hit: Hit):
        
        player.add_hit(hit)
        if player.add_hit(hit):
            hits_over = max(0, hit.multiplier - 3 + self.cricket_display[hit.zone])

            if not self.cricket_closed[hit.zone]:
                self.cricket_display[hit.zone] += hit.multiplier
                if self.cricket_display[hit.zone] >= 3:
                    self.cricket_display[hit.zone] = 3
                    self.cricket_closed[hit.zone] = True
            
            return hits_over
        else:
            return 0


# -------------------------
# Game State
# -------------------------

class CricketGame:

    def __init__(self):

        self.teams = [
            Team("Team A", "Adam", "Charles"),
            Team("Team B", "Ben", "David")
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
        opponent = self.opponent_team()

        hits_over = team.add_hit(player, hit)

        if hits_over and not opponent.cricket_closed[hit.zone]:
            team.cricket_tallies[hit.zone] += hits_over
            team.score += hits_over * hit.zone

        self.darts_in_turn += 1

        if self.darts_in_turn == 3:
            self.next_turn()

    def save(self):
        pass
        # data = {
        #     "teams": [],
        #     "current_team": self.current_team,
        #     "current_player": self.current_player,
        #     "darts_in_turn": self.darts_in_turn
        # }

        # for team in self.teams:

        #     t = {
        #         "name": team.name,
        #         "score": team.score,
        #         "players": []
        #     }

        #     for p in team.players:
        #         t["players"].append({
        #             "name": p.name,
        #             "hits": p.hits,
        #             "score": p.score,
        #             "darts": p.darts_thrown
        #         })

        #     data["teams"].append(t)

        with open(SAVE_FILE, "w") as f:
            # json.dump(data, f)
            pass

    def load(self):
        pass

        # if not os.path.exists(SAVE_FILE):
        #     return

        # with open(SAVE_FILE) as f:
        #     data = json.load(f)

        # self.current_team = data["current_team"]
        # self.current_player = data["current_player"]
        # self.darts_in_turn = data["darts_in_turn"]

        # for t_i, tdata in enumerate(data["teams"]):

        #     team = self.teams[t_i]
        #     team.score = tdata["score"]

        #     for p_i, pdata in enumerate(tdata["players"]):

        #         p = team.players[p_i]
        #         p.hits = pdata["hits"]
        #         p.score = pdata["score"]
        #         p.darts_thrown = pdata["darts"]


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
        return None

    # angle from center
    angle = math.degrees(math.atan2(dy, dx))

    # convert to 0-360
    angle = (angle + 360) % 360

    # rotate so 0° is at top
    angle = (angle + 90 + 9) % 360

    # each wedge = 18 degrees
    index = int(angle / 18)

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
        root.title("Cricket Darts")

        self.game = CricketGame()

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

        tk.Button(btn_frame,text="Save",command=self.save).pack(side=tk.LEFT)
        tk.Button(btn_frame,text="Load",command=self.load).pack(side=tk.LEFT)

        # store markers for current turn
        self.dart_markers = []

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
        dot = self.canvas.create_oval(
            event.x-5, event.y-5,
            event.x+5, event.y+5,
            fill="cyan", outline=""
        )

        self.dart_markers.append(dot)

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
            self.clear_darts()

        self.update_label()

    def update_label(self):

        g = self.game

        player = g.active_player()
        team = g.teams[g.current_team]

        text = f"""
            Current Team: {team.name}
            Player: {player.name}
            Darts this turn: {g.darts_in_turn}
            """

        self.label.config(text=text)

        self.draw_scoreboard()

    def clear_darts(self):

        for marker in self.dart_markers:
            self.canvas.delete(marker)

        self.dart_markers = []

    def save(self):
        pass

        # self.game.save()

        # data = {
        #     "dart_history": self.dart_history
        # }

        # with open("dart_history.json","w") as f:
        #     json.dump(data,f,indent=2)

    def load(self):
        pass

        # self.game.load()

        # if os.path.exists("dart_history.json"):

        #     with open("dart_history.json") as f:
        #         data = json.load(f)

        #     self.dart_history = data["dart_history"]

        # self.update_label()

    def undo(self):
        pass

    def draw_scoreboard(self):

        c = self.score_canvas
        c.delete("all")

        col_width = 60
        start_x = 120
        start_y = 40

        # Header row (numbers)

        for i,num in enumerate(CRICKET_NUMBERS):

            x = start_x + i*col_width

            c.create_text(
                x,
                start_y,
                text=str(num),
                font=("Arial",14,"bold")
            )

        # Team labels

        c.create_text(50,80,text="Team A",font=("Arial",14,"bold"))
        c.create_text(50,130,text="Team B",font=("Arial",14,"bold"))

        # Team A marks

        for i,num in enumerate(CRICKET_NUMBERS):

            hits = self.game.teams[0].cricket_display[num] + self.game.teams[0].cricket_tallies[num]

            # hits = max(p.hits[num] for p in self.game.teams[0].players)
            # hits = self.team.cricket_display[num]

            x = start_x + i*col_width

            c.create_text(
                x,
                80,
                text=cricket_marks(hits),
                font=("Arial",16)
            )

        # Team B marks

        for i,num in enumerate(CRICKET_NUMBERS):

            hits = self.game.teams[1].cricket_display[num] + self.game.teams[1].cricket_tallies[num]

            x = start_x + i*col_width

            c.create_text(
                x,
                130,
                text=cricket_marks(hits),
                font=("Arial",16)
            )

        # Score column

        score_x = start_x + len(CRICKET_NUMBERS)*col_width + 20

        c.create_text(score_x,start_y,text="Score",font=("Arial",14,"bold"))

        c.create_text(
            score_x,
            80,
            text=str(self.game.teams[0].score),
            font=("Arial",16,"bold")
        )

        c.create_text(
            score_x,
            130,
            text=str(self.game.teams[1].score),
            font=("Arial",16,"bold")
        )


# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DartsApp(root)
root.mainloop()