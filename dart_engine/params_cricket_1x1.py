from dataclasses import dataclass

CRICKET_NUMBERS = [20,19,18,17,16,15,25]

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
        self.cricket_display = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_tallies = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_closed = {num: False for num in CRICKET_NUMBERS}
        self.score = 0

    def has_closed(self, number):
        if sum(self.hit_history[number]) >= 3:
            self.cricket_closed[number] = True
        return self.cricket_closed[number]
    
    def add_hit(self, hit: Hit):

        self.darts_thrown += 1
        self.hit_history.append(hit)

        if hit.zone in CRICKET_NUMBERS:
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


    def register_hit(self, hit: Hit):

        player = self.active_player()
        opponent = self.opponent_player()

        hits_over = player.add_hit(hit)

        if hits_over and not opponent.cricket_closed[hit.zone]:
            player.cricket_tallies[hit.zone] += hits_over
            player.score += hits_over * hit.zone

        self.darts_in_turn += 1

        if self.darts_in_turn == 3:
            self.next_turn()


    def reset(self):

        self.next_player = 0
        self.current_player = 0
        self.darts_in_turn = 0

        for player in self.players:
            player.cricket_display = {num: 0 for num in CRICKET_NUMBERS}
            player.cricket_tallies = {num: 0 for num in CRICKET_NUMBERS}
            player.cricket_closed = {num: False for num in CRICKET_NUMBERS}
            player.score = 0