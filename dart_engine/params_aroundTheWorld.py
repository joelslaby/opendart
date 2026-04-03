from dataclasses import dataclass

ATW_ORDER = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,25,0]

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
        self.current_number_idx = 0
    
    def add_hit(self, hit: Hit):

        self.darts_thrown += 1
        self.hit_history.append(hit)

        if hit.zone == ATW_ORDER[self.current_number_idx]:
            self.current_number_idx += 1


# -------------------------
# Game State
# -------------------------

class ATWGame:

    def __init__(self):

        self.players = [
            Player("Jacob"),
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
        self.next_player %= 1
        self.current_player = self.next_player % 1


    def register_hit(self, hit: Hit):

        player = self.active_player()

        player.add_hit(hit)

        self.darts_in_turn += 1

        if self.darts_in_turn == 3:
            self.next_turn()


    def reset(self):

        self.next_player = 0
        self.current_player = 0
        self.darts_in_turn = 0

        for player in self.players:
            player.current_number_idx = 0