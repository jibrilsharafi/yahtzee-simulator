from typing import Dict, List, Optional


class Scorecard:
    def __init__(self) -> None:
        self.scores: Dict[str, Optional[int]] = {
            "Ones": None,
            "Twos": None,
            "Threes": None,
            "Fours": None,
            "Fives": None,
            "Sixes": None,
            "Three of a Kind": None,
            "Four of a Kind": None,
            "Full House": None,
            "Small Straight": None,
            "Large Straight": None,
            "Yahtzee": None,
            "Chance": None,
        }

    def get_score(self, category: str) -> Optional[int]:
        return self.scores.get(category)

    def set_score(self, category: str, value: int) -> None:
        if category not in self.scores:
            raise ValueError(f"Invalid category: {category}")
        if self.scores[category] is not None:
            raise ValueError(f"Category {category} already scored")
        self.scores[category] = value

    def get_total_score(self) -> int:
        # Calculate upper section bonus
        upper_section = ["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"]
        upper_total = sum(self.scores[category] or 0 for category in upper_section)
        bonus = 35 if upper_total >= 63 else 0

        # Calculate total including bonus
        total = sum(score or 0 for score in self.scores.values()) + bonus
        return total

    def is_complete(self) -> bool:
        return all(score is not None for score in self.scores.values())

    def calculate_score(self, category: str, dice: List[int]) -> int:
        if category == "Ones":
            return sum(d for d in dice if d == 1)
        elif category == "Twos":
            return sum(d for d in dice if d == 2)
        elif category == "Threes":
            return sum(d for d in dice if d == 3)
        elif category == "Fours":
            return sum(d for d in dice if d == 4)
        elif category == "Fives":
            return sum(d for d in dice if d == 5)
        elif category == "Sixes":
            return sum(d for d in dice if d == 6)
        elif category == "Three of a Kind":
            for i in range(1, 7):
                if dice.count(i) >= 3:
                    return sum(dice)
            return 0
        elif category == "Four of a Kind":
            for i in range(1, 7):
                if dice.count(i) >= 4:
                    return sum(dice)
            return 0
        elif category == "Full House":
            has_three = False
            has_two = False
            for i in range(1, 7):
                if dice.count(i) == 3:
                    has_three = True
                elif dice.count(i) == 2:
                    has_two = True
            return 25 if has_three and has_two else 0
        elif category == "Small Straight":
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
        elif category == "Large Straight":
            sorted_dice = sorted(set(dice))
            return (
                40
                if sorted_dice == [1, 2, 3, 4, 5] or sorted_dice == [2, 3, 4, 5, 6]
                else 0
            )
        elif category == "Yahtzee":
            return 50 if any(dice.count(i) == 5 for i in range(1, 7)) else 0
        elif category == "Chance":
            return sum(dice)
        else:
            raise ValueError(f"Invalid category: {category}")
