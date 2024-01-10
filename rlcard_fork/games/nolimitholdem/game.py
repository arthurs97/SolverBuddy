from enum import Enum

import numpy as np
from copy import deepcopy
from rlcard_fork.games.limitholdem import Game
from rlcard_fork.games.limitholdem import PlayerStatus

from rlcard_fork.games.base import Card
from rlcard_fork.games.nolimitholdem import Dealer
from rlcard_fork.games.nolimitholdem import Player
from rlcard_fork.games.nolimitholdem import Judger
from rlcard_fork.games.nolimitholdem import Round, Action
from rlcard_fork.utils.utils import init_standard_deck
import json


class Stage(Enum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END_HIDDEN = 4
    SHOWDOWN = 5

class Position(Enum):
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
    
    @staticmethod
    def from_value(val):
        if val == 0:
            return Position.SB
        elif val == 1:
            return Position.BB
        elif val == 2:
            return Position.UTG
        elif val == 3:
            return Position.UTG1
        elif val == 4:
            return Position.MP
        elif val == 5:
            return Position.MP1
        elif val == 6:
            return Position.HJ
        elif val == 7:
            return Position.CO
        elif val == 8:
            return Position.BTN
        else:
            raise ValueError(f"Invalid position value: {val}")
    
    def next(self, num_players):
        positions = Position.positions(num_players)
        return positions[(positions.index(self) + 1) % len(positions)]

    @staticmethod
    def explanation_string(num_players):
        return','.join([str(p) for p in Position.positions(num_players)])
    
    @staticmethod
    def positions(num_players):
        if num_players == 2:
            return [Position.BB, Position.BTN]
        elif num_players == 3:
            return [Position.SB, Position.BB, Position.BTN]
        elif num_players == 4:
            return [Position.SB, Position.BB, Position.UTG, Position.BTN]
        elif num_players == 5:
            return [Position.SB, Position.BB, Position.UTG, Position.CO, Position.BTN]
        elif num_players == 6:
            return [Position.SB, Position.BB, Position.UTG, Position.HJ, Position.CO, Position.BTN]
        elif num_players == 7:
            return [Position.SB, Position.BB, Position.UTG, Position.MP, Position.HJ, Position.CO, Position.BTN]
        elif num_players == 8:
            return [Position.SB, Position.BB, Position.UTG, Position.UTG1, Position.MP, Position.HJ, Position.CO, Position.BTN]
        elif num_players == 9:
            return [Position.SB, Position.BB, Position.UTG, Position.UTG1, Position.MP, Position.MP1, Position.HJ, Position.CO, Position.BTN]


class NolimitholdemGame(Game):
    def __init__(
            self, 
            small_blind=1,
            big_blind=2,
            effective_stack=100, 
            hero_position=Position.BB,
            allow_step_back=False, 
            num_players=2):
        """Initialize the class no limit holdem Game"""
        super().__init__(small_blind, big_blind, allow_step_back, num_players)

        self.np_random = np.random.RandomState()

        # small blind and big blind
        self.small_blind = small_blind
        self.big_blind = big_blind

        # config players
        self.init_chips = [effective_stack] * num_players

        # If None, the dealer will be randomly chosen
        self.dealer_id = None

        self.effective_stack = 0
        self.hero_position = hero_position
        self.deck = init_standard_deck()

    def configure(self, game_config):
        """
        Specify some game specific parameters, such as number of players, initial chips, and dealer id.
        If dealer_id is None, he will be randomly chosen
        """
        self.num_players = game_config['game_num_players']
        # must have num_players length
        self.init_chips = [game_config['chips_for_each']] * game_config["game_num_players"]
        self.dealer_id = game_config['dealer_id']

    def init_game(self):
        """
        Initialize the game of no limit holdem

        This version supports two-player no limit texas holdem

        Returns:
            (tuple): Tuple containing:

                (dict): The first state of the game
                (int): Current player's id
        """

        # Initialize players to play the game
        positions = Position.positions(self.num_players)
        self.players = [Player(i, positions[i], self.init_chips[i], self.np_random) for i in range(self.num_players)]

        # Initialize a judger class which will decide who wins in the end
        self.judger = Judger(self.np_random)

        # Initialize public cards
        self.public_cards = []
        self.stage = Stage.PREFLOP

        # Big blind and small blind
        # s = (self.dealer_id + 1) % self.num_players
        # b = (self.dealer_id + 2) % self.num_players
        sb: Player = self.players[0]
        bb: Player = self.players[1]
        sb.bet(chips=self.small_blind)
        bb.bet(chips=self.big_blind)
        

        # the game pointer is the index of the `players` list who is next to act
        # in HU, the pointer starts on 1 (BTN). On all other modes, the pointer starts on 2 (first player after BB)
        self.game_pointer: int = 1 if self.num_players == 2 else 2
        

        # Initialize a bidding round, in the first round, the big blind and the small blind needs to
        # be passed to the round for processing.
        self.round = Round(self.num_players, self.big_blind, dealer=self.dealer, np_random=self.np_random)

        self.round.start_new_round(game_pointer=self.game_pointer, raised=[p.in_chips for p in self.players])

        # Count the round. There are 4 rounds in each game.
        self.round_counter = 0

        # Save the history for stepping back to the last state.
        self.history = []

        state = self.get_state(self.game_pointer)

        return state, self.game_pointer
    
    def hero(self):
        return self.players[self.hero_position.value]
    
    def get_legal_actions(self):
        """
        Return the legal actions for current player

        Returns:
            (list): A list of legal actions
        """
        return self.round.get_nolimit_legal_actions(players=self.players)

    def step(self, action, size=None):
        """
        Get the next state

        Args:
            action (str): a specific action. (check, call, bet, raise, or fold)

        Returns:
            (tuple): Tuple containing:

                (dict): next player's state
                (int): next player id
        """

        if action not in self.get_legal_actions():
            print(action, self.get_legal_actions())
            print(self.get_state(self.game_pointer))
            raise Exception('Action not allowed')

        if self.allow_step_back:
            # First snapshot the current state
            r = deepcopy(self.round)
            b = self.game_pointer
            r_c = self.round_counter
            d = deepcopy(self.dealer)
            p = deepcopy(self.public_cards)
            ps = deepcopy(self.players)
            self.history.append((r, b, r_c, d, p, ps))

        # Then we proceed to the next round
        self.game_pointer = self.round.proceed_round(self.players, action, size)

        players_in_bypass = [1 if player.status in (PlayerStatus.FOLDED, PlayerStatus.ALLIN) else 0 for player in self.players]
        if self.num_players - sum(players_in_bypass) == 1:
            last_player = players_in_bypass.index(0)
            if self.round.raised[last_player] >= max(self.round.raised):
                # If the last player has put enough chips, he is also bypassed
                players_in_bypass[last_player] = 1

        # If a round is over, we deal more public cards
        if self.round.is_over():
            self.game_pointer = 0
            if sum(players_in_bypass) < self.num_players:
                while players_in_bypass[self.game_pointer]:
                    self.game_pointer = (self.game_pointer + 1) % self.num_players

            '''
            # For the first round, we deal 3 cards
            if self.round_counter == 0:
                self.stage = Stage.FLOP
                self.public_cards.append(self.dealer.deal_card())
                self.public_cards.append(self.dealer.deal_card())
                self.public_cards.append(self.dealer.deal_card())
                if len(self.players) == np.sum(players_in_bypass):
                    self.round_counter += 1
            # For the following rounds, we deal only 1 card
            if self.round_counter == 1:
                self.stage = Stage.TURN
                self.public_cards.append(self.dealer.deal_card())
                if len(self.players) == np.sum(players_in_bypass):
                    self.round_counter += 1
            if self.round_counter == 2:
                self.stage = Stage.RIVER
                self.public_cards.append(self.dealer.deal_card())
                if len(self.players) == np.sum(players_in_bypass):
                    self.round_counter += 1
            '''

            self.round_counter += 1
            self.round.start_new_round(self.game_pointer)

        state = self.get_state(self.game_pointer)

        return state, self.game_pointer

    def get_state(self, player_id):
        """
        Return player's state

        Args:
            player_id (int): player id

        Returns:
            (dict): The state of the player
        """
        self.dealer.pot = np.sum([player.in_chips for player in self.players])

        chips = [self.players[i].in_chips for i in range(self.num_players)]
        legal_actions = self.get_legal_actions()
        state = self.players[player_id].get_state(self.public_cards, chips, legal_actions)
        state['stakes'] = [self.players[i].remained_chips for i in range(self.num_players)]
        state['current_player'] = self.game_pointer
        state['pot'] = self.dealer.pot
        state['stage'] = self.stage
        return state

    def step_back(self):
        """
        Return to the previous state of the game

        Returns:
            (bool): True if the game steps back successfully
        """
        if len(self.history) > 0:
            self.round, self.game_pointer, self.round_counter, self.dealer, self.public_cards, self.players = self.history.pop()
            self.stage = Stage(self.round_counter)
            return True
        return False

    def get_num_players(self):
        """
        Return the number of players in no limit texas holdem

        Returns:
            (int): The number of players in the game
        """
        return self.num_players

    def get_payoffs(self):
        """
        Return the payoffs of the game

        Returns:
            (list): Each entry corresponds to the payoff of one player
        """
        hands = [p.hand + self.public_cards if p.status in (PlayerStatus.ALIVE, PlayerStatus.ALLIN) else None for p in self.players]
        chips_payoffs = self.judger.judge_game(self.players, hands)
        return chips_payoffs
    
    def dump(self, live_players_only=True):
        """
        Dump the state of the object as a JSON string

        Returns:
            (str): The state of the object as a JSON string
        """
        state = {
            "Stage": str(self.stage),
            "Action on": str(self.game_pointer),
            "Round Counter": str(self.round_counter),
            "Public Cards": str(self.public_cards),
            "Players": []
        }
        for player in self.players:
            if live_players_only and player.status != PlayerStatus.ALIVE:
                continue
            player_state = {
                "position": Position.from_value(player.player_id),
                "hand": str(player.hand),
                "status": str(player.status),
                "chips": str(player.chips)
            }
            if player.position == self.hero_position:
                player_state["isHero"] = True
            state["Players"].append(player_state)
        
        print(json.dumps(state))

    @staticmethod
    def get_num_actions():
        """
        Return the number of applicable actions

        Returns:
            (int): The number of actions. There are 6 actions (call, raise_half_pot, raise_pot, all_in, check and fold)
        """
        return len(Action)
