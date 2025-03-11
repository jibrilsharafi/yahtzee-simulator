import itertools
from collections import Counter
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from src.game.scorecard import Scorecard, ScorecardCategory
from src.strategies.base_strategy import BaseStrategy


class ExpectedValueV2Strategy(BaseStrategy):
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

        # Track important categories for decision making
        self.high_value_categories = [
            ScorecardCategory.YAHTZEE,
            ScorecardCategory.LARGE_STRAIGHT,
            ScorecardCategory.SMALL_STRAIGHT,
            ScorecardCategory.FULL_HOUSE,
        ]

        # Runtime cache - will be cleared between games
        self.ev_cache = {}

    def _dice_key(self, dice: List[int]) -> Tuple[int, ...]:
        """Convert dice values to a canonical representation (counts of each value)"""
        if not dice:
            return (0, 0, 0, 0, 0, 0)
        counts = Counter(dice)
        return tuple(counts.get(i, 0) for i in range(1, 7))

    def _calculate_score_for_category(
        self, dice: List[int], category: ScorecardCategory
    ) -> int:
        """Calculate the score for a specific category with the given dice"""
        scorecard = Scorecard()
        return scorecard.calculate_score(category, dice)

    def _calculate_max_score(
        self, dice: List[int], available_categories: List[ScorecardCategory]
    ) -> int:
        """Calculate the maximum score possible across available categories"""
        max_score = 0
        for category in available_categories:
            score = self._calculate_score_for_category(dice, category)
            max_score = max(max_score, score)
        return max_score

    def _available_categories_key(
        self, categories: List[ScorecardCategory]
    ) -> FrozenSet:
        """Create a hashable key from available categories"""
        return frozenset(categories)

    def _calculate_ev_for_roll(
        self,
        kept_dice: List[int],
        roll_number: int,
        available_categories: List[ScorecardCategory],
    ) -> float:
        """
        Calculate the expected value (average score) for the current roll state.
        Uses caching to avoid recalculating values.
        """
        # Terminal cases: roll 3 or keeping all dice
        if roll_number >= 3 or len(kept_dice) == 5:
            return self._calculate_max_score(kept_dice, available_categories)

        # Create cache key
        dice_key = self._dice_key(kept_dice)
        categories_key = self._available_categories_key(available_categories)
        cache_key = (dice_key, roll_number, categories_key)

        # Check cache first
        if cache_key in self.ev_cache:
            return self.ev_cache[cache_key]

        # Calculate how many dice we still need to roll
        dice_to_roll = 5 - len(kept_dice)

        # Calculate expected value
        total_outcomes = 6**dice_to_roll
        total_score = 0.0

        # For each possible outcome of the dice we're rolling
        for roll_outcome in itertools.product(range(1, 7), repeat=dice_to_roll):
            # Combine the dice we're keeping with this roll outcome
            complete_dice = kept_dice + list(roll_outcome)

            # For the final roll (roll 3), we just take the max score
            if roll_number == 2:  # This is roll 2, leading to roll 3
                outcome_score = float(
                    self._calculate_max_score(complete_dice, available_categories)
                )
            else:  # This is roll 1, we need to find the optimal keep decision for roll 2
                outcome_score = self._find_best_keep_decision(
                    complete_dice, roll_number + 1, available_categories
                )

            total_score += outcome_score

        # Calculate the expected value and cache it
        ev = total_score / total_outcomes
        self.ev_cache[cache_key] = ev

        return ev

    def _find_best_keep_decision(
        self,
        current_dice: List[int],
        next_roll_number: int,
        available_categories: List[ScorecardCategory],
    ) -> float:
        """Find the best dice to keep for the next roll."""
        # If we're already on roll 3, just score the dice
        if next_roll_number >= 3:
            return self._calculate_max_score(current_dice, available_categories)

        # Create sorted dice for smarter pruning
        dice_counts = Counter(current_dice)

        # Try all possible subsets of dice to keep (2^5 = 32 possibilities)
        best_ev = 0.0

        # Each mask represents a different subset of dice to keep
        for keep_mask in range(1 << len(current_dice)):
            # Get the indices of dice to keep based on the binary mask
            keep_indices = {i for i in range(len(current_dice)) if (keep_mask >> i) & 1}
            kept_dice = [current_dice[i] for i in keep_indices]

            # Calculate EV for this keep decision
            keep_ev = self._calculate_ev_for_roll(
                kept_dice, next_roll_number, available_categories
            )

            # Update our best EV if this is better
            if keep_ev > best_ev:
                best_ev = keep_ev

        return best_ev

    def select_dice_to_keep(
        self,
        current_dice: List[int],
        scorecard: Scorecard,
        debug: bool = False,
        top_n: int = 5,
    ) -> Set[int]:
        """
        Choose which dice to keep based on expected value calculations.

        Args:
            current_dice: List of current dice values
            scorecard: Current scorecard state
            debug: If True, print basic information about top decisions
            debug: If True, print comprehensive stats and distribution analysis
            top_n: Number of top decisions to show when debugging (default: 5)

        Returns:
            Set of indices of dice to keep
        """
        # Clear cache at the start of a new decision
        self.ev_cache = {}

        # If this is the third roll, keep all dice
        if scorecard.current_roll >= 3:
            if debug or debug:
                print("Roll 3: Always keeping all dice")
            return set(range(len(current_dice)))

        # Get available categories
        available_categories = [
            cat for cat in self.all_categories if scorecard.get_score(cat) is None
        ]

        # Track top decisions with their EVs
        all_decisions = []  # Will store (indices, kept_dice, ev) tuples

        # Try all possible subsets of dice to keep
        for keep_mask in range(1 << len(current_dice)):
            # Get the indices of dice to keep based on the binary mask
            keep_indices = {i for i in range(len(current_dice)) if (keep_mask >> i) & 1}
            kept_dice = [current_dice[i] for i in keep_indices]

            # Calculate EV for this keep decision
            keep_ev = self._calculate_ev_for_roll(
                kept_dice, scorecard.current_roll, available_categories
            )

            # Add to all decisions
            all_decisions.append((keep_indices, kept_dice, keep_ev))

        # Sort by EV in descending order
        all_decisions.sort(key=lambda x: x[2], reverse=True)

        # Take top N (or fewer if there aren't that many decisions)
        top_decisions = all_decisions[:top_n]

        # Print debug information if requested
        if debug:
            print("\n===== TOP KEEP DECISIONS =====")
            print(f"Current dice: {current_dice}")
            print(f"Roll number: {scorecard.current_roll}")
            print(f"Available categories: {[cat.name for cat in available_categories]}")
            print("\nTop decisions:")

            for i, (indices, kept, ev) in enumerate(top_decisions):
                # Format the indices being kept
                indices_str = ", ".join(str(idx) for idx in sorted(indices))

                # Format the kept dice
                kept_str = str(kept) if kept else "[]"

                # Calculate what would be rerolled
                reroll = [
                    current_dice[i]
                    for i in range(len(current_dice))
                    if i not in indices
                ]
                reroll_str = str(reroll) if reroll else "[]"

                # Print the decision details
                print(
                    f"#{i+1}: Keep {kept_str}, reroll {reroll_str}, indices [{indices_str}], EV: {ev:.2f}"
                )

                # If detailed debug is enabled, show outcome analysis for top decisions
                if debug and i < 3:  # Analyze top 3 decisions
                    dice_to_roll = 5 - len(kept)

                    # Calculate all possible outcomes for this keep decision
                    if (
                        dice_to_roll <= 3
                    ):  # Only do exhaustive analysis for 3 or fewer dice
                        all_outcomes = []
                        zero_count = 0
                        total_outcomes = 6**dice_to_roll

                        # Generate all possible roll outcomes
                        for roll_outcome in itertools.product(
                            range(1, 7), repeat=dice_to_roll
                        ):
                            complete_dice = kept + list(roll_outcome)
                            max_score = self._calculate_max_score(
                                complete_dice, available_categories
                            )
                            best_cat = max(
                                available_categories,
                                key=lambda c: self._calculate_score_for_category(
                                    complete_dice, c
                                ),
                            )

                            # Track zero-point outcomes
                            if max_score == 0:
                                zero_count += 1

                            all_outcomes.append(
                                (roll_outcome, complete_dice, best_cat, max_score)
                            )

                        # Sort outcomes by score (highest first)
                        all_outcomes.sort(key=lambda x: x[3], reverse=True)

                        # Show statistics about outcome distribution
                        scores = [outcome[3] for outcome in all_outcomes]

                        # Calculate percentiles
                        percentiles = {
                            "25th": scores[int(len(scores) * 0.25)],
                            "50th (median)": scores[int(len(scores) * 0.5)],
                            "75th": scores[int(len(scores) * 0.75)],
                            "90th": scores[int(len(scores) * 0.9)],
                        }

                        # Create score distribution buckets
                        buckets: Dict[int, int] = {}
                        for score in scores:
                            bucket = (
                                score // 10 * 10
                            )  # Group by tens (0-9, 10-19, etc.)
                            buckets[bucket] = buckets.get(bucket, 0) + 1

                        # Print outcome statistics
                        print(
                            f"  Outcome Analysis (for {total_outcomes} possible rolls):"
                        )
                        print(
                            f"    - Zero-point outcomes: {zero_count} ({zero_count/total_outcomes:.1%})"
                        )
                        print(
                            f"    - Percentiles: {', '.join(f'{k}: {v}' for k, v in percentiles.items())}"
                        )

                        # Print score distribution
                        print("    - Score distribution:")
                        for bucket in sorted(buckets.keys()):
                            count = buckets[bucket]
                            percentage = count / total_outcomes
                            bar_length = int(
                                percentage * 40
                            )  # Scale to make bars reasonable length
                            print(
                                f"      {bucket:3d}-{bucket+9:<3d}: {count:4d} ({percentage:.1%}) {'█' * bar_length}"
                            )

                        # Show the best possible outcomes
                        print("    - Top 3 possible outcomes:")
                        for j, (roll, complete, cat, score) in enumerate(
                            all_outcomes[:3]
                        ):
                            print(
                                f"      → Roll {list(roll)} → Complete {complete} → Best: {cat.name} ({score} pts)"
                            )

                        # Show median outcome
                        median_idx = len(all_outcomes) // 2
                        print("    - Median outcome:")
                        roll, complete, cat, score = all_outcomes[median_idx]
                        print(
                            f"      → Roll {list(roll)} → Complete {complete} → Best: {cat.name} ({score} pts)"
                        )

                    else:
                        print(
                            f"  Outcome analysis skipped (too many combinations for {dice_to_roll} dice)"
                        )

            print("=============================\n")

        # Return the indices from the best decision
        return top_decisions[0][0] if top_decisions else set()

    def select_category(
        self, dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> ScorecardCategory:
        """
        Advanced category selection that considers expected value of future turns.
        This is a more sophisticated version that could be used in future strategy improvements.

        Args:
            dice: Current dice values
            scorecard: Current scorecard of the player
            debug: If True, print information about the decision process

        Returns:
            Category to score in
        """
        # Get available categories
        available_categories = [
            cat for cat in self.all_categories if scorecard.get_score(cat) is None
        ]

        if not available_categories:
            raise ValueError("No available categories to select")

        # Calculate the immediate score for each category
        category_values = []
        for category in available_categories:
            immediate_score = self._calculate_score_for_category(dice, category)

            # For each category, calculate the EV cost of using it now
            # This is done by comparing the score we get now with the expected value
            # we'd get if we saved this category for a future turn

            # Make a copy of available categories without this one
            remaining_categories = [
                cat for cat in available_categories if cat != category
            ]

            # If this is the last category, there's no opportunity cost
            if not remaining_categories:
                opportunity_cost = 0
            else:
                # A simple approximation of the EV for this category in future turns
                # This could be made more sophisticated with actual EV calculations
                if category in self.high_value_categories:
                    # High value categories have higher opportunity cost
                    opportunity_cost = 25 if immediate_score == 0 else 10
                elif category in self.upper_categories:
                    # Upper categories opportunity cost depends on the die value
                    die_value = self.upper_categories.index(category) + 1
                    opportunity_cost = (
                        die_value * 3
                    )  # Assume average 3 of this die in future
                    opportunity_cost = max(0, opportunity_cost - immediate_score)
                else:
                    # Other lower categories
                    opportunity_cost = 15 if immediate_score == 0 else 5

            # Calculate the adjusted value
            adjusted_value = immediate_score - opportunity_cost

            category_values.append(
                (category, immediate_score, opportunity_cost, adjusted_value)
            )

        # Sort by adjusted value (highest first)
        category_values.sort(key=lambda x: x[3], reverse=True)

        if debug:
            print("\n===== CATEGORY SELECTION =====")
            print(f"Current dice: {dice}")
            print("Category options:")
            for cat, score, cost, adj_value in category_values:
                print(
                    f"  {cat.name}: Score {score}, Opportunity Cost {cost}, Adjusted Value {adj_value}"
                )

        # Select the category with highest adjusted value
        best_category = category_values[0][0]

        if debug:
            print(
                f"Selected {best_category.name} with adjusted value {category_values[0][3]}"
            )
            print("=============================\n")

        return best_category
