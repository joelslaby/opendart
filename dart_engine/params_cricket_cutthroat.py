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

    def add_hit(self, hit: Hit) -> int:
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
        self.hits_against = {num: 0 for num in CRICKET_NUMBERS}


class CricketGame:
    """Cutthroat cricket for 3+ players.

    Marks scored on a number after it's already closed by the thrower add
    points to every OTHER player who hasn't closed that number yet (instead
    of to the thrower's own score, as in standard cricket). Lowest score
    wins once a player has closed all seven numbers.
    """

    def __init__(self, player_names=("Player 1", "Player 2", "Player 3")):
        self.players = [Player(name) for name in player_names]
        self.reset()

    def active_player(self):
        return self.players[self.current_player]

    def opponents(self, player=None):
        player = player or self.active_player()
        return [p for p in self.players if p is not player]

    def all_players(self):
        return list(self.players)

    def players_by_turn_order(self):
        return list(self.players)

    def rotated_turn_order(self, start_player=None):
        players = self.players_by_turn_order()
        if not players:
            return []

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

    def get_player_by_name(self, name):
        return next((player for player in self.players if player.name == name), None)

    def player_has_closed(self, player):
        return all(player.cricket_closed[number] for number in CRICKET_NUMBERS)

    def check_winner(self):
        for player in self.players:
            others = self.opponents(player)
            if self.player_has_closed(player) and all(player.score <= other.score for other in others):
                self.winner = player.name
                return self.winner
        return None

    def next_turn(self):
        self.darts_in_turn = 0
        self.next_player = (self.next_player + 1) % len(self.players)
        self.current_player = self.next_player

    def register_hit(self, hit: Hit):
        player = self.active_player()

        hits_over = player.add_hit(hit)
        if hits_over:
            for opponent in self.opponents(player):
                if not opponent.cricket_closed[hit.zone]:
                    opponent.score += hits_over * hit.zone
                    opponent.hits_against[hit.zone] += hits_over

        self.check_winner()
        if self.winner:
            return

        self.darts_in_turn += 1
        if self.darts_in_turn == 3:
            self.next_turn()

    def reset(self):
        self.next_player = 0
        self.current_player = 0
        self.darts_in_turn = 0
        self.winner = None

        for player in self.players:
            player.reset()
