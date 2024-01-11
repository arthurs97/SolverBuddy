import os
import sys

sys.path.append('/Users/arthurshi/SolverBuddy')
from rlcard_fork.games.nolimitholdem.player import Position
from rlcard_fork.games.nolimitholdem.game import Card, NolimitholdemGame as Game
from rlcard_fork.games.nolimitholdem.round import Action


def main():
    print(sys.path)
    game = None

    print("Starting the program. Type 'exit' to quit.")
    
    # blinds = input("What are the blinds? (e.g. 1/2)")
    blinds = "1/2"
    blinds = blinds.split("/")
    
    # effective_stack = int(input("What is the effective stack in this hand?"))
    effective_stack = 200

    # num_players = int(input("How many players are there?"))
    num_players = 6

    small_blind = int(blinds[0])
    big_blind = int(blinds[1])

    pos = input(f"What position are you in? ({Position.explanation_string(num_players)})")
    hero_position = Position[pos.upper()]
    

    cards = input("What cards do you have? (e.g. Th2s)")

    game = Game(small_blind, big_blind, effective_stack, hero_position, allow_step_back=False, num_players=num_players)
    print(f"hero position: {hero_position}")
    print(f"hero index: {game.hero_index}")
    game.hero().hand = [
        Card(cards[0].upper(), cards[1].upper()),
        Card(cards[2].upper(), cards[3].upper())]
    for card in game.hero().hand:
        game.deck.remove(card)
    
    # start the hand, beginning with posting for the blinds
    game.init_game()

    player_to_act = Position.positions(num_players)[game.game_pointer]

    while not game.round.is_over():
        legal_actions = game.get_legal_actions()
        actions_string = \
            ",".join([f"{action.name.lower()}/{action.shorthand().lower()}" for action in legal_actions])
        action = Action.parse(input(f"{player_to_act}'s action: ({actions_string})"))

        size = None
        if action == Action.BET or action == Action.RAISE:
            size = input("Bet size: (total number or 'allin')")
            size = game.players[game.game_pointer].remained_chips if size == "allin" else int(size)
        state, next_player_idx = game.step(action, size)
        # print(state)
        game.dump()
        player_to_act = Position.positions(num_players)[next_player_idx]
    
    game.dump()

    return
    
if __name__ == "__main__":
    main()
