from dataclasses import dataclass

CRICKET_NUMBERS = [20, 19, 18, 17, 16, 15, 25]


@dataclass
class Hit:
    zone: int
    multiplier: int = 1
    location: tuple | None = None


class Player:
    def __init__(self, name):
        self.name = name
        self.hit_history: list[Hit] = []
        self.darts_thrown = 0
        self.reset()

    def add_hit(self, hit: Hit):
        self.darts_thrown += 1
        self.hit_history.append(hit)

        if hit.zone not in CRICKET_NUMBERS:
            return 0

        hits_over = max(0, hit.multiplier - 3 + self.cricket_display[hit.zone])
        if not self.cricket_closed[hit.zone]:
            self.cricket_display[hit.zone] = min(3, self.cricket_display[hit.zone] + hit.multiplier)
            self.cricket_closed[hit.zone] = self.cricket_display[hit.zone] >= 3
        return hits_over

    def reset(self):
        self.cricket_display = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_tallies = {num: 0 for num in CRICKET_NUMBERS}
        self.cricket_closed = {num: False for num in CRICKET_NUMBERS}
        self.score = 0


class CricketGame:
    def __init__(self):
        self.players = [
            Player("Jacob"),
            Player("Joel"),
        ]
        self.reset()

    def active_player(self):
        return self.players[self.current_player]

    def opponent_player(self):
        return self.players[1 - self.current_player]

    def all_players(self):
        return list(self.players)

    def players_by_turn_order(self):
        return list(self.players)

    def rotated_turn_order(self, start_player=None):
        players = self.players_by_turn_order()
        start_name = start_player.name if hasattr(start_player, "name") else start_player
        if start_name is None:
            start_name = self.active_player().name

        start_index = next(
            (index for index, player in enumerate(players) if player.name == start_name),
            0,
        )
        return players[start_index:] + players[:start_index]

    def team_index_for_player(self, player):
        player_name = player.name if hasattr(player, "name") else player
        for index, member in enumerate(self.players):
            if member.name == player_name:
                return index
        raise ValueError(f"Unknown player: {player_name}")

    def score_for_player(self, player):
        return self.players[self.team_index_for_player(player)].score

    def set_player_names(self, names):
        self.players = [Player(name) for name in names]

    def swap_players(self):
        self.players[0], self.players[1] = self.players[1], self.players[0]

    def next_turn(self):
        self.darts_in_turn = 0
        self.next_player = (self.next_player + 1) % 2
        self.current_player = self.next_player

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
            player.reset()
