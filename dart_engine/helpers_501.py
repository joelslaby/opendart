import numpy as np
import csv

# ---------------------------
# Display functions
# ---------------------------

def get_recommended_hits(num_darts_left,points):

    hits = []

    with open('references/dart_out_chart.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for nn, row in enumerate(reader):
            if nn != 0:
                if int(row[0]) == points:
                    hits = row[1:4]
                    if not hits[2]:
                        hits = hits[:-1]
                    if not hits[1]:
                        hits = hits[:-1]
                    if not hits[0]:
                        hits = hits[:-1]
    if num_darts_left == 1:
        if len(hits) > 2:
            hits = []
    if num_darts_left == 2:
        if len(hits) > 1:
            hits = []
    return hits
            
    

    

# ---------------------------
# Score calculation functions
# ---------------------------

def get_score_at_turn(hist,team_idx):
    scores = [0]
    curr_team = 0
    curr_throw = 0
    running_score = 501
    for hh,hit in enumerate(hist):
        if hit["team"] != curr_team:
            curr_team = hit["team"]
            if curr_team == team_idx:
                curr_throw += 1
                scores.append(0)
        if hit["team"] == team_idx:
            running_score -= hit["multiplier"] * hit["number"]
            if running_score <= 1:
                running_score = scores[curr_throw-1]
            scores[curr_throw] = running_score
    return scores

def get_past_scores(hist,player_name,team_idx):
    scores = [0]
    player_past_scores = []
    curr_team = 0
    curr_throw = 0
    curr_player_throw = -1
    running_score = 501
    last_player = ""
    for hh,hit in enumerate(hist):
        if hit["player"] == player_name and last_player != player_name:
            curr_player_throw += 1
            player_past_scores.append(0)
        if hit["team"] != curr_team:
            curr_team = hit["team"]
            if curr_team == team_idx:
                curr_throw += 1
                scores.append(0)
        if hit["team"] == team_idx:
            running_score -= hit["multiplier"] * hit["number"]
            if hit["player"] == player_name:
                player_past_scores[curr_player_throw] += hit["multiplier"] * hit["number"]
            if running_score <= 1:
                running_score = scores[curr_throw-1]
                if hit["player"] == player_name:
                    player_past_scores[curr_player_throw] = 0
            scores[curr_throw] = running_score

        last_player = hit["player"]
    if not player_past_scores:
        player_past_scores = [0]
    return player_past_scores