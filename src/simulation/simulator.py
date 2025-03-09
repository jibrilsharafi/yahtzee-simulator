from typing import List, Dict, Any, Tuple, Set
from src.strategies.base_strategy import BaseStrategy
from src.game.yahtzee_game import YahtzeeGame


class Simulator:
    def __init__(self) -> None:
        self.results: List[Dict[str, Any]] = []

    def run_simulation(
        self, strategy: BaseStrategy, game_state: Dict[str, Any], dice_roll: List[int]
    ) -> Tuple[Set[int], str]:
        """
        Run a single simulation step using the provided strategy.

        :param strategy: Strategy to use for decision making.
        :param game_state: Current state of the game.
        :param dice_roll: Current dice values.
        :return: Tuple of (dice to keep, selected category)
        """
        dice_to_keep = strategy.select_dice_to_keep(
            dice_roll, game_state["current_player"].scorecard
        )
        category = strategy.select_category(
            dice_roll, game_state["current_player"].scorecard
        )

        self.results.append(
            {
                "dice_roll": dice_roll,
                "kept_dice": dice_to_keep,
                "category": category,
                "potential_score": game_state[
                    "current_player"
                ].scorecard.calculate_score(category, dice_roll),
            }
        )

        return dice_to_keep, category

    def run_game_simulation(
        self, num_games: int, strategies: Dict[str, BaseStrategy]
    ) -> Dict[str, int]:
        """
        Run multiple complete games and track wins.

        :param num_games: Number of games to simulate.
        :param strategies: Dictionary mapping player names to strategies.
        :return: Dictionary of win counts by player.
        """
        wins: Dict[str, int] = {player: 0 for player in strategies}

        for _ in range(num_games):
            game = YahtzeeGame()
            for player_name in strategies:
                game.add_player(player_name)

            game.play_game(strategies)
            winner = game.determine_winner()
            wins[winner] = wins.get(winner, 0) + 1

        return wins

    def get_results(self) -> List[Dict[str, Any]]:
        return self.results
