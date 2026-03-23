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
CRICKET_NUMBERS = [20,19,18,17,16,15,25]
SAVE_FILE = "darts_save.json"
T1_COLOR = "dodgerblue"
T2_COLOR = "blueviolet"
SCOREBOARD_BG = "darkolivegreen"
INFOBOARD_BG = "white"

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
        opponent = self.opponent_team()

        hits_over = team.add_hit(player, hit)

        if hits_over and not opponent.cricket_closed[hit.zone]:
            team.cricket_tallies[hit.zone] += hits_over
            team.score += hits_over * hit.zone

        self.darts_in_turn += 1

        if self.darts_in_turn == 3:
            self.next_turn()


    def reset(self):

        self.next_player = 0
        self.current_team = 0
        self.current_player = 0
        self.darts_in_turn = 0

        for team in self.teams:
            team.cricket_display = {num: 0 for num in CRICKET_NUMBERS}
            team.cricket_tallies = {num: 0 for num in CRICKET_NUMBERS}
            team.cricket_closed = {num: False for num in CRICKET_NUMBERS}
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
        root.title("Cricket Darts")
        root.attributes('-fullscreen', True)
        x = root.winfo_width()
        y = root.winfo_height()

        print(f"Screen size: {x}x{y}")

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
        self.score_label.pack(anchor="e")

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Motion>", self.update_cursor)

        self.score_canvas = tk.Canvas(root, width=x/2-self.size/2-2, height=600-2, bg=SCOREBOARD_BG)
        self.score_canvas.place(x=0, y=0)

        self.info_canvas = tk.Canvas(root, width=self.size-7, height=y-600-4, bg=INFOBOARD_BG)
        self.info_canvas.place(x=x/2-self.size/2+1, y=600)

        self.label = tk.Label(root, font=("Arial",14))
        self.label.pack(anchor="se")

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

        self.score_label.config(text=f"dart score: {number}, {mult}")

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
        self.update_label()

    def swap_players_team_1(self):
        self.game.teams[0].players[0], self.game.teams[0].players[1] = self.game.teams[0].players[1], self.game.teams[0].players[0]
        self.update_label()

    def swap_players_team_2(self):
        self.game.teams[1].players[0], self.game.teams[1].players[1] = self.game.teams[1].players[1], self.game.teams[1].players[0]
        self.update_label()

    def draw_scoreboard(self):

        c = self.score_canvas
        c.delete("all")

        size_x = 454
        mid_width = 80
        row_height = 68
        start_y = 90

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

            # hits = max(p.hits[num] for p in self.game.teams[0].players)
            # hits = self.team.cricket_display[num]

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

        width = 593
        panel_height = 180
        panel_width = int((width-2)/3)
        pfp_size = 70

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

        player_list = [player0, player1, player2, player3]
        player_list = player_list[-k:] + player_list[:-k]
    
        text = f"""
            Current Team: {team.name}
            Player: {player.name}
            Darts this turn: {g.darts_in_turn}
            Next Players: {upcoming_list[1]}, {upcoming_list[2]}, {upcoming_list[3]}
            """
        
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        search_dir = "Profile_Pics"

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

        #Next next player panel
        c.create_text(
            width/2,
            12+panel_height,
            text=player_list[2].name,
            font=("Arial",20,"bold"),
            fill=T1_COLOR if player_list[2].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

        #Next next next player panel
        c.create_text(
            width/2 + panel_width,
            12+panel_height,
            text=player_list[3].name,
            font=("Arial",20,"bold"),
            fill=T1_COLOR if player_list[3].name in [self.game.teams[0].players[0].name, self.game.teams[0].players[1].name] else T2_COLOR
        )

# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DartsApp(root)
root.mainloop()