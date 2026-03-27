import json
import pandas as pd
from collections import defaultdict
import copy
import matplotlib.pyplot as plt
from PIL import Image

CRICKET_NUMBERS = [20,19,18,17,16,15,25]

dartboard_path = "/Users/jslaby/Documents/projects/darts/opendart/dartboard.png"
data_path = "/Users/jslaby/Documents/projects/darts/data/cricket/"
data_file = "Cricket_2026-03-22_22:01"

with open(data_path + data_file + ".json") as f:
    data = json.load(f)

df = pd.DataFrame(data["dart_history"])

# turn index
df["throw_index"] = df.index
df["turn"] = df.index // 3

# columns for board states
df["board_state_before"] = None
df["board_state_after"] = None

# derived columns
cols = [
    "marks_before","marks_after",
    "opponent_marks_before","opponent_marks_after",
    "team_score_before","team_score_after",
    "marks_added","closing_marks","overmarks",
    "points_scored",
    "number_closed",
    "closing_dart","scoring_dart",
    "closing_triple","point_triple",
    "closing_double","point_double"
]

for c in cols:
    df[c] = 0

bool_cols = [
    "number_closed","closing_dart","scoring_dart",
    "closing_triple","point_triple",
    "closing_double","point_double"
]

df[bool_cols] = False


team_marks = {
    0: {n:0 for n in CRICKET_NUMBERS},
    1: {n:0 for n in CRICKET_NUMBERS}
}

team_points = {0:0,1:0}


for i,row in df.iterrows():

    team = row.team
    opponent = 1 - team
    number = row.number
    mult = row.multiplier

    # snapshot board before
    df.at[i,"board_state_before"] = copy.deepcopy(team_marks)

    points_scored = 0
    marks_added = 0
    closing_marks = 0
    overmarks = 0

    marks_before = team_marks[team].get(number,0)
    opp_before = team_marks[opponent].get(number,0)

    score_before = team_points[team]

    if number in CRICKET_NUMBERS:

        for _ in range(mult):

            if team_marks[team][number] < 3:

                team_marks[team][number] += 1
                marks_added += 1

                if team_marks[team][number] == 3:
                    closing_marks += 1

            else:

                if team_marks[opponent][number] < 3:
                    overmarks += 1
                    points_scored += number


    team_points[team] += points_scored

    marks_after = team_marks[team].get(number,0)
    opp_after = team_marks[opponent].get(number,0)
    score_after = team_points[team]

    # snapshot board after
    df.at[i,"board_state_after"] = copy.deepcopy(team_marks)

    # write columns
    df.loc[i,"marks_before"] = marks_before
    df.loc[i,"marks_after"] = marks_after
    df.loc[i,"opponent_marks_before"] = opp_before
    df.loc[i,"opponent_marks_after"] = opp_after

    df.loc[i,"team_score_before"] = score_before
    df.loc[i,"team_score_after"] = score_after

    df.loc[i,"marks_added"] = marks_added
    df.loc[i,"closing_marks"] = closing_marks
    df.loc[i,"overmarks"] = overmarks
    df.loc[i,"points_scored"] = points_scored

    # flags
    if closing_marks > 0:
        df.loc[i,"closing_dart"] = True

    if points_scored > 0:
        df.loc[i,"scoring_dart"] = True

    if marks_before < 3 and marks_after >= 3:
        df.loc[i,"number_closed"] = True

    if mult == 3:
        if closing_marks > 0:
            df.loc[i,"closing_triple"] = True
        if points_scored > 0:
            df.loc[i,"point_triple"] = True

    if mult == 2:
        if closing_marks > 0:
            df.loc[i,"closing_double"] = True
        if points_scored > 0:
            df.loc[i,"point_double"] = True

df.to_pickle(data_path + data_file + ".pkl")

print(df.groupby("player")["closing_triple"].sum())
print(df.groupby("player")["point_triple"].sum())
print(df.groupby("player")["closing_double"].sum())
print(df.groupby("player")["point_double"].sum())
print(df.groupby("player")["points_scored"].sum())
print(df.groupby("player")["marks_added"].sum())
print(df.groupby("player")["closing_dart"].sum())
print(df[df.point_triple].groupby("player")["points_scored"].sum())
print(df.groupby("player")["closing_marks"].sum())
print(df[df.points_scored > 0 & (df.number.isin(CRICKET_NUMBERS))].groupby(["player","number"])["points_scored"].sum())
print(df.groupby("player")["points_scored"].sum() / df.groupby("player").size())
# print(df.groupby(["player","turn"])["points_scored"].sum())
print(df[df.number_closed].groupby(["player","number"]).size())
print(df.groupby("player")["overmarks"].sum())
# print(df.groupby(["player","turn"])["marks_added"].sum())

print(df[(df.marks_before == 0) & (df.number.isin(CRICKET_NUMBERS))].groupby(["player","number"]).size())

print(df[(df.closing_dart == True)].groupby(["player","number"]).size())

print(df[df.scoring_dart].groupby(["player","number"])["points_scored"].sum())

print(df[(df.number_closed) & (df.opponent_marks_before < 3)].groupby(["player","number"]).size())

def plot_darts(cricket_data):
    for dart in cricket_data['dart_history']:
        match dart['player']:
            case "Jacob":
                color = 'tab:blue'
            case "Joel":
                color = 'tab:green'
            case "Ravi":
                color = 'tab:red'
            case "Dustin":
                color = 'tab:orange'
        x = dart['x']
        y = dart['y']
        plt.scatter(x, y, color=color, s=5)
    
    # plt.imshow(img)
    dartboard = Image.open(dartboard_path)
    plt.imshow(dartboard)
    plt.show()

plot_darts(data)
