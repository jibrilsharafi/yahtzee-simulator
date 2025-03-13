from enum import Enum, auto
from typing import Dict, List, Optional


class ScorecardCategory(Enum):
    # Upper section
    ONES = "ones"
    TWOS = "twos"
    THREES = "threes"
    FOURS = "fours"
    FIVES = "fives"
    SIXES = "sixes"
    # Lower section
    THREE_OF_A_KIND = "three_of_a_kind"
    FOUR_OF_A_KIND = "four_of_a_kind"
    FULL_HOUSE = "full_house"
    SMALL_STRAIGHT = "small_straight"
    LARGE_STRAIGHT = "large_straight"
    YAHTZEE = "yahtzee"
    CHANCE = "chance"


def scorecard_from_string(category_str: str) -> "ScorecardCategory":
    """Convert a string to a ScorecardCategory enum."""
    try:
        return ScorecardCategory[category_str.upper()]
    except KeyError:
        raise ValueError(f"Invalid category string: {category_str}")
    return None


class Scorecard:
    def __init__(self) -> None:
        # Initialize scores dictionary with None values for all categories
        self.scores: Dict[ScorecardCategory, Optional[int]] = {
            category: None for category in ScorecardCategory
        }
        self.current_roll = 1  # Track the current roll number (1-3)
        self.yahtzee_bonus_count = 0  # Track additional Yahtzees

    def get_available_categories(self) -> List[ScorecardCategory]:
        """Get a list of categories that are not yet filled."""
        return [cat for cat, score in self.scores.items() if score is None]

    def get_filled_categories(self) -> List[ScorecardCategory]:
        """Get a list of categories that are already filled."""
        return [cat for cat, score in self.scores.items() if score is not None]

    def is_category_filled(self, category: ScorecardCategory) -> bool:
        return self.scores.get(category) is not None

    def get_score(self, category: ScorecardCategory) -> Optional[int]:
        return self.scores.get(category)

    def is_complete(self) -> bool:
        return all(score is not None for score in self.scores.values())

    @staticmethod
    def calculate_score(
        category: ScorecardCategory, dice: List[int], is_yahtzee: bool = False
    ) -> int:
        if category == ScorecardCategory.ONES:
            return sum(d for d in dice if d == 1)
        elif category == ScorecardCategory.TWOS:
            return sum(d for d in dice if d == 2)
        elif category == ScorecardCategory.THREES:
            return sum(d for d in dice if d == 3)
        elif category == ScorecardCategory.FOURS:
            return sum(d for d in dice if d == 4)
        elif category == ScorecardCategory.FIVES:
            return sum(d for d in dice if d == 5)
        elif category == ScorecardCategory.SIXES:
            return sum(d for d in dice if d == 6)
        elif category == ScorecardCategory.THREE_OF_A_KIND:
            for i in range(1, 7):
                if dice.count(i) >= 3 or is_yahtzee:
                    return sum(dice)
            return 0
        elif category == ScorecardCategory.FOUR_OF_A_KIND:
            for i in range(1, 7):
                if dice.count(i) >= 4 or is_yahtzee:
                    return sum(dice)
            return 0
        elif category == ScorecardCategory.FULL_HOUSE:
            has_three = False
            has_two = False
            for i in range(1, 7):
                if dice.count(i) == 3:
                    has_three = True
                elif dice.count(i) == 2:
                    has_two = True
            return 25 if (has_three and has_two) or is_yahtzee else 0
        elif category == ScorecardCategory.SMALL_STRAIGHT:
            sorted_dice = sorted(set(dice))
            if (
                len(sorted_dice) >= 4
                and (
                    sorted_dice == [1, 2, 3, 4]
                    or sorted_dice == [2, 3, 4, 5]
                    or sorted_dice == [3, 4, 5, 6]
                    or [1, 2, 3, 4] == sorted_dice[:4]
                    or [2, 3, 4, 5] == sorted_dice[:4]
                    or [3, 4, 5, 6] == sorted_dice[:4]
                    or [1, 2, 3, 4] == sorted_dice[-4:]
                    or [2, 3, 4, 5] == sorted_dice[-4:]
                    or [3, 4, 5, 6] == sorted_dice[-4:]
                )
            ) or is_yahtzee:
                return 30
            return 0
        elif category == ScorecardCategory.LARGE_STRAIGHT:
            sorted_dice = sorted(dice)
            return (
                40
                if sorted_dice == [1, 2, 3, 4, 5]
                or sorted_dice == [2, 3, 4, 5, 6]
                or is_yahtzee
                else 0
            )
        elif category == ScorecardCategory.YAHTZEE:
            return 50 if any(dice.count(i) == 5 for i in range(1, 7)) else 0
        elif category == ScorecardCategory.CHANCE:
            return sum(dice)
        else:
            raise ValueError(f"Invalid category: {category}")

    def is_yahtzee(self, dice: List[int]) -> bool:
        """Check if the dice roll is a Yahtzee (all five dice showing the same face)."""
        return len(set(dice)) == 1

    def score_additional_yahtzee(self, dice: List[int]) -> bool:
        """
        Check if an additional Yahtzee bonus should be scored.
        Returns True if a bonus was scored, False otherwise.
        """
        # Must be a Yahtzee roll
        if not self.is_yahtzee(dice):
            return False

        # Yahtzee category must be already filled with 50 points to get a bonus
        if self.scores.get(ScorecardCategory.YAHTZEE) != 50:
            return False

        # Increment bonus count and return True
        self.yahtzee_bonus_count += 1
        return True

    def get_yahtzee_bonus_score(self) -> int:
        """Get the total score from Yahtzee bonuses."""
        return self.yahtzee_bonus_count * 100

    def get_total_score(self) -> int:
        # Calculate upper section bonus
        upper_section = [
            ScorecardCategory.ONES,
            ScorecardCategory.TWOS,
            ScorecardCategory.THREES,
            ScorecardCategory.FOURS,
            ScorecardCategory.FIVES,
            ScorecardCategory.SIXES,
        ]
        upper_total = sum(self.scores[category] or 0 for category in upper_section)
        bonus = 35 if upper_total >= 63 else 0

        # Calculate total including regular scores, upper section bonus, and Yahtzee bonuses
        total = (
            sum(score or 0 for score in self.scores.values())
            + bonus
            + self.get_yahtzee_bonus_score()
        )
        return total

    def get_mandatory_category(self, dice: List[int]) -> Optional[ScorecardCategory]:
        """
        For a Yahtzee joker, determine if there's a mandatory category that must be filled.
        Returns the mandatory category or None if player has free choice.
        """
        if (
            not self.is_yahtzee(dice)
            or self.scores.get(ScorecardCategory.YAHTZEE) is None
        ):
            return None

        # Map die value to the corresponding upper section category
        die_value = dice[0]
        corresponding_categories = {
            1: ScorecardCategory.ONES,
            2: ScorecardCategory.TWOS,
            3: ScorecardCategory.THREES,
            4: ScorecardCategory.FOURS,
            5: ScorecardCategory.FIVES,
            6: ScorecardCategory.SIXES,
        }

        # If the corresponding upper section box is available, it must be used
        if die_value in corresponding_categories:
            category = corresponding_categories[die_value]
            if self.scores[category] is None:
                return category

        return None
    
    # To be used only if strictly necessary
    def set_score_raw(self, category: ScorecardCategory, score: int) -> None:
        """Set the score for a category directly."""
        if category not in self.scores:
            raise ValueError(f"Invalid category: {category}")
        if self.scores[category] is not None:
            raise ValueError(f"Category {category} already scored")
        self.scores[category] = score

    def set_score(self, category: ScorecardCategory, dice: List[int]) -> None:
        if category not in self.scores:
            raise ValueError(f"Invalid category: {category}")
        if self.scores[category] is not None:
            raise ValueError(f"Category {category} already scored")

        # Check for Yahtzee joker rules
        if self.is_yahtzee(dice) and self.scores.get(ScorecardCategory.YAHTZEE) == 50:
            # This is a Yahtzee joker situation
            die_value = dice[0]
            upper_category = {
                1: ScorecardCategory.ONES,
                2: ScorecardCategory.TWOS,
                3: ScorecardCategory.THREES,
                4: ScorecardCategory.FOURS,
                5: ScorecardCategory.FIVES,
                6: ScorecardCategory.SIXES,
            }[die_value]

            # Rule 1: If the corresponding upper section box is available, it MUST be used
            if self.scores[upper_category] is None and category != upper_category:
                raise ValueError(
                    f"For Yahtzee joker with {die_value}'s, you must use the {upper_category.value} category"
                )

            # Rule 2 & 3: If upper section is filled, allow any category (already handled by allowing the function to proceed)

            # Record the Yahtzee bonus
            self.yahtzee_bonus_count += 1

        # Calculate score based on the category and dice
        value = self.calculate_score(category, dice, self.is_yahtzee(dice))
        self.scores[category] = value
        self.current_roll = 1  # Reset roll counter after scoring
