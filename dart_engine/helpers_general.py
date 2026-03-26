import math

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
# Dart history changes
# -------------------------

def swap_players_history(hist,team_idx):
    # TODO: swap the dart history with a player switch (universal to game type)
    return hist

def swap_teams_history(hist):
    # TODO: swap the dart history with a team switch (universal to game type)
    return hist