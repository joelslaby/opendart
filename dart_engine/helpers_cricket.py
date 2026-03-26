import numpy as np

CRICKET_NUMBERS = [20,19,18,17,16,15,25]

# ---------------------------
# Display functions
# ---------------------------

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


# ---------------------------
# Score calculation functions
# ---------------------------

def get_game_marks(hist,teams,player):

    remaining_score_team_0 = 3*np.ones(len(CRICKET_NUMBERS))
    remaining_score_team_1 = 3*np.ones(len(CRICKET_NUMBERS))

    marks = [0]
    num_turn = 0
    num_dart = 0
    for hh,hit in enumerate(hist):
        if hit["player"] == player.name:
            num_dart += 1
            if num_dart > 3:
                num_dart = 1
                num_turn += 1
                marks.append(0)

        if hit["number"] in CRICKET_NUMBERS:
            if hit["player"] in [teams[0].players[0].name, teams[0].players[1].name]:
                if remaining_score_team_0[CRICKET_NUMBERS.index(hit["number"])] > 0:
                    idx = CRICKET_NUMBERS.index(hit["number"])
                    remaining_score_team_0[idx] -= hit["multiplier"]
                    if remaining_score_team_0[idx] < 0:
                        if remaining_score_team_1[idx] == 0:
                            if player.name == hit["player"]:
                                marks[num_turn] += hit["multiplier"] + remaining_score_team_0[idx]
                        else:
                            if player.name == hit["player"]:
                                marks[num_turn] += hit["multiplier"]
                        remaining_score_team_0[idx] = 0
                    else:
                        if player.name == hit["player"]:
                            marks[num_turn] += hit["multiplier"]
                elif remaining_score_team_0[CRICKET_NUMBERS.index(hit["number"])] == 0 and remaining_score_team_1[CRICKET_NUMBERS.index(hit["number"])] > 0:
                    if player.name == hit["player"]:
                        marks[num_turn] += hit["multiplier"]
            else:
                if remaining_score_team_1[CRICKET_NUMBERS.index(hit["number"])] > 0:
                    idx = CRICKET_NUMBERS.index(hit["number"])
                    remaining_score_team_1[idx] -= hit["multiplier"]
                    if remaining_score_team_1[idx] < 0:
                        if remaining_score_team_0[idx] == 0:
                            if player.name == hit["player"]:
                                marks[num_turn] += hit["multiplier"] + remaining_score_team_1[idx]
                        else:                                    
                            if player.name == hit["player"]:
                                marks[num_turn] += hit["multiplier"]
                        remaining_score_team_1[idx] = 0
                    else:
                        if player.name == hit["player"]:
                            marks[num_turn] += hit["multiplier"]
                elif remaining_score_team_1[CRICKET_NUMBERS.index(hit["number"])] == 0 and remaining_score_team_0[CRICKET_NUMBERS.index(hit["number"])] > 0:
                    if player.name == hit["player"]:
                        marks[num_turn] += hit["multiplier"]
    
    return [int(m) for m in marks]