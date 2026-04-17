import csv
from functools import lru_cache


@lru_cache(maxsize=1)
def _load_checkout_chart() -> dict[int, list[str]]:
    chart = {}
    with open("references/dart_out_chart.csv", newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        next(reader, None)
        for row in reader:
            score = int(row[0])
            chart[score] = [hit for hit in row[1:4] if hit]
    return chart


def get_recommended_hits(num_darts_left, points):
    hits = _load_checkout_chart().get(points, []).copy()
    if len(hits) > num_darts_left:
        return []
    return hits


def get_score_at_turn(hist, team_idx):
    scores = [501]
    score = 501
    darts_in_turn = 0

    for hit in hist:
        if hit["team"] != team_idx:
            continue

        score -= hit["multiplier"] * hit["number"]
        darts_in_turn += 1

        if score <= 1:
            score = scores[-1]
            darts_in_turn = 3

        if darts_in_turn == 3:
            scores.append(score)
            darts_in_turn = 0

    if darts_in_turn:
        scores.append(score)

    return scores


def get_past_scores(hist, player_name, team_idx):
    past_scores = []
    score_in_turn = 0
    last_player = None
    team_score = 501
    team_turn_start = 501

    for hit in hist:
        if hit["team"] == team_idx and hit["player"] != last_player:
            team_turn_start = team_score

        if hit["player"] == player_name and hit["player"] != last_player:
            score_in_turn = 0
            past_scores.append(score_in_turn)

        if hit["team"] == team_idx:
            points = hit["multiplier"] * hit["number"]
            team_score -= points

            if hit["player"] == player_name and past_scores:
                score_in_turn += points
                past_scores[-1] = score_in_turn

            if team_score <= 1:
                team_score = team_turn_start
                if hit["player"] == player_name and past_scores:
                    score_in_turn = 0
                    past_scores[-1] = score_in_turn

        last_player = hit["player"]

    return past_scores or [0]
