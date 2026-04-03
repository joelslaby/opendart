from dataclasses import dataclass
from dart_engine.helpers_501_1x1 import get_score_at_turn

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
        self.darts_thrown = 0
        self.score = 501
    
    def add_hit(self, hit: Hit):
        self.darts_thrown += 1
        self.hit_history.append(hit)


# -------------------------
# Game State
# -------------------------

class Game501:

    def __init__(self):

        self.players = [
            Player("Jacob"),
            Player("Joel"),
        ]

        self.next_player = 0
        self.current_player = 0
        self.darts_in_turn = 0

    def active_player(self):
        return self.players[self.current_player]

    def opponent_player(self):
        return self.players[1 - self.current_player]

    def next_turn(self):

        self.darts_in_turn = 0
        self.next_player += 1
        self.next_player %= 2
        self.current_player = self.next_player % 2


    def register_hit(self, hit: Hit, hist):

        player = self.active_player()

        player.add_hit(hit)

        player.score -= hit.multiplier * hit.zone

        self.darts_in_turn += 1

        if player.score == 0 and hit.multiplier == 2:
            print(f"{player.name} wins!")
        elif player.score <= 1:
            player.score = get_score_at_turn(hist,self.current_player)[-2]
            self.next_turn()
        elif self.darts_in_turn == 3:
            self.next_turn()


    def reset(self):

        self.next_player = 0
        self.current_player = 0
        self.darts_in_turn = 0

        for player in self.players:
            player.score = 501