from typing import List, Set

from src.game.scorecard import Scorecard, ScorecardCategory


class BaseStrategy:
    def select_dice_to_keep(
        self, current_dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> Set[int]:
        """
        Selects which dice to keep based on the current state of the game.

        :param current_dice: List of current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Set of indices of dice to keep.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")

    def select_category(
        self, dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> ScorecardCategory:
        """
        Selects which category to score in.

        :param dice: Current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Category name to score in.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
