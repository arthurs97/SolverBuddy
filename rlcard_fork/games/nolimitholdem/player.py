from enum import Enum
from rlcard_fork.games.limitholdem import Player

class NolimitholdemPlayer(Player):
    def __init__(self, player_id, position, init_chips, np_random):
        """
        Initialize a player.

        Args:
            player_id (int): The id of the player. This is equivalent to the index in the players list.
            init_chips (int): The number of chips the player has initially
        """
        super().__init__(player_id, np_random)
        self.position = position
        self.remained_chips = init_chips

    def bet(self, chips):
        quantity = chips if chips <= self.remained_chips else self.remained_chips
        self.in_chips += quantity
        self.remained_chips -= quantity


class Position(Enum):
    """
    Enum representing the positions players can occupy
    """
    SB = 0
    BB = 1
    UTG = 2
    UTG1 = 3
    MP = 4
    MP1 = 5
    HJ = 6
    CO = 7
    BTN = 8

    def __str__(self):
        return self.name

    def next(self, num_players):
        positions = Position.positions(num_players)
        return positions[(positions.index(self) + 1) % len(positions)]

    @staticmethod
    def explanation_string(num_players):
        return ','.join([str(p) for p in Position.positions(num_players)])

    @staticmethod
    def positions(num_players):
        player_count_to_positions = {
            2: [Position.BB, Position.BTN],
            3: [Position.SB, Position.BB, Position.BTN],
            4: [Position.SB, Position.BB, Position.UTG, Position.BTN],
            5: [Position.SB, Position.BB, Position.UTG, Position.CO, Position.BTN],
            6: [Position.SB, Position.BB, Position.UTG, Position.HJ, Position.CO, Position.BTN],
            7: [Position.SB, Position.BB, Position.UTG, Position.MP, Position.HJ, Position.CO, Position.BTN],
            8: [Position.SB, Position.BB, Position.UTG, Position.UTG1, Position.MP, Position.HJ, Position.CO, Position.BTN],
            9: [Position.SB, Position.BB, Position.UTG, Position.UTG1, Position.MP, Position.MP1, Position.HJ, Position.CO, Position.BTN]
        }
        return player_count_to_positions[num_players]
