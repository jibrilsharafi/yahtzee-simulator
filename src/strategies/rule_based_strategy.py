from typing import List, Set, Dict, Any, Tuple
from collections import Counter
from src.strategies.base_strategy import BaseStrategy
from src.game.scorecard import Scorecard

class RuleBasedStrategy(BaseStrategy):
    def select_dice_to_keep(self, current_dice: List[int], scorecard: Scorecard) -> Set[int]:
        """
        Selects which dice to keep based on a rule-based approach.
        
        :param current_dice: List of current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Set of indices of dice to keep.
        """
        # Count occurrences of each value
        counts = Counter(current_dice)
        most_common = counts.most_common()
        
        # Try to build sets (pairs, three of a kind, etc.)
        if most_common[0][1] >= 2:  # If we have at least a pair
            value_to_keep = most_common[0][0]
            return {i for i, v in enumerate(current_dice) if v == value_to_keep}
        
        # Otherwise, keep high values
        return {i for i, v in enumerate(current_dice) if v >= 4}

    def select_category(self, dice: List[int], scorecard: Scorecard) -> str:
        """
        Selects the best category to score based on the current dice.
        
        :param dice: Current dice values.
        :param scorecard: Current scorecard of the player.
        :return: Category name to score in.
        """
        # Calculate potential scores for each category
        potential_scores = {}
        for category in scorecard.scores:
            if scorecard.get_score(category) is None:  # Only consider unscored categories
                potential_scores[category] = scorecard.calculate_score(category, dice)
        
        if not potential_scores:
            raise ValueError("No available categories to score")
            
        # Choose the category with the highest potential score
        return max(potential_scores.items(), key=lambda x: x[1])[0]