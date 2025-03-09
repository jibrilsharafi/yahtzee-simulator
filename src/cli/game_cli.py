# Contents of /yahtzee-simulator/yahtzee-simulator/src/cli/game_cli.py

import sys
from game.yahtzee_game import YahtzeeGame
from strategies.rule_based_strategy import RuleBasedStrategy
from strategies.random_strategy import RandomStrategy

def main():
    print("Welcome to the Yahtzee Simulator!")
    game = YahtzeeGame()
    
    while not game.is_game_over():
        print(game)
        current_player = game.current_player()
        print(f"Current player: {current_player.name}")
        
        # Example of using a strategy
        strategy = RuleBasedStrategy()  # or RandomStrategy()
        dice_to_keep, score_choice = strategy.select_dice_and_score(game.get_current_state(), game.roll_dice())
        
        game.update_game_state(dice_to_keep, score_choice)
        
        if game.is_game_over():
            print("Game over!")
            print(game.get_winner())
            break

if __name__ == "__main__":
    main()