# -*- coding: utf-8 -*-
"""Implement no limit texas holdem Round class"""
from enum import Enum

from rlcard_fork.games.limitholdem import PlayerStatus


class Action(Enum):
    '''
    Enum representing the actions players can take
    '''
    FOLD = 0
    CHECK = 1
    CALL = 2
    BET = 3
    RAISE = 4

    @staticmethod
    def parse(action_str, sh_map=None):
        '''
        Parse an action string into an Action enum
        '''
        if sh_map is None:
            sh_map = {
                "F": Action.FOLD,
                "X": Action.CHECK,
                "C": Action.CALL,
                "B": Action.BET,
                "R": Action.RAISE
            }
        return Action[action_str.upper()] if len(action_str) > 1 \
            else sh_map[action_str.upper()]

    def shorthand(self, action_map=None):
        '''
        Get the shorthand representation of this action
        '''
        if action_map is None:
            action_map = {
                Action.FOLD: "F",
                Action.CHECK: "X",
                Action.CALL: "C",
                Action.BET: "B",
                Action.RAISE: "R"
            }
        return action_map[self]


class NolimitholdemRound:
    """Round can call functions from other classes to keep the game running"""

    def __init__(self, game, init_raise_amount, np_random):
        """
        Initialize the round class

        Args:
            num_players (int): The number of players
            init_raise_amount (int): The min raise amount when every round starts
        """
        self.np_random = np_random
        self.game_pointer = None
        self.game = game
        self.num_players = game.num_players
        self.init_raise_amount = init_raise_amount

        # Count the number without raise
        # If every player agree to not raise, the round is over
        self.not_raise_num = 0

        # Count players that are not playing anymore (folded or all-in)
        self.not_playing_num = 0

        # Raised amount for each player
        self.raised = [0 for _ in range(self.num_players)]

    def start_new_round(self, game_pointer, raised=None):
        """
        Start a new bidding round

        Args:
            game_pointer (int): The game_pointer that indicates the next player
            raised (list): Initialize the chips for each player

        Note: For the first round of the game, we need to setup the big/small blind
        """
        self.game_pointer = game_pointer
        self.not_raise_num = 0
        if raised:
            self.raised = raised
        else:
            self.raised = [0 for _ in range(self.num_players)]

    def validate_bet_size(self, size: int):
        """
        Check whether the bet size is legal

        Args:
            size (int): The size of the bet

        Raises:
            ValueError: If the bet size is illegal
        """
        # TODO
        raise ValueError("todo")
        
    def proceed_round(self, players, action, size):
        """
        Call functions from other classes to keep one round running

        Args:
            players (list): The list of players that play the game
            action (str/int): An legal action taken by the player

        Returns:
            (int): The game_pointer that indicates the next player
        """
        player = players[self.game_pointer]

        if action == Action.CHECK:
            self.not_raise_num += 1
        
        elif action == Action.CALL:
            diff = max(self.raised) - self.raised[self.game_pointer]
            self.raised[self.game_pointer] = max(self.raised)
            player.bet(chips=diff)
            self.not_raise_num += 1

        elif action in (Action.BET, Action.RAISE):
            self.raised[self.game_pointer] += size
            player.bet(chips=size)
            self.not_raise_num = 1

        elif action == Action.FOLD:
            player.status = PlayerStatus.FOLDED
            self.not_playing_num += 1

        if player.remained_chips < 0:
            raise Exception("Player in negative stake")

        if player.remained_chips == 0 and player.status != PlayerStatus.FOLDED:
            player.status = PlayerStatus.ALLIN
            self.not_playing_num += 1
            self.not_raise_num -= 1  # Because already counted in not_playing_num

        self.game_pointer = (self.game_pointer + 1) % self.num_players

        # Skip the folded players
        while players[self.game_pointer].status == PlayerStatus.FOLDED:
            self.game_pointer = (self.game_pointer + 1) % self.num_players

        return self.game_pointer

    def get_nolimit_legal_actions(self, players):
        """
        Obtain the legal actions for the current player

        Args:
            players (list): The players in the game

        Returns:
           (list):  A list of legal actions
        """
        player = players[self.game_pointer]
        # folding is always allowed
        allowed_actions = [Action.FOLD]
        # checking, initial betting are only allowed if there is no bet so far
        if max(self.raised) == 0:
            allowed_actions.append(Action.CHECK)
            allowed_actions.append(Action.BET)
        else:
            # if already facing a live bet, calling is always allowed
            allowed_actions.append(Action.CALL)
            allowed_actions.append(Action.RAISE)

        return allowed_actions
    def is_over(self):
        """
        Check whether the round is over

        Returns:
            (boolean): True if the current round is over
        """
        print("is_over()")
        print(f"not_raise_num: {self.not_raise_num}")
        print(f"not_playing_num: {self.not_playing_num}")
        print([p.status for p in self.game.players])           
        return self.not_raise_num + self.not_playing_num == self.num_players
