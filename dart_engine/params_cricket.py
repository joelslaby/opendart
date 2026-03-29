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
        self.points_for = 0
        self.darts_thrown = 0

    def add_hit(self, hit: Hit):
        self.darts_thrown += 1
        self.hit_history.append(hit)

        if hit.zone not in CRICKET_NUMBERS:
            return 0
        else:
            return hit.zone


# -------------------------
# Team class
# -------------------------

class Team:
    def __init__(self, name, p1, p2):
        self.name = name
        self.players = [Player(p1), Player(p2)]
        self.cricket_display = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_tallies = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_closed = {num: False for num in CRICKET_NUMBERS}
        self.score = 0

    def has_closed(self, number):
        if sum(p.hits[number] for p in self.players) >= 3:
            self.cricket_closed[number] = True
        return self.cricket_closed[number]
    
    def add_hit(self, player: Player, hit: Hit):
        
        player.add_hit(hit)
        if player.add_hit(hit):
            hits_over = max(0, hit.multiplier - 3 + self.cricket_display[hit.zone])

            if not self.cricket_closed[hit.zone]:
                self.cricket_display[hit.zone] += hit.multiplier
                if self.cricket_display[hit.zone] >= 3:
                    self.cricket_display[hit.zone] = 3
                    self.cricket_closed[hit.zone] = True
            
            return hits_over
        else:
            return 0
        
    def get_player_by_name(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None


# -------------------------
# Game State
# -------------------------

class CricketGame:

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


    def register_hit(self, hit: Hit):

        player = self.active_player()
        team = self.teams[self.current_team]
        opponent = self.opponent_team()

        hits_over = team.add_hit(player, hit)

        if hits_over and not opponent.cricket_closed[hit.zone]:
            team.cricket_tallies[hit.zone] += hits_over
            team.score += hits_over * hit.zone

        self.darts_in_turn += 1

        if self.darts_in_turn == 3:
            self.next_turn()


    def reset(self):

        self.next_player = 0
        self.current_team = 0
        self.current_player = 0
        self.darts_in_turn = 0

        for team in self.teams:
            team.cricket_display = {num: 0 for num in CRICKET_NUMBERS}
            team.cricket_tallies = {num: 0 for num in CRICKET_NUMBERS}
            team.cricket_closed = {num: False for num in CRICKET_NUMBERS}
            team.score = 0

    def get_player_by_name(self, name):
        for team in self.teams:
            player = team.get_player_by_name(name)
            if player:
                return player
        return None