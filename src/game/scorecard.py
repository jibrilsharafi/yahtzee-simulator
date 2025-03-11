from typing import Dict, List, Optional
from enum import Enum, auto


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

    def set_score(self, category: ScorecardCategory, value: int) -> None:
        if category not in self.scores:
            raise ValueError(f"Invalid category: {category}")
        if self.scores[category] is not None:
            raise ValueError(f"Category {category} already scored")
        self.scores[category] = value
        self.current_roll = 1  # Reset roll counter after scoring

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

        # Calculate total including bonus
        total = sum(score or 0 for score in self.scores.values()) + bonus
        return total

    def is_complete(self) -> bool:
        return all(score is not None for score in self.scores.values())

    def calculate_score(self, category: ScorecardCategory, dice: List[int]) -> int:
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
                if dice.count(i) >= 3:
                    return sum(dice)
            return 0
        elif category == ScorecardCategory.FOUR_OF_A_KIND:
            for i in range(1, 7):
                if dice.count(i) >= 4:
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
            return 25 if has_three and has_two else 0
        elif category == ScorecardCategory.SMALL_STRAIGHT:
            sorted_dice = sorted(set(dice))
            if len(sorted_dice) >= 4 and (
                sorted_dice == [1, 2, 3, 4]
                or sorted_dice == [2, 3, 4, 5]
                or sorted_dice == [3, 4, 5, 6]
                or [1, 2, 3, 4] == sorted_dice[:4]
                or [2, 3, 4, 5] == sorted_dice[:4]
                or [3, 4, 5, 6] == sorted_dice[:4]
                or [1, 2, 3, 4] == sorted_dice[-4:]
                or [2, 3, 4, 5] == sorted_dice[-4:]
                or [3, 4, 5, 6] == sorted_dice[-4:]
            ):
                return 30
            return 0
        elif category == ScorecardCategory.LARGE_STRAIGHT:
            sorted_dice = sorted(dice)
            return (
                40
                if sorted_dice == [1, 2, 3, 4, 5] or sorted_dice == [2, 3, 4, 5, 6]
                else 0
            )
        elif category == ScorecardCategory.YAHTZEE:
            return 50 if any(dice.count(i) == 5 for i in range(1, 7)) else 0
        elif category == ScorecardCategory.CHANCE:
            return sum(dice)
        else:
            raise ValueError(f"Invalid category: {category}")
