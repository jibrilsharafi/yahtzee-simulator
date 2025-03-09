import random
from typing import List, Set, Dict, Any
from src.strategies.base_strategy import BaseStrategy
from src.game.scorecard import Scorecard

class RandomStrategy(BaseStrategy):
    def select_dice_to_keep(self, current_dice: List[int], scorecard: Scorecard) -> Set[int]:
        """
        Randomly selects which dice to keep.
        
        :param current_dice: List of current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Set of indices of dice to keep.
        """
        # Randomly decide how many dice to keep
        num_to_keep = random.randint(0, len(current_dice))
        # Randomly select indices to keep
        return set(random.sample(range(len(current_dice)), num_to_keep))

    def select_category(self, dice: List[int], scorecard: Scorecard) -> str:
        """
        Randomly selects an unscored category.
        
        :param dice: Current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Category name to score in.
        """
        # Get all unscored categories
        available_categories = [category for category, score in scorecard.scores.items() 
                                if score is None]
        
        if not available_categories:
            raise ValueError("No available categories to score")
            
        # Randomly select one
        return random.choice(available_categories)