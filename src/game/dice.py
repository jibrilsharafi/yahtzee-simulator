import random
from typing import List, Set, Optional


class Dice:
    def __init__(self, num_dice: int = 5) -> None:
        self.values: List[int] = [1] * num_dice
        self.num_dice: int = num_dice

    def roll(self, indices: Optional[Set[int]] = None) -> List[int]:
        """Roll specified dice or all dice if indices is None"""
        indices_to_roll = range(self.num_dice) if indices is None else indices
        for i in indices_to_roll:
            if 0 <= i < self.num_dice:
                self.values[i] = random.randint(1, 6)
        return self.values

    def get_values(self) -> List[int]:
        return self.values
