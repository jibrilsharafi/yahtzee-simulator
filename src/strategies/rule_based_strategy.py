from typing import List, Set, Tuple
from collections import Counter
from src.strategies.base_strategy import BaseStrategy
from src.game.scorecard import Scorecard, ScorecardCategory


class RuleBasedStrategy(BaseStrategy):
    def select_dice_to_keep(
        self, current_dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> Set[int]:
        """
        Selects which dice to keep based on a rule-based approach.

        :param current_dice: List of current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Set of indices of dice to keep.
        """
        # Count occurrences of each value
        counts = Counter(current_dice)
        most_common = counts.most_common()

        # Find the highest count
        highest_count = most_common[0][1] if most_common else 0

        if highest_count >= 2:  # If we have at least a pair
            # Find all values that appear with the highest count
            highest_count_values = [
                value for value, count in most_common if count == highest_count
            ]

            # Choose the highest value among them
            value_to_keep = max(highest_count_values)

            # Keep all dice with that value
            return {i for i, v in enumerate(current_dice) if v == value_to_keep}

        # Check for potential straights
        sorted_unique = sorted(set(current_dice))

        # If we have 4 unique consecutive numbers, keep them
        if self._is_potential_straight(sorted_unique):
            return {
                i
                for i, v in enumerate(current_dice)
                if v in sorted_unique and sorted_unique.count(v) == 1
            }

        # Otherwise, keep high values
        return {i for i, v in enumerate(current_dice) if v >= 4}

    def _is_potential_straight(self, values: List[int]) -> bool:
        """Check if the values could form a straight."""
        if len(values) < 3:
            return False

        # Check for consecutive values
        for i in range(len(values) - 2):
            if values[i + 1] == values[i] + 1 and values[i + 2] == values[i] + 2:
                return True

        return False

    def select_category(
        self, dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> ScorecardCategory:
        """
        Selects the best category to score based on the current dice.

        :param dice: Current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Category name to score in.
        """
        # Calculate potential scores for each category
        potential_scores: dict[ScorecardCategory, int] = {}
        for category in scorecard.scores:
            if (
                scorecard.get_score(category) is None
            ):  # Only consider unscored categories
                potential_scores[category] = scorecard.calculate_score(category, dice)

        if not potential_scores:
            raise ValueError("No available categories to score")

        # Check if we have any high-scoring categories
        high_value_categories = [
            ScorecardCategory.YAHTZEE,
            ScorecardCategory.LARGE_STRAIGHT,
            ScorecardCategory.SMALL_STRAIGHT,
            ScorecardCategory.FULL_HOUSE,
        ]
        for category in high_value_categories:
            if category in potential_scores and potential_scores[category] > 0:
                return category

        # Find the category with the highest points per potential (upper section has long-term value)
        upper_section = {
            ScorecardCategory.ONES: 1,
            ScorecardCategory.TWOS: 2,
            ScorecardCategory.THREES: 3,
            ScorecardCategory.FOURS: 4,
            ScorecardCategory.FIVES: 5,
            ScorecardCategory.SIXES: 6,
        }
        best_category = None
        best_value = -1.0

        for category, score in potential_scores.items():
            # Give bonus to upper section categories to encourage completing them
            value = float(score)
            if category in upper_section:
                # Value efficiency - how close are we to maximizing this category
                max_possible = upper_section[category] * 5
                if max_possible > 0:
                    efficiency = score / max_possible
                    # Bonus for nearly complete upper section categories
                    if score >= upper_section[category] * 3:
                        value = score * 1.2

            if value > best_value:
                best_value = value
                best_category = category

        return (
            best_category
            if best_category
            else max(potential_scores.items(), key=lambda x: x[1])[0]
        )
