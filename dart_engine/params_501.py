from dataclasses import dataclass
from dart_engine.helpers_501 import get_score_at_turn

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
        
    def get_player_by_name(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

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

class Game501:

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


    def register_hit(self, hit: Hit, hist):

        player = self.active_player()
        team = self.teams[self.current_team]

        team.add_hit(player, hit)

        team.score -= hit.multiplier * hit.zone

        self.darts_in_turn += 1

        if team.score == 0 and hit.multiplier == 2:
            print(f"{team.name} wins!")
        elif team.score <= 1:
            team.score += hit.multiplier * hit.zone
            team.score = get_score_at_turn(hist,self.current_team)[-2]
            self.next_turn()
        elif self.darts_in_turn == 3:
            self.next_turn()


    def reset(self):

        self.next_player = 0
        self.current_team = 0
        self.current_player = 0
        self.darts_in_turn = 0
        self.darts_in_turn = 0

        for team in self.teams:
            team.score = 501

    def get_player_by_name(self, name):
        for team in self.teams:
            player = team.get_player_by_name(name)
            if player:
                return player
        return None