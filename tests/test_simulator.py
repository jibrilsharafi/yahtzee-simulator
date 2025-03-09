import unittest
from unittest.mock import MagicMock, patch

from src.game.player import Player
from src.game.scorecard import Scorecard
from src.game.yahtzee_game import YahtzeeGame
from src.simulation.simulator import Simulator
from src.strategies.base_strategy import BaseStrategy


class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.simulator = Simulator()
        self.mock_strategy = MagicMock(spec=BaseStrategy)
        self.mock_player = MagicMock(spec=Player)
        self.mock_player.scorecard = MagicMock(spec=Scorecard)

        self.game_state = {
            "current_player": self.mock_player,
            "current_roll": [1, 2, 3, 4, 5],
            "roll_count": 1,
            "turn": 1,
        }

        self.dice_roll = [2, 2, 3, 4, 6]

    def test_init(self):
        self.assertEqual(self.simulator.results, [])

    def test_run_simulation(self):
        # Set up mocks
        self.mock_strategy.select_dice_to_keep.return_value = {
            0,
            1,
        }  # Keep first two dice
        self.mock_strategy.select_category.return_value = "Twos"
        self.mock_player.scorecard.calculate_score.return_value = (
            4  # Two 2's = 4 points
        )

        # Run the simulation
        dice_to_keep, category = self.simulator.run_simulation(
            self.mock_strategy, self.game_state, self.dice_roll
        )

        # Verify the strategy methods were called correctly
        self.mock_strategy.select_dice_to_keep.assert_called_once_with(
            self.dice_roll, self.mock_player.scorecard
        )
        self.mock_strategy.select_category.assert_called_once_with(
            self.dice_roll, self.mock_player.scorecard
        )

        # Verify the result
        self.assertEqual(dice_to_keep, {0, 1})
        self.assertEqual(category, "Twos")

        # Verify the result was recorded
        self.assertEqual(len(self.simulator.results), 1)
        result = self.simulator.results[0]
        self.assertEqual(result["dice_roll"], self.dice_roll)
        self.assertEqual(result["kept_dice"], {0, 1})
        self.assertEqual(result["category"], "Twos")
        self.assertEqual(result["potential_score"], 4)

    def test_get_results(self):
        # Add some test results
        self.simulator.results = [{"test": "data1"}, {"test": "data2"}]

        # Check that get_results returns the results
        self.assertEqual(
            self.simulator.get_results(), [{"test": "data1"}, {"test": "data2"}]
        )


if __name__ == "__main__":
    unittest.main()
