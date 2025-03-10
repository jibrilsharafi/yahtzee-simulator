from typing import Dict

from src.game.yahtzee_game import YahtzeeGame
from src.strategies.base_strategy import BaseStrategy
from src.strategies.random_strategy import RandomStrategy
from src.strategies.rule_based_strategy import RuleBasedStrategy
from src.strategies.expected_value_strategy import ExpectedValueStrategy


def main() -> None:
    print("Welcome to the Yahtzee Simulator!")
    game = YahtzeeGame()

    # Set up players
    num_players = int(input("Enter number of players: "))
    strategies: Dict[str, BaseStrategy] = {}

    for i in range(num_players):
        name = input(f"Enter name for player {i+1}: ")
        strategy_choice = input(
            f"Choose strategy for {name} (1: Expected Value, 2: Rule-Based, 3: Random): "
        )

        if strategy_choice == "1":
            strategies[name] = ExpectedValueStrategy()
        elif strategy_choice == "2":
            strategies[name] = RuleBasedStrategy()
        else:
            strategies[name] = RandomStrategy()

        game.add_player(name)

    # Play the game
    print("\nStarting game...\n")

    while not game.is_game_over():
        current_player = game.current_player()
        print(f"\nCurrent player: {current_player.name}")

        # First roll is automatic
        dice = game.roll_dice()
        print(f"Roll #1: {dice}")

        # Use strategy for rerolls and scoring
        strategy = strategies[current_player.name]

        # Second roll
        if game.roll_count < 3:
            dice_to_keep = strategy.select_dice_to_keep(dice, current_player.scorecard)
            kept_indices = ", ".join(str(i + 1) for i in dice_to_keep)
            print(f"Keeping dice at positions: {kept_indices or 'none'}")

            dice = game.roll_dice(dice_to_keep)
            print(f"Roll #2: {dice}")

        # Third roll
        if game.roll_count < 3:
            dice_to_keep = strategy.select_dice_to_keep(dice, current_player.scorecard)
            kept_indices = ", ".join(str(i + 1) for i in dice_to_keep)
            print(f"Keeping dice at positions: {kept_indices or 'none'}")

            dice = game.roll_dice(dice_to_keep)
            print(f"Roll #3: {dice}")

        # Score the roll
        category = strategy.select_category(dice, current_player.scorecard)
        score = current_player.scorecard.calculate_score(category, dice)
        print(f"Scoring {score} in {category}")

        game.select_score(category)

    # Game over - show results
    print("\nGame over!")
    for player in game.players:
        print(f"{player.name}: {player.get_total_score()} points")

    winner = game.determine_winner()
    print(f"\nThe winner is {winner}!")


if __name__ == "__main__":
    main()
