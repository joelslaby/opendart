import math
import tkinter as tk

# -------------------------
# Dartboard math
# -------------------------

def interpret_click(x, y):

    size_mm = 473.2
    score_r_mm = 170
    dbull_r_mm = 12.7/2
    sbull_r_mm = 32/2
    double_r_mm = 162
    triple_r1_mm = 107
    triple_r2_mm = 99

    cx = 300
    cy = 300
    radius = score_r_mm * 600 / size_mm

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

    if dist <= dbull_r_mm*600/size_mm:
        return 25, 2
    elif dist <= sbull_r_mm*600/size_mm:
        return 25, 1
    else:
        board_numbers = [
            20,1,18,4,13,6,10,15,2,17,
            3,19,7,16,8,11,14,9,12,5
        ]

        if double_r_mm*600/size_mm <= dist <= score_r_mm*600/size_mm:
            mult = 2

        elif triple_r2_mm*600/size_mm <= dist <= triple_r1_mm*600/size_mm:
            mult = 3

        else:
            mult = 1

        return board_numbers[index], mult
    

# -------------------------
# Dart history changes
# -------------------------

def swap_players_history(hist,team_idx):
    # TODO: swap the dart history with a player switch (universal to game type)
    return hist

def swap_teams_history(hist):
    # TODO: swap the dart history with a team switch (universal to game type)
    return hist

# -------------------------
# Display
# -------------------------

def get_screen_size_tkinter():
    root = tk.Tk()
    # Withdraw the window so it doesn't flash on the screen
    root.withdraw()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy() # Close the root window
    return width, height
