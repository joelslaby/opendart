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
    def __init__(self, name, *player_names):
        self.name = name
        self.players = [Player(player_name) for player_name in player_names]
        self.score = 501

    def get_player_by_name(self, name):
        return next((player for player in self.players if player.name == name), None)

    def add_hit(self, player: Player, hit: Hit):
        player.add_hit(hit)

    def set_player_names(self, names):
        self.players = [Player(name) for name in names]


class Game501:
    def __init__(self, mode="2v2"):
        self.mode = mode
        if mode == "1v1":
            self.teams = [
                Team("Team 1", "Jacob"),
                Team("Team 2", "Dustin"),
            ]
        else:
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

    def turn_order_slots(self):
        slots = []
        max_players = max((len(team.players) for team in self.teams), default=0)
        for player_index in range(max_players):
            for team_index, team in enumerate(self.teams):
                if player_index < len(team.players):
                    slots.append((team_index, player_index))
        return slots

    def players_by_turn_order(self):
        return [
            self.teams[team_index].players[player_index]
            for team_index, player_index in self.turn_order_slots()
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

    def set_team_name(self, team_index, name):
        self.teams[team_index].name = name

    def swap_team_players(self, team_index):
        team = self.teams[team_index]
        if len(team.players) < 2:
            return
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
        order = self.turn_order_slots()
        self.next_player = (self.next_player + 1) % len(order)
        self.current_team, self.current_player = order[self.next_player]
        self.turn_start_score = self.teams[self.current_team].score

    def register_hit(self, hit: Hit, hist=None):
        player = self.active_player()
        team = self.teams[self.current_team]

        team.add_hit(player, hit)
        team.score -= hit.multiplier * hit.zone
        self.darts_in_turn += 1

        if team.score == 0 and hit.multiplier == 2:
            self.winner = team.name
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
        self.winner = None

        for team in self.teams:
            team.score = 501

        self.turn_start_score = self.teams[self.current_team].score
