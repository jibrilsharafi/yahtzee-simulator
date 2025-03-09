import unittest
from src.strategies.rule_based_strategy import RuleBasedStrategy
from src.strategies.random_strategy import RandomStrategy

class TestStrategies(unittest.TestCase):

    def setUp(self):
        self.rule_based_strategy = RuleBasedStrategy()
        self.random_strategy = RandomStrategy()

    def test_rule_based_strategy(self):
        # Test the rule-based strategy with a sample dice roll
        current_status = {
            'scorecard': {},  # Add relevant scorecard state
            'rolled_dice': [1, 2, 3, 4, 5],  # Example roll
            'player': 'Player 1'  # Example player
        }
        keep_dice, score = self.rule_based_strategy.select_dice_to_keep(current_status)
        # Add assertions based on expected behavior
        self.assertIsInstance(keep_dice, list)
        self.assertIsInstance(score, int)

    def test_random_strategy(self):
        # Test the random strategy with a sample dice roll
        current_status = {
            'scorecard': {},  # Add relevant scorecard state
            'rolled_dice': [1, 2, 3, 4, 5],  # Example roll
            'player': 'Player 1'  # Example player
        }
        keep_dice, score = self.random_strategy.select_dice_to_keep(current_status)
        # Add assertions based on expected behavior
        self.assertIsInstance(keep_dice, list)
        self.assertIsInstance(score, int)

if __name__ == '__main__':
    unittest.main()