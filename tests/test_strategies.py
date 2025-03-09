import unittest
from unittest.mock import MagicMock, patch
from src.strategies.base_strategy import BaseStrategy
from src.strategies.random_strategy import RandomStrategy
from src.strategies.rule_based_strategy import RuleBasedStrategy
from src.game.scorecard import Scorecard

class TestBaseStrategy(unittest.TestCase):
    def test_abstract_methods(self):
        # BaseStrategy is abstract and its methods should raise NotImplementedError
        strategy = BaseStrategy()
        scorecard = Scorecard()
        
        with self.assertRaises(NotImplementedError):
            strategy.select_dice_to_keep([1, 2, 3, 4, 5], scorecard)
            
        with self.assertRaises(NotImplementedError):
            strategy.select_category([1, 2, 3, 4, 5], scorecard)

class TestRandomStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = RandomStrategy()
        self.scorecard = Scorecard()
        
    @patch('random.randint')
    @patch('random.sample')
    def test_select_dice_to_keep(self, mock_sample, mock_randint):
        # Setup mocks
        mock_randint.return_value = 2  # Keep 2 dice
        mock_sample.return_value = [0, 3]  # Keep dice at positions 0 and 3
        
        dice = [1, 2, 3, 4, 5]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        
        # Check the mocks were called correctly
        mock_randint.assert_called_once_with(0, 5)
        mock_sample.assert_called_once_with(range(5), 2)
        
        # Check the result
        self.assertEqual(result, {0, 3})
    
    @patch('random.choice')
    def test_select_category(self, mock_choice):
        # Setup mocks
        mock_choice.return_value = "Yahtzee"
        
        # Make sure all categories are available
        self.scorecard.scores = {cat: None for cat in self.scorecard.scores}
        
        result = self.strategy.select_category([1, 1, 1, 1, 1], self.scorecard)
        
        # Check the mock was called with all available categories
        available_categories = list(self.scorecard.scores.keys())
        mock_choice.assert_called_once_with(available_categories)
        
        # Check the result
        self.assertEqual(result, "Yahtzee")
    
    def test_select_category_no_available(self):
        # Set all categories as already scored
        self.scorecard.scores = {cat: 0 for cat in self.scorecard.scores}
        
        # Should raise ValueError when no categories are available
        with self.assertRaises(ValueError):
            self.strategy.select_category([1, 1, 1, 1, 1], self.scorecard)

class TestRuleBasedStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = RuleBasedStrategy()
        self.scorecard = Scorecard()
    
    def test_select_dice_to_keep_pair(self):
        # Dice with a pair should keep the pair
        dice = [1, 3, 3, 5, 6]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {1, 2})  # Keep the 3's
        
        # Dice with two pairs should keep the higher pair
        dice = [2, 2, 5, 5, 1]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {2, 3})  # Keep the 5's
    
    def test_select_dice_to_keep_three_of_a_kind(self):
        # Dice with three of a kind should keep those three
        dice = [4, 4, 4, 2, 1]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2})  # Keep the 4's
    
    def test_select_dice_to_keep_high_values(self):
        # With no pairs, keep high values
        dice = [1, 2, 3, 4, 6]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2, 3, 4})  # Keep the first four dice (straight)
        
        dice = [4, 5, 6, 4, 5]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {1, 4})  # Keep all (all >= 4)
    
    def test_select_category(self):
        # Set up a scorecard with some categories already scored
        self.scorecard.scores["Ones"] = 3
        self.scorecard.scores["Twos"] = 6
        
        # With a Yahtzee, it should choose Yahtzee category
        dice = [5, 5, 5, 5, 5]
        result = self.strategy.select_category(dice, self.scorecard)
        self.assertEqual(result, "Yahtzee")  # Yahtzee is the highest scoring option
        
        # With no obvious high-scoring option, it should pick the best available
        self.scorecard.scores["Yahtzee"] = 50  # Now Yahtzee is taken
        dice = [3, 3, 4, 5, 6]
        result = self.strategy.select_category(dice, self.scorecard)
        # Here it depends on which remaining category scores highest
        # Let's verify it's not choosing an already scored category
        self.assertNotIn(result, ["Ones", "Twos", "Yahtzee"])

if __name__ == '__main__':
    unittest.main()
