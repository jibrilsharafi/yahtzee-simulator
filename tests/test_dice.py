import unittest
from unittest.mock import patch
from src.game.dice import Dice

class TestDice(unittest.TestCase):
    def setUp(self):
        self.dice = Dice()
    
    def test_init_default_values(self):
        self.assertEqual(len(self.dice.values), 5)
        self.assertEqual(self.dice.num_dice, 5)
        for value in self.dice.values:
            self.assertEqual(value, 1)
    
    def test_init_custom_dice_count(self):
        custom_dice = Dice(3)
        self.assertEqual(len(custom_dice.values), 3)
        self.assertEqual(custom_dice.num_dice, 3)
    
    @patch('random.randint')
    def test_roll_all_dice(self, mock_randint):
        # Set up mock to return specific values
        mock_randint.side_effect = [3, 4, 2, 6, 1]
        
        result = self.dice.roll()
        
        # Check that random.randint was called 5 times with the right args
        self.assertEqual(mock_randint.call_count, 5)
        mock_randint.assert_called_with(1, 6)
        
        # Check that values were updated correctly
        self.assertEqual(result, [3, 4, 2, 6, 1])
        self.assertEqual(self.dice.values, [3, 4, 2, 6, 1])
    
    @patch('random.randint')
    def test_roll_specific_dice(self, mock_randint):
        # Set initial values
        self.dice.values = [1, 2, 3, 4, 5]
        
        # Set up mock for the two dice we're going to roll
        mock_randint.side_effect = [6, 6]
        
        # Roll only indices 0 and 2
        result = self.dice.roll({0, 2})
        
        # Check that random.randint was called twice
        self.assertEqual(mock_randint.call_count, 2)
        
        # Check that only specified dice were changed
        self.assertEqual(result, [6, 2, 6, 4, 5])
        self.assertEqual(self.dice.values, [6, 2, 6, 4, 5])
    
    @patch('random.randint')
    def test_roll_out_of_range_indices(self, mock_randint):
        # Set initial values
        self.dice.values = [1, 2, 3, 4, 5]
        
        # Set up mock
        mock_randint.side_effect = [6]
        
        # Try to roll an out-of-range index and a valid index
        result = self.dice.roll({-1, 10, 2})
        
        # Should only roll the valid index
        self.assertEqual(mock_randint.call_count, 1)
        self.assertEqual(result, [1, 2, 6, 4, 5])
    
    def test_get_values(self):
        self.dice.values = [2, 3, 5, 6, 1]
        self.assertEqual(self.dice.get_values(), [2, 3, 5, 6, 1])

if __name__ == '__main__':
    unittest.main()
