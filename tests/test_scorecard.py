import unittest
from src.game.scorecard import Scorecard

class TestScorecard(unittest.TestCase):
    def setUp(self):
        self.scorecard = Scorecard()

    def test_initial_scores(self):
        for category in self.scorecard.scores:
            self.assertIsNone(self.scorecard.get_score(category))
    
    def test_set_and_get_score(self):
        self.scorecard.set_score("Ones", 3)
        self.assertEqual(self.scorecard.get_score("Ones"), 3)
        
        # Try setting an already scored category
        with self.assertRaises(ValueError):
            self.scorecard.set_score("Ones", 4)
            
        # Try setting an invalid category
        with self.assertRaises(ValueError):
            self.scorecard.set_score("Invalid Category", 5)
    
    def test_get_total_score_without_bonus(self):
        # Set some scores but not enough for a bonus
        self.scorecard.set_score("Ones", 3)
        self.scorecard.set_score("Twos", 6)
        self.scorecard.set_score("Threes", 9)
        self.scorecard.set_score("Yahtzee", 50)
        
        # Calculate expected score
        expected_score = 3 + 6 + 9 + 50
        self.assertEqual(self.scorecard.get_total_score(), expected_score)
    
    def test_get_total_score_with_bonus(self):
        # Set scores to get the bonus (≥ 63 in upper section)
        self.scorecard.set_score("Ones", 3)
        self.scorecard.set_score("Twos", 8)
        self.scorecard.set_score("Threes", 12)
        self.scorecard.set_score("Fours", 16)
        self.scorecard.set_score("Fives", 15)
        self.scorecard.set_score("Sixes", 12)
        self.scorecard.set_score("Yahtzee", 50)
        
        # Calculate expected score (including 35 bonus)
        expected_score = 3 + 8 + 12 + 16 + 15 + 12 + 50 + 35
        self.assertEqual(self.scorecard.get_total_score(), expected_score)
    
    def test_is_complete(self):
        # Initially not complete
        self.assertFalse(self.scorecard.is_complete())
        
        # Set all scores
        categories = list(self.scorecard.scores.keys())
        for i, category in enumerate(categories):
            self.scorecard.set_score(category, i)
        
        # Now it should be complete
        self.assertTrue(self.scorecard.is_complete())
    
    def test_calculate_score_upper_section(self):
        # Test Ones
        self.assertEqual(self.scorecard.calculate_score("Ones", [1, 1, 2, 3, 4]), 2)
        # Test Twos  
        self.assertEqual(self.scorecard.calculate_score("Twos", [1, 2, 2, 3, 4]), 4)
        # Test Threes
        self.assertEqual(self.scorecard.calculate_score("Threes", [1, 2, 3, 3, 4]), 6)
        # Test Fours
        self.assertEqual(self.scorecard.calculate_score("Fours", [1, 4, 4, 4, 5]), 12)
        # Test Fives
        self.assertEqual(self.scorecard.calculate_score("Fives", [1, 2, 5, 5, 5]), 15)
        # Test Sixes
        self.assertEqual(self.scorecard.calculate_score("Sixes", [6, 6, 6, 6, 2]), 24)
    
    def test_calculate_score_three_of_a_kind(self):
        # Valid three of a kind
        self.assertEqual(self.scorecard.calculate_score("Three of a Kind", [3, 3, 3, 4, 5]), 18)
        # Not a three of a kind
        self.assertEqual(self.scorecard.calculate_score("Three of a Kind", [1, 2, 3, 4, 5]), 0)
        # Four of a kind also counts as three of a kind
        self.assertEqual(self.scorecard.calculate_score("Three of a Kind", [2, 2, 2, 2, 5]), 13)
    
    def test_calculate_score_four_of_a_kind(self):
        # Valid four of a kind
        self.assertEqual(self.scorecard.calculate_score("Four of a Kind", [4, 4, 4, 4, 5]), 21)
        # Not a four of a kind
        self.assertEqual(self.scorecard.calculate_score("Four of a Kind", [1, 1, 1, 2, 3]), 0)
        # Yahtzee also counts as four of a kind
        self.assertEqual(self.scorecard.calculate_score("Four of a Kind", [6, 6, 6, 6, 6]), 30)
    
    def test_calculate_score_full_house(self):
        # Valid full house
        self.assertEqual(self.scorecard.calculate_score("Full House", [2, 2, 3, 3, 3]), 25)
        # Not a full house
        self.assertEqual(self.scorecard.calculate_score("Full House", [1, 2, 3, 4, 5]), 0)
        self.assertEqual(self.scorecard.calculate_score("Full House", [2, 2, 2, 2, 3]), 0)
    
    def test_calculate_score_small_straight(self):
        # Valid small straights
        self.assertEqual(self.scorecard.calculate_score("Small Straight", [1, 2, 3, 4, 6]), 30)
        self.assertEqual(self.scorecard.calculate_score("Small Straight", [2, 3, 4, 5, 5]), 30)
        self.assertEqual(self.scorecard.calculate_score("Small Straight", [3, 4, 5, 6, 6]), 30)
        # Not a small straight
        self.assertEqual(self.scorecard.calculate_score("Small Straight", [1, 2, 3, 5, 6]), 0)
        self.assertEqual(self.scorecard.calculate_score("Small Straight", [1, 1, 2, 3, 4]), 30)  # Still valid with duplicates
    
    def test_calculate_score_large_straight(self):
        # Valid large straights
        self.assertEqual(self.scorecard.calculate_score("Large Straight", [1, 2, 3, 4, 5]), 40)
        self.assertEqual(self.scorecard.calculate_score("Large Straight", [2, 3, 4, 5, 6]), 40)
        # Not a large straight
        self.assertEqual(self.scorecard.calculate_score("Large Straight", [1, 2, 3, 4, 6]), 0)
        self.assertEqual(self.scorecard.calculate_score("Large Straight", [1, 2, 2, 3, 4, 5]), 0)  # Duplicates make it invalid
    
    def test_calculate_score_yahtzee(self):
        # Valid yahtzee
        self.assertEqual(self.scorecard.calculate_score("Yahtzee", [4, 4, 4, 4, 4]), 50)
        # Not a yahtzee
        self.assertEqual(self.scorecard.calculate_score("Yahtzee", [1, 1, 1, 1, 2]), 0)
    
    def test_calculate_score_chance(self):
        # Chance is just the sum of all dice
        self.assertEqual(self.scorecard.calculate_score("Chance", [1, 2, 3, 4, 5]), 15)
        self.assertEqual(self.scorecard.calculate_score("Chance", [6, 6, 6, 6, 6]), 30)

if __name__ == '__main__':
    unittest.main()
