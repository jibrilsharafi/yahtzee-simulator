class RuleBasedStrategy:
    def __init__(self):
        pass

    def select_dice_to_keep(self, current_game_state, rolled_dice):
        # Implement rule-based logic to decide which dice to keep
        # For example, keep all dice of the same value or pairs
        counts = {}
        for die in rolled_dice:
            counts[die] = counts.get(die, 0) + 1
        
        # Keep the highest count dice
        max_count = max(counts.values())
        dice_to_keep = [die for die, count in counts.items() if count == max_count]
        
        return dice_to_keep

    def score(self, current_game_state, rolled_dice):
        # Implement scoring logic based on the current game state and rolled dice
        # For example, return the score for a specific category
        score = 0
        # Example scoring logic (this should be expanded based on game rules)
        if len(set(rolled_dice)) == 1:  # Yahtzee
            score = 50
        elif len(set(rolled_dice)) == 2:  # Full house or four of a kind
            score = sum(rolled_dice)
        else:
            score = sum(rolled_dice)  # Simple sum for other cases
        
        return score