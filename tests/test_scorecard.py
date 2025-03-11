import unittest
from src.game.scorecard import Scorecard, ScorecardCategory


class TestScorecard(unittest.TestCase):
    def setUp(self):
        self.scorecard = Scorecard()

    def test_initial_scores(self):
        for category in self.scorecard.scores:
            self.assertIsNone(self.scorecard.get_score(category))

    def test_set_and_get_score(self):
        self.scorecard.set_score(ScorecardCategory.ONES, [1, 1, 1, 2, 2])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.ONES), 3)

        # Try setting an already scored category
        with self.assertRaises(ValueError):
            self.scorecard.set_score(ScorecardCategory.ONES, [4])

        # Try setting an invalid category
        with self.assertRaises(ValueError):
            # Create a value that isn't in the Enum
            self.scorecard.set_score("Invalid Category", [5])

    def test_get_total_score_without_bonus(self):
        # Set some scores but not enough for a bonus
        self.scorecard.set_score(ScorecardCategory.ONES, [1, 1, 1, 2, 2])
        self.scorecard.set_score(ScorecardCategory.TWOS, [2, 2, 2, 3, 3])
        self.scorecard.set_score(ScorecardCategory.THREES, [3, 3, 3, 4, 4])
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [5, 5, 5, 5, 5])

        # Calculate expected score
        expected_score = 3 + 6 + 9 + 50
        self.assertEqual(self.scorecard.get_total_score(), expected_score)

    def test_get_total_score_with_bonus(self):
        # Set scores to get the bonus (≥ 63 in upper section)
        self.scorecard.set_score(ScorecardCategory.ONES, [1, 1, 1, 2, 2])
        self.scorecard.set_score(ScorecardCategory.TWOS, [2, 2, 2, 2, 3])
        self.scorecard.set_score(ScorecardCategory.THREES, [3, 3, 3, 3, 4])
        self.scorecard.set_score(ScorecardCategory.FOURS, [4, 4, 4, 4, 5])
        self.scorecard.set_score(ScorecardCategory.FIVES, [5, 5, 5, 3, 4])
        self.scorecard.set_score(ScorecardCategory.SIXES, [6, 6, 1, 2, 3])
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [5, 5, 5, 5, 5])

        # Calculate expected score (including 35 bonus)
        expected_score = 3 + 8 + 12 + 16 + 15 + 12 + 50 + 35
        self.assertEqual(self.scorecard.get_total_score(), expected_score)

    def test_is_complete(self):
        # Initially not complete
        self.assertFalse(self.scorecard.is_complete())

        # Set all scores
        categories = list(self.scorecard.scores.keys())
        for i, category in enumerate(categories):
            self.scorecard.set_score(category, [i + 1] * 5)

        # Now it should be complete
        self.assertTrue(self.scorecard.is_complete())

    def test_calculate_score_upper_section(self):
        # Test Ones
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.ONES, [1, 1, 2, 3, 4]), 2
        )
        # Test Twos
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.TWOS, [1, 2, 2, 3, 4]), 4
        )
        # Test Threes
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.THREES, [1, 2, 3, 3, 4]), 6
        )
        # Test Fours
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.FOURS, [1, 4, 4, 4, 5]), 12
        )
        # Test Fives
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.FIVES, [1, 2, 5, 5, 5]), 15
        )
        # Test Sixes
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.SIXES, [6, 6, 6, 6, 2]), 24
        )

    def test_calculate_score_three_of_a_kind(self):
        # Valid three of a kind
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.THREE_OF_A_KIND, [3, 3, 3, 4, 5]
            ),
            18,
        )
        # Not a three of a kind
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.THREE_OF_A_KIND, [1, 2, 3, 4, 5]
            ),
            0,
        )
        # Four of a kind also counts as three of a kind
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.THREE_OF_A_KIND, [2, 2, 2, 2, 5]
            ),
            13,
        )

    def test_calculate_score_four_of_a_kind(self):
        # Valid four of a kind
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.FOUR_OF_A_KIND, [4, 4, 4, 4, 5]
            ),
            21,
        )
        # Not a four of a kind
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.FOUR_OF_A_KIND, [1, 1, 1, 2, 3]
            ),
            0,
        )
        # Yahtzee also counts as four of a kind
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.FOUR_OF_A_KIND, [6, 6, 6, 6, 6]
            ),
            30,
        )

    def test_calculate_score_full_house(self):
        # Valid full house
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.FULL_HOUSE, [2, 2, 3, 3, 3]
            ),
            25,
        )
        # Not a full house
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.FULL_HOUSE, [1, 2, 3, 4, 5]
            ),
            0,
        )
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.FULL_HOUSE, [2, 2, 2, 2, 3]
            ),
            0,
        )

    def test_calculate_score_small_straight(self):
        # Valid small straights
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.SMALL_STRAIGHT, [1, 2, 3, 4, 6]
            ),
            30,
        )
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.SMALL_STRAIGHT, [2, 3, 4, 5, 5]
            ),
            30,
        )
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.SMALL_STRAIGHT, [3, 4, 5, 6, 6]
            ),
            30,
        )
        # Not a small straight
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.SMALL_STRAIGHT, [1, 2, 3, 5, 6]
            ),
            0,
        )
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.SMALL_STRAIGHT, [1, 1, 2, 3, 4]
            ),
            30,
        )  # Still valid with duplicates

    def test_calculate_score_large_straight(self):
        # Valid large straights
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.LARGE_STRAIGHT, [1, 2, 3, 4, 5]
            ),
            40,
        )
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.LARGE_STRAIGHT, [2, 3, 4, 5, 6]
            ),
            40,
        )
        # Not a large straight
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.LARGE_STRAIGHT, [1, 2, 3, 4, 6]
            ),
            0,
        )
        self.assertEqual(
            self.scorecard.calculate_score(
                ScorecardCategory.LARGE_STRAIGHT, [1, 2, 2, 3, 4, 5]
            ),
            0,
        )  # Extra dice make it invalid

    def test_calculate_score_yahtzee(self):
        # Valid yahtzee
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.YAHTZEE, [4, 4, 4, 4, 4]),
            50,
        )
        # Not a yahtzee
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.YAHTZEE, [1, 1, 1, 1, 2]),
            0,
        )

    def test_calculate_score_chance(self):
        # Chance is just the sum of all dice
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.CHANCE, [1, 2, 3, 4, 5]),
            15,
        )
        self.assertEqual(
            self.scorecard.calculate_score(ScorecardCategory.CHANCE, [6, 6, 6, 6, 6]),
            30,
        )

    def test_yahtzee_bonus_scoring(self):
        """Test that Yahtzee bonuses are correctly scored."""
        # First score a regular Yahtzee
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [5, 5, 5, 5, 5])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.YAHTZEE), 50)
        self.assertEqual(self.scorecard.yahtzee_bonus_count, 0)

        # Score another category using another Yahtzee roll
        # This should register a Yahtzee bonus
        self.scorecard.set_score(ScorecardCategory.FIVES, [5, 5, 5, 5, 5])
        self.assertEqual(self.scorecard.yahtzee_bonus_count, 1)
        self.assertEqual(self.scorecard.get_yahtzee_bonus_score(), 100)

        # Score another Yahtzee roll
        self.scorecard.set_score(ScorecardCategory.SIXES, [6, 6, 6, 6, 6])
        self.assertEqual(self.scorecard.yahtzee_bonus_count, 2)
        self.assertEqual(self.scorecard.get_yahtzee_bonus_score(), 200)

        # Verify the total score includes Yahtzee bonuses
        expected_score = 50 + 25 + 30 + 200  # Yahtzee + Fives + Chance + bonuses
        self.assertEqual(self.scorecard.get_total_score(), expected_score)

    def test_no_yahtzee_bonus_when_yahtzee_scored_zero(self):
        """Test that no Yahtzee bonus is awarded if Yahtzee was scored 0."""
        # Score a zero in Yahtzee (using non-Yahtzee roll)
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [1, 2, 3, 4, 5])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.YAHTZEE), 0)

        # Try to score a Yahtzee in another category
        self.scorecard.set_score(ScorecardCategory.SIXES, [6, 6, 6, 6, 6])
        self.assertEqual(self.scorecard.yahtzee_bonus_count, 0)
        self.assertEqual(self.scorecard.get_yahtzee_bonus_score(), 0)

    def test_get_mandatory_category(self):
        """Test that get_mandatory_category returns the correct category."""
        # No mandatory category when not a Yahtzee roll
        self.assertIsNone(self.scorecard.get_mandatory_category([1, 2, 3, 4, 5]))

        # No mandatory category when Yahtzee category not yet scored
        self.assertIsNone(self.scorecard.get_mandatory_category([3, 3, 3, 3, 3]))

        # Score the Yahtzee category
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [4, 4, 4, 4, 4])

        # Now have a Yahtzee joker - should require the matching upper section
        self.assertEqual(
            self.scorecard.get_mandatory_category([2, 2, 2, 2, 2]),
            ScorecardCategory.TWOS,
        )

        # Fill the matching upper section
        self.scorecard.set_score(ScorecardCategory.TWOS, [2, 2, 2, 2, 2])

        # No mandatory category since the matching upper section is filled
        self.assertIsNone(self.scorecard.get_mandatory_category([2, 2, 2, 2, 2]))

    def test_yahtzee_joker_rule_enforcement(self):
        """Test that Yahtzee joker rules are enforced in set_score."""
        # First score a regular Yahtzee
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [6, 6, 6, 6, 6])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.YAHTZEE), 50)

        # Try to score a Yahtzee joker in a category other than the matching upper section
        with self.assertRaises(ValueError):
            self.scorecard.set_score(ScorecardCategory.CHANCE, [3, 3, 3, 3, 3])

        # Score in the mandatory upper section first
        self.scorecard.set_score(ScorecardCategory.THREES, [3, 3, 3, 3, 3])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.THREES), 15)
        self.assertEqual(self.scorecard.yahtzee_bonus_count, 1)

        # Fill the fours
        self.scorecard.set_score(ScorecardCategory.FOURS, [4, 1, 2, 3, 5])

        # Now with the matching upper section filled, should be able to score anywhere
        self.scorecard.set_score(ScorecardCategory.CHANCE, [4, 4, 4, 4, 4])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.CHANCE), 20)
        self.assertEqual(self.scorecard.yahtzee_bonus_count, 2)

    def test_yahtzee_joker_scoring_rules(self):
        """Test scoring rules for Yahtzee jokers in different categories."""
        # First score a Yahtzee
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [5, 5, 5, 5, 5])

        # Fill the matching upper section first
        self.scorecard.set_score(ScorecardCategory.ONES, [1, 1, 2, 3, 4])
        self.scorecard.set_score(ScorecardCategory.TWOS, [2, 2, 2, 3, 4])
        self.scorecard.set_score(ScorecardCategory.THREES, [3, 3, 3, 4, 5])
        self.scorecard.set_score(ScorecardCategory.FOURS, [4, 4, 3, 4, 5])
        self.scorecard.set_score(ScorecardCategory.FIVES, [5, 5, 5, 5, 5]) # Yahtzee joker
        self.scorecard.set_score(ScorecardCategory.SIXES, [6, 6, 1, 2, 3])
    
        # Three of a kind should score sum of all dice
        self.scorecard.set_score(ScorecardCategory.THREE_OF_A_KIND, [6, 6, 6, 6, 6])
        self.assertEqual(
            self.scorecard.get_score(ScorecardCategory.THREE_OF_A_KIND), 30
        )

        # Four of a kind should score sum of all dice
        self.scorecard.set_score(ScorecardCategory.FOUR_OF_A_KIND, [4, 4, 4, 4, 4])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.FOUR_OF_A_KIND), 20)

        # Full house should score 25
        self.scorecard.set_score(ScorecardCategory.FULL_HOUSE, [3, 3, 3, 3, 3])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.FULL_HOUSE), 25)

        # Small straight should score 30
        self.scorecard.set_score(ScorecardCategory.SMALL_STRAIGHT, [2, 2, 2, 2, 2])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.SMALL_STRAIGHT), 30)

        # Large straight should score 40
        self.scorecard.set_score(ScorecardCategory.LARGE_STRAIGHT, [1, 1, 1, 1, 1])
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.LARGE_STRAIGHT), 40)

        # Check total Yahtzee bonuses
        self.assertEqual(self.scorecard.yahtzee_bonus_count, 6)
        self.assertEqual(self.scorecard.get_yahtzee_bonus_score(), 600)


if __name__ == "__main__":
    unittest.main()
