import os
import sys

sys.path.append('/Users/arthurshi/SolverBuddy')

from rlcard_fork.games.nolimitholdem.game import Card, Position, NolimitholdemGame as Game


def main():
    print(sys.path)
    game = None

    while True:
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

        game = Game(small_blind, big_blind, effective_stack, hero_position, num_players=num_players)
        
        game.hero().hand = [
            Card(cards[0].upper(), cards[1].upper()),
            Card(cards[2].upper(), cards[3].upper())]
        for card in game.hero().hand:
            game.deck.remove(card)
        
        # start the hand, beginning with posting for the blinds
        game.init_game()

        player_to_act = Position.positions(num_players)[game.game_pointer]
        

        while not game.round.is_over():
            action = input(f"{player_to_act}'s action: (call/c, raise/r, fold/f)")
            size = None
            if action.upper() == "R" or action.upper() == "RAISE":
                size = input("Raise size: (number of 'allin')")
                size = game.players[game.game_pointer].remained_chips if size == "allin" else int(size)
            state, next_player_idx = game.step(action, size)
            print(state)
            game.dump()
            player_to_act = Position.positions(num_players)[next_player_idx]
        
        game.dump()

    return
    
if __name__ == "__main__":
    main()
