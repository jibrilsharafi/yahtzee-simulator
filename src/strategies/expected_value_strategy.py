import itertools
import math
from collections import Counter
from typing import List, Optional, Set, Tuple

from src.game.scorecard import Scorecard, ScorecardCategory
from src.strategies.base_strategy import BaseStrategy


class ExpectedValueStrategy(BaseStrategy):
    def __init__(self):
        # Category references using enums directly
        self.upper_categories = [
            ScorecardCategory.ONES,
            ScorecardCategory.TWOS,
            ScorecardCategory.THREES,
            ScorecardCategory.FOURS,
            ScorecardCategory.FIVES,
            ScorecardCategory.SIXES,
        ]
        self.lower_categories = [
            ScorecardCategory.THREE_OF_A_KIND,
            ScorecardCategory.FOUR_OF_A_KIND,
            ScorecardCategory.FULL_HOUSE,
            ScorecardCategory.SMALL_STRAIGHT,
            ScorecardCategory.LARGE_STRAIGHT,
            ScorecardCategory.YAHTZEE,
            ScorecardCategory.CHANCE,
        ]
        self.all_categories = self.upper_categories + self.lower_categories

        # Cache to store expected values for different game states
        self.roll_ev_cache = (
            {}
        )  # Cache for expected values based on dice and roll number
        self.category_ev_cache = {}  # Cache for category selection expected values

        # Pre-calculate lookup tables
        self._initialize_lookup_tables()

    def _dice_key(self, dice: List[int]) -> Tuple[int, ...]:
        """Convert dice values to a canonical representation (counts of each value)"""
        if not dice:
            return (0, 0, 0, 0, 0, 0)
        counts = Counter(dice)
        return tuple(counts.get(i, 0) for i in range(1, 7))

    def _scorecard_key(self, scorecard: Scorecard) -> Tuple[Optional[int], ...]:
        """Create a compact representation of a scorecard state"""
        return tuple(scorecard.get_score(cat) for cat in self.all_categories)

    def _initialize_lookup_tables(self):
        print("Initializing lookup tables for ExpectedValueStrategy...")
        self.ev_table = (
            {}
        )  # Expected values for each roll number and dice configuration

        # Pre-compute the expected values for the third roll (no more decisions)
        print("Computing third roll values...")
        for dice_config in self._generate_all_dice_configs():
            self.ev_table[(dice_config, 3)] = self._calculate_max_category_score(
                dice_config
            )

        # Pre-compute the expected values for the second roll
        print("Computing second roll values...")
        for dice_config in self._generate_all_dice_configs():
            self.ev_table[(dice_config, 2)] = self._calculate_keep_options_ev(
                dice_config, 2
            )

        # Pre-compute the expected values for the first roll
        print("Computing first roll values...")
        for dice_config in self._generate_all_dice_configs():
            self.ev_table[(dice_config, 1)] = self._calculate_keep_options_ev(
                dice_config, 1
            )

        print("Lookup tables initialized!")

    def _generate_all_dice_configs(self) -> List[Tuple[int, ...]]:
        """Generate all possible dice configurations (as count tuples)"""
        configs = []

        # Function to generate all ways to distribute n dice across 6 values
        def distribute_dice(n, position=0, current_config=(0, 0, 0, 0, 0, 0)):
            if position == 6:
                if sum(current_config) == n:
                    configs.append(current_config)
                return

            for count in range(n + 1):
                new_config = list(current_config)
                new_config[position] = count
                distribute_dice(n, position + 1, tuple(new_config))

        # Generate configs for 0 to 5 dice
        for n_dice in range(6):
            distribute_dice(n_dice)

        return configs

    def _calculate_max_category_score(self, dice_config: Tuple[int, ...]) -> float:
        """Calculate the maximum score possible across all available categories"""
        # Convert dice config to a list for scoring
        dice_list = []
        for value, count in enumerate(dice_config, 1):
            dice_list.extend([value] * count)

        # Create a temporary scorecard to calculate scores
        scorecard = Scorecard()

        # Calculate the score for each category
        max_score = 0
        for category in self.all_categories:
            score = scorecard.calculate_score(category, dice_list)
            max_score = max(max_score, score)

        return max_score

    def _calculate_keep_options_ev(
        self, dice_config: Tuple[int, ...], roll_number: int
    ) -> float:
        """Calculate the expected value considering all possible keep decisions"""
        # If all 5 dice are used, no decision to make
        if sum(dice_config) == 5:
            if roll_number == 3:
                return self._calculate_max_category_score(dice_config)
            else:
                return self.ev_table.get((dice_config, roll_number + 1), 0)

        # If this is the third roll, just score what we have
        if roll_number == 3:
            return self._calculate_max_category_score(dice_config)

        # Consider keeping what we have
        total_kept = sum(dice_config)
        dice_to_roll = 5 - total_kept

        # Calculate EV for all possible next rolls
        outcomes_ev = 0
        for new_roll in self._generate_all_possible_rolls(dice_to_roll):
            # Combine kept dice with new roll
            new_config = list(dice_config)
            for value in new_roll:
                new_config[value - 1] += 1

            # Get the EV for this new configuration
            new_config_tuple = tuple(new_config)
            next_roll_ev = self.ev_table.get((new_config_tuple, roll_number + 1), 0)
            outcomes_ev += next_roll_ev

        # Average over all possible outcomes
        total_outcomes = 6**dice_to_roll
        expected_value = outcomes_ev / total_outcomes

        return expected_value

    def _generate_all_possible_rolls(self, num_dice: int) -> List[Tuple[int, ...]]:
        """Generate all possible rolls for a given number of dice"""
        return list(itertools.product(range(1, 7), repeat=num_dice))

    def _generate_all_subsets(self, indices: range) -> List[Tuple[int, ...]]:
        """Generate all possible subsets of dice indices to keep"""
        result: List[Tuple[int, ...]] = []
        for r in range(len(indices) + 1):
            result.extend(itertools.combinations(indices, r))
        return result

    def _estimate_future_value(
        self, scorecard: Scorecard, category: ScorecardCategory
    ) -> float:
        """Estimate the value of future turns after selecting a category"""
        # Cache the result based on the scorecard state and category
        scorecard_key = self._scorecard_key(scorecard)
        cache_key = (scorecard_key, category)

        if cache_key in self.category_ev_cache:
            return self.category_ev_cache[cache_key]

        # Create a copy of the scorecard with the category scored
        new_scorecard = Scorecard()
        for cat in self.all_categories:
            score = scorecard.get_score(cat)
            if score is not None:
                new_scorecard.set_score(cat, score)

        # Calculate how many turns remain
        remaining_categories = [
            cat
            for cat in self.all_categories
            if new_scorecard.get_score(cat) is None and cat != category
        ]
        turns_remaining = len(remaining_categories)

        if turns_remaining == 0:
            # No more turns, check for upper section bonus
            upper_total = sum(
                new_scorecard.get_score(cat) or 0 for cat in self.upper_categories
            )
            bonus = 35 if upper_total >= 63 else 0
            return bonus

        # Estimate future value based on average expected value per turn
        # and potential bonus for upper section
        avg_turn_value = 24  # Average expected value per turn in Yahtzee

        # Adjust for upper section bonus potential
        upper_total = sum(
            new_scorecard.get_score(cat) or 0 for cat in self.upper_categories
        )
        upper_remaining = [
            cat for cat in self.upper_categories if new_scorecard.get_score(cat) is None
        ]
        upper_potential = upper_total + (
            len(upper_remaining) * 3.5
        )  # Average value per upper category

        # Add bonus value weighted by probability
        bonus_probability = 1.0 if upper_potential >= 63 else 0
        bonus_value = 35 * bonus_probability

        future_value = (turns_remaining * avg_turn_value) + bonus_value

        # Store in cache
        self.category_ev_cache[cache_key] = future_value
        return future_value

    def select_dice_to_keep(
        self, current_dice: List[int], scorecard: Scorecard
    ) -> Set[int]:
        """Choose which dice to keep based on expected value"""
        # [No changes needed for this method]
        # Determine current roll number (1, 2, or 3)
        roll_number = scorecard.current_roll

        # If this is the third roll, keep all dice
        if roll_number >= 3:
            return set(range(len(current_dice)))

        # Create a key for our dice configuration
        dice_config = self._dice_key(current_dice)

        # Try all possible subsets of dice to keep
        best_ev = -1.0
        best_indices = set()

        for keep_mask in range(1 << len(current_dice)):
            keep_indices = {i for i in range(len(current_dice)) if (keep_mask >> i) & 1}
            kept_dice = [current_dice[i] for i in keep_indices]
            kept_config = self._dice_key(kept_dice)

            # Calculate expected value for this keep decision
            keep_ev = self._calculate_ev_for_kept_dice(kept_config, roll_number)

            if keep_ev > best_ev:
                best_ev = keep_ev
                best_indices = keep_indices

        return best_indices

    def _calculate_ev_for_kept_dice(
        self, kept_config: Tuple[int, ...], roll_number: int
    ) -> float:
        """Calculate expected value for keeping specific dice configuration"""
        # Use the pre-computed table or calculate if not available
        if (kept_config, roll_number) in self.ev_table:
            return self.ev_table[(kept_config, roll_number)]

        # If not in pre-computed table, we need to calculate it
        dice_to_roll = 5 - sum(kept_config)
        total_outcomes = 6**dice_to_roll
        total_ev = 0

        # Generate all possible outcomes for rolling the remaining dice
        for roll in itertools.product(range(1, 7), repeat=dice_to_roll):
            # Combine kept dice with new roll
            new_config = list(kept_config)
            for value in roll:
                new_config[value - 1] += 1

            # Get the score/EV for this new configuration
            new_config_tuple = tuple(new_config)
            next_roll_ev = self.ev_table.get(
                (new_config_tuple, roll_number + 1),
                self._calculate_max_category_score(new_config_tuple),
            )
            total_ev += next_roll_ev

        expected_value = total_ev / total_outcomes
        return expected_value

    def select_category(
        self, dice: List[int], scorecard: Scorecard
    ) -> ScorecardCategory:
        """Select category that maximizes expected future value"""
        best_ev = -1.0
        best_category = None

        # Get available categories
        available_categories = [
            cat for cat in self.all_categories if scorecard.get_score(cat) is None
        ]

        # If only one category left, just use that
        if len(available_categories) == 1:
            return available_categories[0]

        # Calculate expected value for each available category
        for category in available_categories:
            # Calculate immediate score
            score = scorecard.calculate_score(category, dice)

            # Calculate impact on future turns
            future_ev = self._estimate_future_value(scorecard, category)

            # Total expected value
            total_ev = score + future_ev

            # Special case for Yahtzee: if we already have one, prioritize getting the bonus
            if (
                category == ScorecardCategory.YAHTZEE
                and scorecard.get_score(ScorecardCategory.YAHTZEE) == 50
            ):
                total_ev += 100  # Strongly favor getting Yahtzee bonus

            # Special case: avoid using Yahtzee as a "dump" category if possible
            if (
                category == ScorecardCategory.YAHTZEE
                and score == 0
                and len(available_categories) > 1
            ):
                total_ev -= (
                    20  # Discourage using Yahtzee for 0 points if other options exist
                )

            if total_ev > best_ev:
                best_ev = total_ev
                best_category = category

        if best_category is None:
            # This should never happen if available_categories is not empty
            # But adding a fallback to ensure we always return a category
            print(
                "Warning: No best category found, defaulting to CHANCE."
            )
            return (
                available_categories[0]
                if available_categories
                else ScorecardCategory.CHANCE
            )
        return best_category
