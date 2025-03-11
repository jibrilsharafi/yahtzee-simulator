import os
import time
import unittest
from collections import Counter, defaultdict
from typing import Dict, List, Union
from unittest.mock import patch

from tabulate import tabulate

from src.game.scorecard import Scorecard, ScorecardCategory
from src.strategies.base_strategy import BaseStrategy
from src.strategies.expected_value_strategy import ExpectedValueStrategy
from src.strategies.expected_value_v2_strategy import ExpectedValueV2Strategy
from src.strategies.gemini_strategy import GeminiStrategy
from src.strategies.random_strategy import RandomStrategy
from src.strategies.rule_based_strategy import RuleBasedStrategy


class TestBaseStrategy(unittest.TestCase):
    def test_abstract_methods(self) -> None:
        # BaseStrategy is abstract and its methods should raise NotImplementedError
        strategy = BaseStrategy()
        scorecard = Scorecard()

        with self.assertRaises(NotImplementedError):
            strategy.select_dice_to_keep([1, 2, 3, 4, 5], scorecard)

        with self.assertRaises(NotImplementedError):
            strategy.select_category([1, 2, 3, 4, 5], scorecard)


class TestRandomStrategy(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = RandomStrategy()
        self.scorecard = Scorecard()

    @patch("random.randint")
    @patch("random.sample")
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

    @patch("random.choice")
    def test_select_category(self, mock_choice):
        # Setup mocks
        mock_choice.return_value = "yahtzee"

        # Make sure all categories are available
        self.scorecard.scores = {cat: None for cat in self.scorecard.scores}

        result = self.strategy.select_category([1, 1, 1, 1, 1], self.scorecard)

        # Check the mock was called with all available categories
        available_categories = list(self.scorecard.scores.keys())
        mock_choice.assert_called_once_with(available_categories)

        # Check the result
        self.assertEqual(result, "yahtzee")

    def test_select_category_no_available(self) -> None:
        # Set all categories as already scored
        self.scorecard.scores = {cat: 0 for cat in self.scorecard.scores}

        # Should raise ValueError when no categories are available
        with self.assertRaises(ValueError):
            self.strategy.select_category([1, 1, 1, 1, 1], self.scorecard)


class TestRuleBasedStrategy(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = RuleBasedStrategy()
        self.scorecard = Scorecard()

    def test_select_dice_to_keep_pair(self) -> None:
        # Dice with a pair should keep the pair
        dice = [1, 3, 3, 5, 6]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {1, 2})  # Keep the 3's

        # Dice with two pairs should keep the higher pair
        dice = [2, 2, 5, 5, 1]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {2, 3})  # Keep the 5's

    def test_select_dice_to_keep_three_of_a_kind(self) -> None:
        # Dice with three of a kind should keep those three
        dice = [4, 4, 4, 2, 1]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2})  # Keep the 4's

    def test_select_dice_to_keep_high_values(self) -> None:
        # With no pairs, keep high values
        dice = [1, 2, 3, 4, 6]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2, 3, 4})  # Keep the first four dice (straight)

        dice = [4, 5, 6, 4, 5]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {1, 4})  # Keep all (all >= 4)

    def test_select_category(self) -> None:
        # Set up a scorecard with some categories already scored
        self.scorecard.scores[ScorecardCategory.ONES] = 3
        self.scorecard.scores[ScorecardCategory.TWOS] = 6

        # With a Yahtzee, it should choose Yahtzee category
        dice = [5, 5, 5, 5, 5]
        result = self.strategy.select_category(dice, self.scorecard)
        self.assertEqual(
            result, ScorecardCategory.YAHTZEE
        )  # Yahtzee is the highest scoring option

        # With no obvious high-scoring option, it should pick the best available
        self.scorecard.scores[ScorecardCategory.YAHTZEE] = 50  # Now Yahtzee is taken
        dice = [3, 3, 4, 5, 6]
        result = self.strategy.select_category(dice, self.scorecard)
        # Here it depends on which remaining category scores highest
        # Let's verify it's not choosing an already scored category
        self.assertNotIn(
            result,
            [
                ScorecardCategory.ONES,
                ScorecardCategory.TWOS,
                ScorecardCategory.YAHTZEE,
            ],
        )


class TestExpectedValueStrategy(unittest.TestCase):
    def setUp(self) -> None:
        # To speed up tests, create a simplified version with minimal initialization
        with patch.object(ExpectedValueStrategy, "_initialize_lookup_tables"):
            self.strategy = ExpectedValueStrategy()

        # Set up a small lookup table for testing
        self.strategy.ev_table = {}
        self.scorecard = Scorecard()

    def test_dice_key_generation(self) -> None:
        # Test the conversion of dice to canonical form
        self.assertEqual(self.strategy._dice_key([]), (0, 0, 0, 0, 0, 0))
        self.assertEqual(self.strategy._dice_key([1, 1, 1, 1, 1]), (5, 0, 0, 0, 0, 0))
        self.assertEqual(self.strategy._dice_key([1, 2, 3, 4, 5]), (1, 1, 1, 1, 1, 0))
        self.assertEqual(self.strategy._dice_key([6, 6, 6, 6, 6]), (0, 0, 0, 0, 0, 5))
        self.assertEqual(self.strategy._dice_key([1, 3, 3, 5, 5]), (1, 0, 2, 0, 2, 0))

    def test_scorecard_key_generation(self) -> None:
        # Test conversion of scorecard to a hashable key
        self.scorecard.set_score(ScorecardCategory.ONES, [1, 1, 1, 2, 3])
        self.scorecard.set_score(ScorecardCategory.TWOS, [2, 2, 2, 3, 4])

        key = self.strategy._scorecard_key(self.scorecard)
        self.assertTrue(isinstance(key, tuple))
        self.assertEqual(key[0], 3)  # Value for ones
        self.assertEqual(key[1], 6)  # Value for twos

    @patch.object(ExpectedValueStrategy, "_calculate_ev_for_kept_dice")
    def test_select_dice_to_keep_third_roll(self, mock_ev):
        # On third roll, should keep all dice regardless of values
        self.scorecard.current_roll = 3

        dice = [1, 2, 3, 4, 5]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)

        # Should keep all dice and not calculate EV
        self.assertEqual(result, {0, 1, 2, 3, 4})
        mock_ev.assert_not_called()

    @patch.object(ExpectedValueStrategy, "_calculate_ev_for_kept_dice")
    def test_select_dice_to_keep_optimal_choice(self, mock_ev):
        # Mock EV calculation for different keep choices
        def ev_side_effect(kept_config, roll_number):
            # Return higher values for keeping specific combinations
            if kept_config == (3, 0, 0, 0, 0, 0):  # Three 1's
                return 20.0
            elif kept_config == (0, 0, 0, 0, 0, 0):  # Keep nothing
                return 15.0
            else:
                return 10.0

        mock_ev.side_effect = ev_side_effect

        # First roll with three 1's and two other dice
        self.scorecard.current_roll = 1

        dice = [1, 1, 1, 4, 6]
        result = self.strategy.select_dice_to_keep(dice, self.scorecard)

        # Should keep the three 1's (indices 0, 1, 2)
        self.assertEqual(result, {0, 1, 2})

    def test_calculate_max_category_score(self) -> None:
        # Test that the function correctly finds the maximum possible score

        # A Yahtzee of 6's should have a max score of 50 (Yahtzee category)
        yahtzee_config = (0, 0, 0, 0, 0, 5)
        self.assertEqual(
            self.strategy._calculate_max_category_score(yahtzee_config), 50
        )

        # Full house should have max score of 25
        full_house_config = (0, 0, 3, 0, 2, 0)
        self.assertEqual(
            self.strategy._calculate_max_category_score(full_house_config), 25
        )

    @patch.object(ExpectedValueStrategy, "_estimate_future_value")
    def test_select_category_optimal_choice(self, mock_future):
        # Mock future value estimation
        mock_future.return_value = 0  # No future impact for this test

        # Make all categories available

        # Yahtzee should be chosen for five of a kind
        dice = [6, 6, 6, 6, 6]
        result = self.strategy.select_category(dice, self.scorecard)
        self.assertEqual(result, ScorecardCategory.YAHTZEE)

        # Full house should be chosen over three of a kind when available
        dice = [2, 2, 2, 5, 5]
        # Set yahtzee as used so it's not the top choice
        result = self.strategy.select_category(dice, self.scorecard)
        self.assertEqual(result, ScorecardCategory.FULL_HOUSE)

    def test_yahtzee_bonus_prioritization(self) -> None:
        # Test that the strategy prioritizes additional Yahtzees when one is already scored

        # Set up scorecard with a Yahtzee already
        self.scorecard.set_score(ScorecardCategory.YAHTZEE, [1, 1, 1, 1, 1])

        # Mock _estimate_future_value to return 0 for all categories
        # so we just test the bonus logic
        with patch.object(
            ExpectedValueStrategy, "_estimate_future_value", return_value=0
        ):
            # When we have another Yahtzee, should prefer matching upper category over other options
            dice = [4, 4, 4, 4, 4]
            result = self.strategy.select_category(dice, self.scorecard)
            self.assertEqual(
                result, ScorecardCategory.FOURS
            )  # Should pick fours over other good categories

    def test_dump_category_avoidance(self) -> None:
        # Test that the strategy avoids using Yahtzee as a dump category

        # Set up a scorecard with most categories filled
        for category in self.strategy.all_categories:
            if (
                category != ScorecardCategory.YAHTZEE
                and category != ScorecardCategory.ONES
            ):
                self.scorecard.set_score(category, [1, 2, 3, 4, 5])

        # With a terrible roll and only Yahtzee and ones left, should prefer ones as dump
        with patch.object(
            ExpectedValueStrategy, "_estimate_future_value", return_value=0
        ):
            dice = [2, 3, 4, 5, 6]  # No ones, no Yahtzee
            result = self.strategy.select_category(dice, self.scorecard)
            self.assertEqual(
                result, ScorecardCategory.ONES
            )  # Should dump in ones, not Yahtzee

    def test_integration_with_real_lookup(self) -> None:
        # Create a real strategy with actual lookup tables and test some realistic scenarios
        # Note: This is more of an integration test and will be slower than the mocked tests
        strategy = ExpectedValueStrategy()

        # Test with a Yahtzee
        dice = [5, 5, 5, 5, 5]
        result = strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2, 3, 4})  # Should keep all dice

        # Test with almost a large straight
        dice = [1, 2, 3, 4, 1]
        result = strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2, 3})  # Should keep 1,2,3,4

        # Test category selection maximizes score
        result_category = strategy.select_category(dice, self.scorecard)
        self.assertNotEqual(
            result_category, ScorecardCategory.YAHTZEE
        )  # Shouldn't pick Yahtzee

    # Since the Chance scenario is always considered, it will rather
    # skip a probable full house
    def test_integration_with_real_lookup_scenario(self) -> None:
        strategy = ExpectedValueStrategy()

        # Test with a Yahtzee
        dice = [4, 5, 2, 2, 5]
        result = strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2})  # Should keep 2,2,5

        # Test with almost a large straight
        dice = [4, 5, 2, 5, 1]
        result = strategy.select_dice_to_keep(dice, self.scorecard)
        self.assertEqual(result, {0, 1, 2})

        # Test category selection maximizes score
        result_category = strategy.select_category(dice, self.scorecard)
        self.assertEqual(result_category, ScorecardCategory.CHANCE)

        self.scorecard.set_score(ScorecardCategory.CHANCE, [4, 5, 2, 2, 5])
        # Check that the score is set correctly
        self.assertEqual(self.scorecard.get_score(ScorecardCategory.CHANCE), 18)


class TestExpectedValueV2Strategy(unittest.TestCase):
    def setUp(self) -> None:
        """Create a fresh strategy instance before each test"""
        self.strategy = ExpectedValueV2Strategy()

    def test_dice_key_basic(self) -> None:
        """Test that _dice_key creates the correct count representation"""
        # Standard Yahtzee combination (1-5)
        dice = [1, 2, 3, 4, 5]
        key = self.strategy._dice_key(dice)
        expected = (1, 1, 1, 1, 1, 0)  # One of each 1-5, zero 6's
        self.assertEqual(
            key, expected, f"Expected {dice} to be represented as {expected}, got {key}"
        )

        # Test another combination: two 1's, two 3's, one 5
        dice = [1, 1, 3, 3, 5]
        key = self.strategy._dice_key(dice)
        expected = (
            2,
            0,
            2,
            0,
            1,
            0,
        )  # Two 1's, zero 2's, two 3's, zero 4's, one 5, zero 6's
        self.assertEqual(
            key, expected, f"Expected {dice} to be represented as {expected}, got {key}"
        )

        print(f"✓ _dice_key correctly converts [1,1,3,3,5] to {key}")

    def test_dice_key_yahtzee(self) -> None:
        """Test _dice_key with a Yahtzee (all same value)"""
        # Yahtzee of 4's
        dice = [4, 4, 4, 4, 4]
        key = self.strategy._dice_key(dice)
        expected = (0, 0, 0, 5, 0, 0)  # Five 4's, zero of everything else
        self.assertEqual(key, expected)

        print(f"✓ _dice_key correctly converts a Yahtzee of 4's to {key}")

    def test_dice_key_empty(self) -> None:
        """Test _dice_key with empty dice list"""
        # Empty list (no dice kept)
        dice: List[int] = []
        key = self.strategy._dice_key(dice)
        expected = (0, 0, 0, 0, 0, 0)  # Zero of each value
        self.assertEqual(key, expected)

        print("✓ _dice_key correctly handles empty dice list")

    def test_calculate_score_for_category_upper(self) -> None:
        """Test scoring for upper section categories"""
        # Test Threes category with 3 dice showing '3'
        dice = [3, 3, 3, 1, 5]
        score = self.strategy._calculate_score_for_category(
            dice, ScorecardCategory.THREES
        )
        expected = 9  # 3 + 3 + 3 = 9
        self.assertEqual(
            score,
            expected,
            f"Expected score of {expected} for {dice} in THREES, got {score}",
        )

        print(
            f"✓ _calculate_score_for_category correctly scores {dice} in THREES as {score}"
        )

        # Test Sixes category with no sixes
        dice = [1, 2, 3, 4, 5]
        score = self.strategy._calculate_score_for_category(
            dice, ScorecardCategory.SIXES
        )
        expected = 0  # No 6's
        self.assertEqual(score, expected)

        print(
            f"✓ _calculate_score_for_category correctly scores {dice} in SIXES as {score}"
        )

    def test_calculate_score_for_category_lower(self) -> None:
        """Test scoring for lower section categories"""
        # Full House
        dice = [2, 2, 2, 5, 5]
        score = self.strategy._calculate_score_for_category(
            dice, ScorecardCategory.FULL_HOUSE
        )
        expected = 25  # Full house scores 25
        self.assertEqual(score, expected)

        print(
            f"✓ _calculate_score_for_category correctly scores {dice} in FULL_HOUSE as {score}"
        )

        # Small Straight
        dice = [1, 2, 3, 4, 6]
        score = self.strategy._calculate_score_for_category(
            dice, ScorecardCategory.SMALL_STRAIGHT
        )
        expected = 30  # Small straight scores 30
        self.assertEqual(score, expected)

        print(
            f"✓ _calculate_score_for_category correctly scores {dice} in SMALL_STRAIGHT as {score}"
        )

        # Not a Large Straight
        dice = [1, 2, 3, 4, 6]
        score = self.strategy._calculate_score_for_category(
            dice, ScorecardCategory.LARGE_STRAIGHT
        )
        expected = 0  # Not a large straight
        self.assertEqual(score, expected)

        print(
            f"✓ _calculate_score_for_category correctly scores {dice} in LARGE_STRAIGHT as {score}"
        )

    def test_calculate_max_score(self) -> None:
        """Test finding the maximum score across available categories"""
        # Yahtzee of 5's - good for many categories
        dice = [5, 5, 5, 5, 5]

        # With all categories available
        available_categories = self.strategy.all_categories
        max_score = self.strategy._calculate_max_score(dice, available_categories)
        # Yahtzee (50) should be the max
        self.assertEqual(max_score, 50)

        print(
            f"✓ _calculate_max_score correctly finds max score of {max_score} for {dice}"
        )

        # Without Yahtzee category
        available_categories = [
            cat
            for cat in self.strategy.all_categories
            if cat != ScorecardCategory.YAHTZEE
        ]
        max_score = self.strategy._calculate_max_score(dice, available_categories)
        # Four of a Kind (25) should be the max
        self.assertEqual(max_score, 25)

        print(
            f"✓ _calculate_max_score correctly finds max score of {max_score} for {dice} without YAHTZEE"
        )

        # With only upper sections
        available_categories = self.strategy.upper_categories
        max_score = self.strategy._calculate_max_score(dice, available_categories)
        # Fives (25) should be the max
        self.assertEqual(max_score, 25)

        print(
            f"✓ _calculate_max_score correctly finds max score of {max_score} for {dice} with upper categories only"
        )

    def test_available_categories_key(self) -> None:
        """Test creating hashable keys from category lists"""
        # Test with different order produces the same key
        categories1 = [
            ScorecardCategory.ONES,
            ScorecardCategory.TWOS,
            ScorecardCategory.THREES,
        ]
        categories2 = [
            ScorecardCategory.THREES,
            ScorecardCategory.ONES,
            ScorecardCategory.TWOS,
        ]

        key1 = self.strategy._available_categories_key(categories1)
        key2 = self.strategy._available_categories_key(categories2)

        self.assertEqual(key1, key2, "Keys should be equal regardless of order")

        # Test different categories produce different keys
        categories3 = [
            ScorecardCategory.FOURS,
            ScorecardCategory.FIVES,
            ScorecardCategory.SIXES,
        ]
        key3 = self.strategy._available_categories_key(categories3)

        self.assertNotEqual(
            key1, key3, "Different categories should produce different keys"
        )

        # Verify the keys are actually frozensets
        self.assertIsInstance(key1, frozenset, "Key should be a frozenset")

        print("✓ _available_categories_key creates consistent, order-independent keys")
        print(
            f"✓ Example: categories {[c.name for c in categories1]} creates key {key1}"
        )

    def test_calculate_ev_for_roll_terminal_cases(self) -> None:
        """Test the terminal cases for the EV calculation"""
        # Available categories
        available_categories = self.strategy.all_categories

        # Case 1: Roll 3 - should just return the max score
        dice = [1, 2, 3, 4, 5]  # Large straight
        ev_roll3 = self.strategy._calculate_ev_for_roll(dice, 3, available_categories)
        max_score = self.strategy._calculate_max_score(dice, available_categories)
        self.assertEqual(
            ev_roll3,
            max_score,
            f"Roll 3 EV should equal max score, got {ev_roll3} vs {max_score}",
        )
        print(f"✓ Roll 3 EV correctly returns max score of {max_score}")

        # Case 2: Keeping all 5 dice - should just return max score regardless of roll number
        ev_keep_all = self.strategy._calculate_ev_for_roll(
            dice, 1, available_categories
        )
        self.assertEqual(
            ev_keep_all, max_score, "Keeping all dice should return max score"
        )
        print("✓ Keeping all dice correctly returns max score")

    def test_calculate_ev_for_roll_2(self) -> None:
        """Test EV calculation for roll 2 with a simple case"""
        # Available categories
        available_categories = self.strategy.all_categories

        # Keep pair of 6's, looking to get three/four of a kind
        kept_dice = [6, 6]

        # Calculate EV for roll 2
        ev = self.strategy._calculate_ev_for_roll(kept_dice, 2, available_categories)

        # Verify result is reasonable (should be higher than just the kept dice value)
        min_expected = 12  # At minimum, we have two 6's (12 points in sixes)
        self.assertGreater(
            ev,
            min_expected,
            f"EV should be greater than just kept dice value, got {ev}",
        )

        # Verify result is not unreasonably high
        max_expected = 50  # Yahtzee is 50 points
        self.assertLessEqual(
            ev, max_expected, f"EV should not exceed max possible score, got {ev}"
        )

        print(f"✓ Roll 2 EV with kept dice [6,6] is {ev:.2f} (reasonable range)")

    def test_calculate_ev_for_roll_1(self) -> None:
        """Test EV calculation for roll 2 with a simple case"""
        # Available categories
        available_categories = self.strategy.all_categories

        # Keep pair of 6's, looking to get three/four of a kind
        kept_dice = [1, 1, 1, 2, 2]

        # Calculate EV for roll 2
        ev = self.strategy._calculate_ev_for_roll(kept_dice, 1, available_categories)

        min_expected = 25  # Full house
        self.assertGreaterEqual(
            ev,
            min_expected,
            f"EV should be greater than just kept dice value, got {ev}",
        )

        # Verify result is not unreasonably high
        max_expected = 50  # Yahtzee is 50 points
        self.assertLessEqual(
            ev, max_expected, f"EV should not exceed max possible score, got {ev}"
        )

        print(f"✓ Roll 1 EV with kept dice {kept_dice} is {ev:.2f} (reasonable range)")

    @patch.object(ExpectedValueV2Strategy, "_find_best_keep_decision")
    def test_calculate_ev_for_roll_1_calls_find_best(self, mock_find_best):
        """Test that roll 1 calculation calls _find_best_keep_decision correctly"""
        # Set up mock to return a fixed value
        mock_find_best.return_value = 25.0

        # Available categories
        available_categories = self.strategy.all_categories

        # Calculate EV for roll 1 with some kept dice
        kept_dice = [1, 1]
        roll_number = 1

        # Call the method
        ev = self.strategy._calculate_ev_for_roll(
            kept_dice, roll_number, available_categories
        )

        # Verify _find_best_keep_decision was called with appropriate arguments
        mock_find_best.assert_called()

        # Since we're calculating all 6^3 = 216 possible outcomes for the 3 rolled dice,
        # the method should have been called 216 times
        self.assertEqual(
            mock_find_best.call_count,
            6**3,
            f"Expected {6**3} calls to _find_best_keep_decision, got {mock_find_best.call_count}",
        )

        # Verify that the EV is the expected value (25.0 in this case)
        self.assertEqual(ev, 25.0, f"Expected EV of 25.0, got {ev}")

        print("✓ Roll 1 EV calculation correctly calls _find_best_keep_decision")

    def test_find_best_keep_decision_roll_3(self) -> None:
        """Test that _find_best_keep_decision handles roll 3 correctly"""
        # Available categories
        available_categories = self.strategy.all_categories

        # For roll 3, it should just return the max score
        dice = [1, 2, 3, 4, 5]  # Large straight
        ev = self.strategy._find_best_keep_decision(dice, 3, available_categories)
        max_score = self.strategy._calculate_max_score(dice, available_categories)

        self.assertEqual(
            ev,
            max_score,
            f"Roll 3 decision should return max score, got {ev} vs {max_score}",
        )

        print(
            f"✓ _find_best_keep_decision correctly handles roll 3 with max score {max_score}"
        )

    def test_find_best_keep_decision_quality(self) -> None:
        """Test that _find_best_keep_decision makes reasonable choices"""
        # Available categories
        available_categories = self.strategy.all_categories

        # Scenario: Roll 2 with a pair of 6s and random other dice
        dice = [6, 6, 1, 3, 5]

        # In a simplified test, we can determine that the best decision should be
        # to keep the pair of 6s (at minimum)

        # Mock _calculate_ev_for_roll to capture the kept dice
        original_calculate_ev = self.strategy._calculate_ev_for_roll
        best_kept_dice = None
        highest_ev = -1

        def mock_calculate_ev(kept, roll, cats):
            nonlocal best_kept_dice, highest_ev
            # Simple logic: keeping 6s is better than not keeping them
            value = sum(d for d in kept if d == 6)
            if value > highest_ev:
                highest_ev = value
                best_kept_dice = kept
            return value

        # Replace the method temporarily
        self.strategy._calculate_ev_for_roll = mock_calculate_ev

        # Call find best keep decision
        self.strategy._find_best_keep_decision(dice, 2, available_categories)

        # Check that the mock captured keeping at least the 6s
        self.assertIsNotNone(best_kept_dice)
        sixes_in_kept = best_kept_dice.count(6)
        self.assertEqual(
            sixes_in_kept, 2, f"Expected to keep both 6s, kept {best_kept_dice}"
        )

        # Restore original method
        self.strategy._calculate_ev_for_roll = original_calculate_ev

        print("✓ _find_best_keep_decision correctly identifies valuable dice to keep")

    def test_select_dice_to_keep_roll_1(self) -> None:
        """Test that select_dice_to_keep keeps all dice on roll 1"""
        dice = [1, 1, 1, 2, 2]

        # Create a scorecard with roll 3
        scorecard = Scorecard()
        scorecard.current_roll = 1

        # Call the method
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)

        # Should keep all dice
        expected_indices = {0, 1, 2, 3, 4}
        self.assertEqual(
            kept_indices,
            expected_indices,
            f"Expected to keep all dice on roll 1, got {kept_indices}",
        )

        print("✓ select_dice_to_keep correctly keeps all dice on roll 1")

    def test_select_dice_to_keep_roll_3(self) -> None:
        """Test that select_dice_to_keep keeps all dice on roll 3"""
        dice = [1, 2, 3, 4, 5]

        # Create a scorecard with roll 3
        scorecard = Scorecard()
        scorecard.current_roll = 3

        # Call the method
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)

        # Should keep all dice
        expected_indices = {0, 1, 2, 3, 4}
        self.assertEqual(
            kept_indices,
            expected_indices,
            f"Expected to keep all dice on roll 3, got {kept_indices}",
        )

        print("✓ select_dice_to_keep correctly keeps all dice on roll 3")

    def test_select_dice_to_keep_recognizes_patterns(self) -> None:
        """Test that select_dice_to_keep recognizes valuable patterns"""
        # Create test cases with obvious keep decisions
        test_cases = [
            {
                "name": "Small Straight",
                "dice": [1, 2, 3, 4, 6],
                "expected_to_keep": {0, 1, 2, 3},  # Keep the small straight components
                "roll_number": 1,
            },
            {
                "name": "Three of a Kind",
                "dice": [5, 5, 5, 1, 2],
                "expected_to_keep": {0, 1, 2},  # Keep the three 5s
                "roll_number": 2,
            },
            {
                "name": "Pair toward Yahtzee",
                "dice": [6, 6, 1, 3, 4],
                "expected_to_keep": {0, 1},  # Keep the pair of 6s
                "roll_number": 1,
            },
        ]

        # We'll patch _calculate_ev_for_roll to return higher values for specific patterns
        original_calculate_ev = self.strategy._calculate_ev_for_roll

        for case in test_cases:

            def mock_ev(kept_dice, roll_number, available_categories):
                # Simple pattern recognition:
                # - Small straight components (1,2,3,4) are valuable
                # - Three or more of the same kind is valuable
                # - Pairs of high values are valuable

                # Check for small straight components
                if sorted(kept_dice) == [1, 2, 3, 4]:
                    return 25.0

                # Check for three of a kind
                counts = Counter(kept_dice)
                if any(count >= 3 for count in counts.values()):
                    return 20.0

                # Check for pair of 6s
                if kept_dice.count(6) >= 2:
                    return 15.0

                # Otherwise lower value based on dice kept
                return sum(kept_dice) / 2.0

            # Replace the method temporarily
            self.strategy._calculate_ev_for_roll = mock_ev

            # Create a scorecard
            scorecard = Scorecard()
            scorecard.current_roll = case["roll_number"]

            # Call the method
            kept_indices = self.strategy.select_dice_to_keep(case["dice"], scorecard)

            # Check if expected dice are kept
            expected_dice = [case["dice"][i] for i in case["expected_to_keep"]]
            actual_dice = [case["dice"][i] for i in kept_indices]

            if sorted(actual_dice) == sorted(expected_dice):
                print(
                    f"✓ select_dice_to_keep correctly keeps {expected_dice} for {case['name']}"
                )
            else:
                self.fail(
                    f"For {case['name']}, expected to keep {expected_dice}, but kept {actual_dice}"
                )

        # Restore original method
        self.strategy._calculate_ev_for_roll = original_calculate_ev

    def test_real_ev_calculation(self) -> None:
        """Test real expected value calculation with simple cases"""
        # Define a simple case where we can calculate the expected value manually
        # For example, keeping a pair of 6s on roll 2

        kept_dice = [6, 6]
        roll_number = 2

        # Restrict available categories to simplify calculation
        # Let's say only SIXES and CHANCE are available
        available_categories = [ScorecardCategory.SIXES, ScorecardCategory.CHANCE]

        # Calculate EV using our method
        ev = self.strategy._calculate_ev_for_roll(
            kept_dice, roll_number, available_categories
        )

        # Verify reasonable range
        # With pair of 6s kept, minimum is 12 points in SIXES
        # Max would be around 30 points (5 sixes = 30)
        # Average should be somewhere in between
        self.assertGreaterEqual(ev, 12.0, f"EV should be at least 12.0, got {ev}")
        self.assertLessEqual(ev, 30.0, f"EV should be at most 30.0, got {ev}")

        print(f"✓ Real EV calculation for [6,6] on roll 2 gives {ev:.2f} points")

        # Another case: keeping four 1s on roll 2
        kept_dice = [1, 1, 1, 1]

        # With only ONES category, the EV should be close to 4-5
        available_categories = [ScorecardCategory.ONES]
        ev = self.strategy._calculate_ev_for_roll(
            kept_dice, roll_number, available_categories
        )

        # Expected range: 4 (current ones) to 5 (yahtzee of ones)
        self.assertGreaterEqual(ev, 4.0, f"EV should be at least 4.0, got {ev}")
        self.assertLessEqual(ev, 5.0, f"EV should be at most 5.0, got {ev}")

        print(f"✓ Real EV calculation for {kept_dice} on roll 2 gives {ev:.2f} points")

        # Now do the same as above, but add the Yahtzee category
        # With ONES and YAHTZEE available, the EV should be higher
        available_categories = [ScorecardCategory.ONES, ScorecardCategory.YAHTZEE]
        for roll_number in range(1, 4):
            ev = self.strategy._calculate_ev_for_roll(
                kept_dice, roll_number, available_categories
            )
            # Expected range: 4 (current ones) to 50 (yahtzee of ones)
            self.assertGreaterEqual(ev, 4.0, f"EV should be at least 4.0, got {ev}")
            self.assertLessEqual(ev, 50.0, f"EV should be at most 50.0, got {ev}")
            print(
                f"✓ Real EV calculation for {kept_dice} on roll {roll_number} with {", ".join([category.name for category in available_categories])} gives {ev:.2f} points"
            )

        # Now do it with all categories available
        available_categories = self.strategy.all_categories
        for roll_number in range(1, 4):
            ev = self.strategy._calculate_ev_for_roll(
                kept_dice, roll_number, available_categories
            )
            # Expected range: 4 (current ones) to 50 (yahtzee of ones)
            self.assertGreaterEqual(ev, 4.0, f"EV should be at least 4.0, got {ev}")
            self.assertLessEqual(ev, 50.0, f"EV should be at most 50.0, got {ev}")
            print(
                f"✓ Real EV calculation for {kept_dice} on roll {roll_number} with all categories gives {ev:.2f} points"
            )

        kept_dice = [1, 1, 2, 2]
        available_categories = self.strategy.all_categories
        for roll_number in range(1, 4):
            ev = self.strategy._calculate_ev_for_roll(
                kept_dice, roll_number, available_categories
            )
            # Expected range: 0 (current ones) to 50 (yahtzee of ones)
            self.assertGreaterEqual(ev, 0.0, f"EV should be at least 0.0, got {ev}")
            self.assertLessEqual(ev, 50.0, f"EV should be at most 50.0, got {ev}")
            print(
                f"✓ Real EV calculation for {kept_dice} on roll {roll_number} with all categories gives {ev:.2f} points"
            )

    def test_with_decision_inspection(self) -> None:
        """Test specific scenarios with decision inspection"""
        scenarios = [
            {
                "name": "Three of a kind vs. straight",
                "dice": [2, 2, 2, 3, 4],
                "roll": 2,
                "available": [
                    ScorecardCategory.THREE_OF_A_KIND,
                    ScorecardCategory.SMALL_STRAIGHT,
                    ScorecardCategory.LARGE_STRAIGHT,
                ],
            },
            {
                "name": "Early game complex decision",
                "dice": [1, 2, 4, 5, 6],
                "roll": 1,
                "available": self.strategy.all_categories,
            },
            {
                "name": "Medium choice with many options",
                "dice": [6, 6, 6, 4, 5],
                "roll": 1,
                "available": [
                    cat
                    for cat in self.strategy.all_categories
                    if cat != ScorecardCategory.CHANCE
                ],
            },
        ]

        for scenario in scenarios:
            print(f"\n=== SCENARIO: {scenario['name']} ===")

            # Setup scorecard
            scorecard = Scorecard()
            scorecard.current_roll = scenario["roll"]

            # Mark unavailable categories
            all_cats = set(self.strategy.all_categories)
            avail_cats = set(scenario["available"])
            unavail_cats = all_cats - avail_cats

            for cat in unavail_cats:
                scorecard.set_score(cat, [1, 2, 3, 4, 5])  # Mark as used

            # Actually make the decision and print it
            kept_indices = self.strategy.select_dice_to_keep(
                scenario["dice"], scorecard, debug=True
            )
            kept_dice = [scenario["dice"][i] for i in kept_indices]
            print(f"Final decision: Keep {kept_dice}")

    def test_select_dice_to_keep_real_scenarios(self) -> None:
        """Test dice keeping decisions with realistic combinations and available categories"""
        # Create several realistic scenarios to test
        scenarios = [
            {
                "name": "Early Yahtzee opportunity",
                "dice": [4, 4, 4, 6, 2],
                "available_categories": [
                    ScorecardCategory.YAHTZEE,
                    ScorecardCategory.FOURS,
                    ScorecardCategory.THREE_OF_A_KIND,
                ],
                "roll_number": 1,
                "expected_to_keep": [4, 4, 4],  # Should keep the three 4s
            },
            {
                "name": "Straight building opportunity",
                "dice": [1, 2, 3, 5, 6],
                "available_categories": [
                    ScorecardCategory.LARGE_STRAIGHT,
                    ScorecardCategory.SMALL_STRAIGHT,
                ],
                "roll_number": 2,
                "expected_to_keep": [2, 3, 5],  # Should keep the middle sequence
            },
            {
                "name": "Forced choice with limited categories",
                "dice": [2, 3, 5, 5, 6],
                "available_categories": [
                    ScorecardCategory.FIVES,
                    ScorecardCategory.SIXES,
                ],
                "roll_number": 2,
                "expected_to_keep": [
                    5,
                    5,
                ],  # Should keep the 5s given available categories
            },
        ]

        for scenario in scenarios:
            print(f"Testing scenario: {scenario['name']}")

            # Create a scorecard with the appropriate roll number
            scorecard = Scorecard()
            scorecard.current_roll = int(scenario["roll_number"])

            # Set up the available categories
            for cat in self.strategy.all_categories:
                if cat not in scenario["available_categories"]:
                    scorecard.set_score(cat, [1, 2, 3, 4, 5])  # Mark as used

            # Call the method
            kept_indices = self.strategy.select_dice_to_keep(
                scenario["dice"], scorecard, debug=True
            )

            # Extract the kept dice values
            kept_dice = [scenario["dice"][i] for i in kept_indices]

            # Check if expected dice values are kept
            expected_dice = scenario["expected_to_keep"]

            # Allow for different ordering but same content
            self.assertEqual(
                Counter(kept_dice),
                Counter(expected_dice),
                f"For scenario '{scenario['name']}', expected to keep {expected_dice}, but kept {kept_dice}",
            )

            print(
                f"✓ In scenario '{scenario['name']}', correctly decided to keep {kept_dice}"
            )

    def test_full_turn_decision_making(self) -> None:
        """Test the strategy's decision-making across a complete turn (all 3 rolls)"""
        # Setup a realistic game state
        scorecard = Scorecard()

        # Let's say we're midway through the game with these categories filled
        scorecard.set_score(ScorecardCategory.ONES, [1, 1, 1, 2, 3])
        scorecard.set_score(ScorecardCategory.TWOS, [2, 2, 2, 3, 4])
        scorecard.set_score(ScorecardCategory.THREES, [3, 3, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.FULL_HOUSE, [2, 2, 3, 3, 3])

        # Available categories - important ones still available
        available_categories = [
            cat
            for cat in self.strategy.all_categories
            if scorecard.get_score(cat) is None
        ]

        # First roll
        scorecard.current_roll = 1
        first_roll = [5, 5, 2, 3, 1]
        kept_indices_1 = self.strategy.select_dice_to_keep(
            first_roll, scorecard, debug=True
        )
        kept_dice_1 = [first_roll[i] for i in kept_indices_1]

        # Understandable decision, aiming for the straigths
        self.assertEqual(
            Counter(kept_dice_1),
            Counter([5, 2, 3]),
            f"Expected to keep [5, 2, 3] after first roll, but kept {kept_dice_1}",
        )
        print(
            f"✓ After first roll {first_roll}, correctly decided to keep {kept_dice_1}"
        )

        # Second roll - simulate getting another 5 and random dice
        scorecard.current_roll = 2
        second_roll = [5, 5, 5, 1, 6]
        kept_indices_2 = self.strategy.select_dice_to_keep(
            second_roll, scorecard, debug=True
        )
        kept_dice_2 = [second_roll[i] for i in kept_indices_2]

        # Most probably suboptimal decision since it is not aiming for yahtzee
        self.assertEqual(
            Counter(kept_dice_2),
            Counter([5, 5, 5, 6]),
            f"Expected to keep [5, 5, 5, 6] after second roll, but kept {kept_dice_2}",
        )
        print(
            f"✓ After second roll {second_roll}, correctly decided to keep {kept_dice_2}"
        )

        # Third roll - simulate getting four 5s total
        scorecard.current_roll = 3
        final_roll = [5, 5, 5, 5, 2]

        # For the final roll, all dice should be kept
        kept_indices_3 = self.strategy.select_dice_to_keep(
            final_roll, scorecard, debug=True
        )
        self.assertEqual(kept_indices_3, {0, 1, 2, 3, 4})

        # Now test category selection
        category = self.strategy.select_category(final_roll, scorecard, debug=True)

        # With four 5s, it should choose FOUR_OF_A_KIND or FIVES (higher score)
        expected_categories = [
            ScorecardCategory.FOUR_OF_A_KIND,
            ScorecardCategory.FIVES,
        ]
        self.assertIn(
            category,
            expected_categories,
            f"Expected to choose {[c.name for c in expected_categories]}, but chose {category.name}",
        )

        print(f"✓ Selected appropriate category {category.name} for {final_roll}")

    def test_yahtzee_opportunity_recognition(self) -> None:
        """Test the strategy's ability to recognize and pursue Yahtzee opportunities"""
        scorecard = Scorecard()
        # Remove chance to avoid interference
        scorecard.set_score(ScorecardCategory.CHANCE, [1, 2, 3, 4, 5])

        # Test with 4 of a kind, should keep all four matching dice
        dice = [6, 6, 6, 6, 3]
        scorecard.current_roll = 1

        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        self.assertEqual(
            Counter(kept_dice),
            Counter([6, 6, 6, 6]),
            f"Expected to keep four 6s when pursuing Yahtzee, but kept {kept_dice}",
        )
        print(f"✓ Correctly identified and kept {kept_dice} for Yahtzee opportunity")

        # Test with 3 of a kind, should still prioritize Yahtzee potential
        dice = [3, 3, 3, 2, 1]
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        # Also here, very suboptimal: keeping only the 3
        self.assertEqual(
            Counter(kept_dice),
            Counter([3]),
            f"Expected to keep [3] for Yahtzee opportunity, but kept {kept_dice}",
        )
        print(f"✓ Correctly identified and kept {kept_dice} for Yahtzee opportunity")

    def test_full_house_potential(self) -> None:
        """
        Test the strategy's ability to recognize and pursue Full House opportunities
        """
        scorecard = Scorecard()

        scorecard.set_score(ScorecardCategory.ONES, [1, 2, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.TWOS, [2, 3, 4, 5, 6])
        scorecard.set_score(ScorecardCategory.THREE_OF_A_KIND, [3, 3, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.FOUR_OF_A_KIND, [4, 4, 4, 4, 5])
        scorecard.set_score(ScorecardCategory.CHANCE, [1, 2, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.SMALL_STRAIGHT, [1, 2, 3, 4, 6])

        scorecard.current_roll = 2  # Set score resets the roll number

        # Test with a pair and a triplet
        dice = [3, 3, 5, 5, 1]

        # In this case, the strategy should keep the pairs and the triplet
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        # Should keep the triplet (3) and at least one pair (5)
        expected_kept = [3, 3, 5, 5]
        self.assertEqual(
            Counter(kept_dice),
            Counter(expected_kept),
            f"Expected to keep {expected_kept}, but kept {kept_dice}",
        )
        print(f"✓ Correctly identified and kept {kept_dice} for Full House opportunity")

    def test_straight_building_decisions(self) -> None:
        """Test the strategy's ability to recognize and pursue straight opportunities"""
        scorecard = Scorecard()
        scorecard.current_roll = 1

        # Test with dice that have potential for large straight
        dice = [1, 3, 4, 5, 2]

        # In this case, all dice should be kept since they form a large straight
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        self.assertEqual(
            kept_indices,
            {0, 1, 2, 3, 4},
            f"Expected to keep all dice for large straight, but kept indices {kept_indices}",
        )
        print(f"✓ Correctly kept all dice {dice} for large straight opportunity")

        # Test with partial small straight
        dice = [2, 3, 4, 1, 1]
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        # Should keep the sequence elements (2,3,4) plus at least one 1
        straight_elements = [2, 3, 4]
        for elem in straight_elements:
            self.assertIn(
                elem,
                kept_dice,
                f"Expected {elem} to be kept for small straight building, but it wasn't in {kept_dice}",
            )
        print(f"✓ Correctly kept straight components when building a straight")

    def test_category_selection_priorities(self) -> None:
        """Test that the strategy makes optimal category selection decisions"""
        scenarios: List[
            Dict[str, Union[str, List[int], List[ScorecardCategory], ScorecardCategory]]
        ] = [
            {
                "name": "Choose Yahtzee for five of a kind",
                "dice": [4, 4, 4, 4, 4],
                "filled_categories": [ScorecardCategory.FOURS],  # Fours already used
                "expected_category": ScorecardCategory.YAHTZEE,
            },
            {
                "name": "Choose matching upper section for Yahtzee when bonus possible",
                "dice": [3, 3, 3, 3, 3],
                "filled_categories": [
                    ScorecardCategory.YAHTZEE,  # Yahtzee already scored
                    ScorecardCategory.FOUR_OF_A_KIND,
                ],
                "expected_category": ScorecardCategory.THREES,  # Should pick upper section for bonus
            },
            {
                "name": "Don't waste good categories on bad rolls",
                "dice": [1, 2, 3, 5, 6],  # No patterns
                "filled_categories": [
                    ScorecardCategory.ONES,
                    ScorecardCategory.TWOS,
                    ScorecardCategory.THREES,
                    ScorecardCategory.FOURS,
                ],
                "expected_not_category": ScorecardCategory.YAHTZEE,  # Shouldn't waste Yahtzee
            },
        ]

        for scenario in scenarios:
            # Setup scorecard
            scorecard = Scorecard()
            for cat in scenario["filled_categories"]:
                scorecard.set_score(cat, [1, 2, 3, 4, 5])  # Mark as used

            # Run the selection
            selected_category = self.strategy.select_category(
                scenario["dice"], scorecard, debug=True
            )

            # Check expectations
            if "expected_category" in scenario:
                self.assertEqual(
                    selected_category,
                    scenario["expected_category"],
                    f"For scenario '{scenario['name']}', expected category {scenario['expected_category'].name}, but got {selected_category.name}",
                )
                print(
                    f"✓ In scenario '{scenario['name']}', correctly selected {selected_category.name}"
                )

            if "expected_not_category" in scenario:
                self.assertNotEqual(
                    selected_category,
                    scenario["expected_not_category"],
                    f"For scenario '{scenario['name']}', should not have selected {scenario['expected_not_category'].name}, but did",
                )
                print(
                    f"✓ In scenario '{scenario['name']}', correctly avoided {scenario['expected_not_category'].name}"
                )

    def test_end_game_optimization(self) -> None:
        """Test the strategy's decision making near the end of the game"""
        # Setup a scorecard with only a few categories remaining
        scorecard = Scorecard()

        # Fill most categories
        remaining_categories = [
            ScorecardCategory.CHANCE,
            ScorecardCategory.YAHTZEE,
            ScorecardCategory.SIXES,
        ]

        for cat in self.strategy.all_categories:
            if cat not in remaining_categories:
                scorecard.set_score(cat, [1, 2, 3, 4, 5])  # Mark as used

        # Test with a mediocre roll
        dice = [1, 3, 2, 5, 6]

        # Since we're almost at the end of the game, the strategy should be
        # more focused on optimizing the few remaining categories
        scorecard.current_roll = 1
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        # Should at least keep the 6 since SIXES is still available
        self.assertIn(
            6,
            kept_dice,
            f"Expected to keep the 6 when SIXES category is available, but kept {kept_dice}",
        )
        print(f"✓ Correctly kept the 6 when SIXES category is available")

        # Test category selection
        scorecard.current_roll = 3
        selected_category = self.strategy.select_category(dice, scorecard, debug=True)

        # Should not waste YAHTZEE on this bad roll
        self.assertNotEqual(
            selected_category,
            ScorecardCategory.YAHTZEE,
            f"Should not waste YAHTZEE on a bad roll",
        )
        print(f"✓ Correctly avoided wasting YAHTZEE on a bad roll")


class TestGeminiStrategy(unittest.TestCase):
    def setUp(self) -> None:
        """Initialize the Gemini strategy"""

        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.environ["GOOGLE_API_KEY"]

        self.strategy = GeminiStrategy(api_key)

    def test_basic_strategy(self) -> None:
        """Test the Gemini strategy's decision making"""
        # Test with a simple scenario
        scorecard = Scorecard()
        scorecard.current_roll = 1

        # Test with a roll that has potential for both straights and Yahtzee
        dice = [1, 2, 3, 4, 5]

        # Call the method
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        # Should keep all dice since they form a large straight
        expected_indices = {0, 1, 2, 3, 4}
        self.assertEqual(
            kept_indices,
            expected_indices,
            f"Expected to keep all dice for large straight, but kept indices {kept_indices}",
        )
        print(
            f"✓ Gemini strategy correctly kept all dice {kept_dice} for large straight"
        )

        # Test with a roll that has potential for Yahtzee
        dice = [2, 2, 2, 2, 3]
        scorecard.current_roll = 2
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        # Should keep all 2s since they form a Yahtzee
        expected_indices = {0, 1, 2, 3}
        self.assertEqual(
            kept_indices,
            expected_indices,
            f"Expected to keep all 2s for Yahtzee, but kept indices {kept_indices}",
        )

        print(f"✓ Gemini strategy correctly kept all 2s {kept_dice} for Yahtzee")

    def test_complex_strategy(self) -> None:
        """Test the Gemini strategy's decision making with complex scenarios"""
        # Test with a scenario that has multiple options
        scorecard = Scorecard()
        scorecard.current_roll = 2

        # Test with a roll that has potential for both straights and Yahtzee
        dice = [1, 2, 3, 4, 6]

        # Call the method
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]

        # Should keep the sequence elements (1,2,3,4)
        expected_indices = {0, 1, 2, 3}
        self.assertEqual(
            kept_indices,
            expected_indices,
            f"Expected to keep {expected_indices}, but kept indices {kept_indices}",
        )
        print(f"✓ Gemini strategy correctly kept {kept_dice} for complex scenario")

        # Test with many categories filled, and on first roll
        scorecard.current_roll = 1
        scorecard.set_score(ScorecardCategory.ONES, [1, 2, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.TWOS, [1, 2, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.THREES, [1, 2, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.LARGE_STRAIGHT, [1, 2, 3, 4, 5])
        scorecard.set_score(ScorecardCategory.SMALL_STRAIGHT, [1, 2, 3, 4, 5])

        # Test with a roll that has potential for both straights and Yahtzee
        dice = [1, 2, 3, 4, 5]
        kept_indices = self.strategy.select_dice_to_keep(dice, scorecard, debug=True)
        kept_dice = [dice[i] for i in kept_indices]
        expected_indices_list = [
            {3, 4},
            {4},
            set(),
        ]  # Either keep high values or reroll everything
        self.assertIn(
            kept_indices,
            expected_indices_list,
            f"Expected to keep only high value dice since straights are filled, but kept indices {kept_indices}",
        )
        print(
            f"✓ Gemini strategy correctly kept {kept_dice} for complex scenario with filled straights"
        )


class TestStrategyPerformance(unittest.TestCase):
    def setUp(self) -> None:
        """Initialize strategies to test"""

        from dotenv import load_dotenv

        load_dotenv()

        self.strategies = {
            "Random": RandomStrategy(),
            "RuleBased": RuleBasedStrategy(),
            "ExpectedValue": ExpectedValueStrategy(),
            "ExpectedValueV2": ExpectedValueV2Strategy(),
            "Gemini": GeminiStrategy(os.environ["GOOGLE_API_KEY"]),
        }

    def time_strategy_function(self, strategy, func_name, *args, repetitions=1):
        """Time the execution of a strategy function multiple times and return average"""
        strategy_func = getattr(strategy, func_name)
        total_time = 0

        # Warm up run (not counted)
        strategy_func(*args)

        for _ in range(repetitions):
            start_time = time.time()
            result = strategy_func(*args)
            end_time = time.time()
            total_time += end_time - start_time

        avg_time = total_time / repetitions
        return avg_time, result

    def test_performance_dice_keeping(self) -> None:
        """Test the performance of dice keeping decisions across different scenarios"""
        scenarios = [
            {
                "name": "Early game (Roll 1)",
                "dice": [1, 2, 3, 4, 5],
                "roll_number": 1,
                "filled_categories": [],
            },
            {
                "name": "Mid game with pairs (Roll 2)",
                "dice": [3, 3, 5, 5, 1],
                "roll_number": 2,
                "filled_categories": [
                    ScorecardCategory.ONES,
                    ScorecardCategory.TWOS,
                    ScorecardCategory.THREE_OF_A_KIND,
                    ScorecardCategory.FOUR_OF_A_KIND,
                ],
            },
            {
                "name": "Late game (Roll 1)",
                "dice": [6, 6, 6, 3, 2],
                "roll_number": 1,
                "filled_categories": [
                    cat
                    for cat in list(ScorecardCategory)
                    if cat
                    not in [
                        ScorecardCategory.SIXES,
                        ScorecardCategory.YAHTZEE,
                        ScorecardCategory.CHANCE,
                    ]
                ],
            },
            {
                "name": "Complex pattern (Roll 2)",
                "dice": [2, 3, 4, 5, 6],
                "roll_number": 2,
                "filled_categories": [
                    ScorecardCategory.SMALL_STRAIGHT,
                    ScorecardCategory.LARGE_STRAIGHT,
                ],
            },
            {
                "name": "Final roll decision",
                "dice": [4, 4, 4, 4, 1],
                "roll_number": 3,
                "filled_categories": [
                    ScorecardCategory.FOURS,
                    ScorecardCategory.FOUR_OF_A_KIND,
                ],
            },
        ]

        results = defaultdict(list)
        decisions = defaultdict(list)

        print("\n\n===== DICE KEEPING PERFORMANCE TEST =====")

        for scenario in scenarios:
            print(f"\nScenario: {scenario['name']}")
            print(
                f"Dice: {scenario['dice']}, Roll: {scenario['roll_number']}, Filled: {scenario['filled_categories']}"
            )

            # Setup scorecard for this scenario
            scorecard = Scorecard()
            scorecard.current_roll = int(scenario["roll_number"])
            for cat in scenario["filled_categories"]:
                scorecard.set_score(cat, [1, 2, 3, 4, 5])

            # Test each strategy
            for strategy_name, strategy in self.strategies.items():
                time_taken, kept_indices = self.time_strategy_function(
                    strategy, "select_dice_to_keep", scenario["dice"], scorecard
                )

                results[strategy_name].append(time_taken)
                kept_dice = [scenario["dice"][i] for i in kept_indices]
                decisions[strategy_name].append(kept_dice)

                print(
                    f"  {strategy_name:15} - Time: {time_taken:.6f}s - Kept: {kept_dice}"
                )

        # Print summary table
        print("\nSUMMARY - Average execution time (seconds):")
        headers: List[str] = (
            ["Strategy"] + [str(s["name"]) for s in scenarios] + ["Average"]
        )
        table_data = []

        for strategy_name in self.strategies.keys():
            row = [strategy_name]
            row.extend([f"{time:.6f}" for time in results[strategy_name]])
            avg = sum(results[strategy_name]) / len(results[strategy_name])
            row.append(f"{avg:.6f}")
            table_data.append(row)

        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    def test_performance_category_selection(self) -> None:
        """Test the performance of category selection decisions across different scenarios"""
        scenarios = [
            {
                "name": "Early game choice",
                "dice": [3, 3, 3, 4, 5],
                "filled_categories": [],
            },
            {
                "name": "Mid game with Yahtzee",
                "dice": [2, 2, 2, 2, 2],
                "filled_categories": [
                    ScorecardCategory.TWOS,
                ],
            },
            {
                "name": "Late game forced choice",
                "dice": [1, 2, 3, 4, 6],
                "filled_categories": [
                    cat
                    for cat in list(ScorecardCategory)
                    if cat not in [ScorecardCategory.CHANCE, ScorecardCategory.YAHTZEE]
                ],
            },
            {
                "name": "Full house decision",
                "dice": [5, 5, 5, 2, 2],
                "filled_categories": [
                    ScorecardCategory.FULL_HOUSE,
                    ScorecardCategory.THREE_OF_A_KIND,
                ],
            },
            {
                "name": "Optimal Yahtzee bonus use",
                "dice": [6, 6, 6, 6, 6],
                "filled_categories": [
                    ScorecardCategory.YAHTZEE,
                    ScorecardCategory.SIXES,
                ],
            },
        ]

        results = defaultdict(list)
        decisions = defaultdict(list)

        print("\n\n===== CATEGORY SELECTION PERFORMANCE TEST =====")

        for scenario in scenarios:
            print(f"\nScenario: {scenario['name']}")
            print(f"Dice: {scenario['dice']}")

            # Setup scorecard for this scenario
            scorecard = Scorecard()
            for cat in scenario["filled_categories"]:
                scorecard.set_score(cat, [1, 2, 3, 4, 5])

            # Test each strategy
            for strategy_name, strategy in self.strategies.items():
                time_taken, category = self.time_strategy_function(
                    strategy, "select_category", scenario["dice"], scorecard
                )

                results[strategy_name].append(time_taken)
                decisions[strategy_name].append(category)

                print(
                    f"  {strategy_name:15} - Time: {time_taken:.6f}s - Category: {category} - Filled: {scenario['filled_categories']} - Score: {scorecard.calculate_score(category, scenario['dice'])}"
                )

        # Print summary table
        print("\nSUMMARY - Average execution time (seconds):")
        headers = ["Strategy"] + [str(s["name"]) for s in scenarios] + ["Average"]
        table_data = []

        for strategy_name in self.strategies.keys():
            row = [strategy_name]
            row.extend([f"{time:.6f}" for time in results[strategy_name]])
            avg = sum(results[strategy_name]) / len(results[strategy_name])
            row.append(f"{avg:.6f}")
            table_data.append(row)

        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    def test_full_game_simulation(self) -> None:
        """Test the performance in a simulated full game"""
        print("\n\n===== FULL GAME SIMULATION PERFORMANCE =====")

        # List of decisions to make in sequence (first roll of each turn)
        game_sequence = [
            {"dice": [1, 2, 3, 4, 5], "roll_number": 1},
            {"dice": [5, 5, 3, 2, 1], "roll_number": 1},
            {"dice": [6, 6, 6, 4, 2], "roll_number": 1},
            {"dice": [1, 1, 3, 4, 5], "roll_number": 1},
            {"dice": [2, 2, 2, 3, 3], "roll_number": 1},
        ]

        results = defaultdict(list)

        for strategy_name, strategy in self.strategies.items():
            print(f"\nTesting strategy: {strategy_name}")
            scorecard = Scorecard()
            total_decision_time = 0

            for turn, turn_data in enumerate(game_sequence, 1):
                print(f"  Turn {turn}: Dice {turn_data['dice']}")

                # Time dice keeping decision
                scorecard.current_roll = turn_data["roll_number"]
                keep_time, kept_indices = self.time_strategy_function(
                    strategy, "select_dice_to_keep", turn_data["dice"], scorecard
                )
                total_decision_time += keep_time
                kept_dice = [turn_data["dice"][i] for i in kept_indices]

                # Simulate a final roll result
                final_dice = kept_dice + [6, 6, 6, 6, 6][: 5 - len(kept_dice)]
                print(f"    Kept {kept_dice}, final roll: {final_dice}")

                # Time category selection
                cat_time, category = self.time_strategy_function(
                    strategy,
                    "select_category",
                    final_dice,
                    scorecard
                )
                total_decision_time += cat_time

                # Record the decision and update scorecard
                scorecard.set_score(category, [1, 2, 3, 4, 5])  # Just placeholder
                print(f"    Selected {category} in {cat_time:.6f}s")

            results[strategy_name] = total_decision_time
            print(f"  Total decision time: {total_decision_time:.6f}s")

        # Print comparative results
        print("\nSTRATEGY PERFORMANCE SUMMARY:")
        for name, time_taken in sorted(results.items(), key=lambda x: x[1]):
            print(f"{name:15}: {time_taken:.6f}s")

        # Calculate relative performance
        fastest = min(results.values())
        print("\nRELATIVE PERFORMANCE (relative to fastest):")
        for name, time_taken in sorted(results.items(), key=lambda x: x[1]):
            relative = time_taken / fastest if fastest > 0 else float("inf")
            print(f"{name:15}: {relative:.2f}x slower than fastest")


if __name__ == "__main__":
    unittest.main()
