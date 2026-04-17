from dataclasses import dataclass


@dataclass
class Hit:
    zone: int
    multiplier: int = 1
    location: tuple | None = None


class Player:
    def __init__(self, name):
        self.name = name
        self.hit_history: list[Hit] = []
        self.points_for = 0
        self.darts_thrown = 0

    def add_hit(self, hit: Hit):
        self.darts_thrown += 1
        self.hit_history.append(hit)


class Team:
    def __init__(self, name, p1, p2):
        self.name = name
        self.players = [Player(p1), Player(p2)]
        self.score = 501

    def get_player_by_name(self, name):
        return next((player for player in self.players if player.name == name), None)

    def add_hit(self, player: Player, hit: Hit):
        player.add_hit(hit)

    def set_player_names(self, names):
        self.players = [Player(name) for name in names]


class Game501:
    def __init__(self):
        self.teams = [
            Team("1236", "Jacob", "Joel"),
            Team("930", "Dustin", "Ravi"),
        ]
        self.reset()

    def active_player(self):
        return self.teams[self.current_team].players[self.current_player]

    def active_team(self):
        return self.teams[self.current_team]

    def all_players(self):
        return [player for team in self.teams for player in team.players]

    def players_by_turn_order(self):
        return [
            self.teams[0].players[0],
            self.teams[1].players[0],
            self.teams[0].players[1],
            self.teams[1].players[1],
        ]

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
        for team_index, team in enumerate(self.teams):
            if any(member.name == player_name for member in team.players):
                return team_index
        raise ValueError(f"Unknown player: {player_name}")

    def team_for_player(self, player):
        return self.teams[self.team_index_for_player(player)]

    def score_for_player(self, player):
        return self.team_for_player(player).score

    def set_team_player_names(self, team_index, names):
        self.teams[team_index].set_player_names(names)

    def swap_team_players(self, team_index):
        team = self.teams[team_index]
        team.players[0], team.players[1] = team.players[1], team.players[0]

    def swap_teams(self):
        self.teams[0], self.teams[1] = self.teams[1], self.teams[0]

    def get_player_by_name(self, name):
        for team in self.teams:
            player = team.get_player_by_name(name)
            if player:
                return player
        return None

    def next_turn(self):
        self.darts_in_turn = 0
        self.next_player = (self.next_player + 1) % 4
        self.current_team = self.next_player % 2
        self.current_player = self.next_player // 2
        self.turn_start_score = self.teams[self.current_team].score

    def register_hit(self, hit: Hit, hist=None):
        player = self.active_player()
        team = self.teams[self.current_team]

        team.add_hit(player, hit)
        team.score -= hit.multiplier * hit.zone
        self.darts_in_turn += 1

        if team.score == 0 and hit.multiplier == 2:
            print(f"{team.name} wins!")
            return

        if team.score <= 1:
            team.score = self.turn_start_score
            self.next_turn()
            return

        if self.darts_in_turn == 3:
            self.next_turn()

    def reset(self):
        self.next_player = 0
        self.current_team = 0
        self.current_player = 0
        self.darts_in_turn = 0

        for team in self.teams:
            team.score = 501

        self.turn_start_score = self.teams[self.current_team].score
