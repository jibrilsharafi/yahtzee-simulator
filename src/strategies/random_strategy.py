class RandomStrategy(BaseStrategy):
    import random

    def select_dice_to_keep(self, current_dice, roll):
        # Randomly decide which dice to keep
        keep_count = self.random.randint(1, len(roll))
        return self.random.sample(roll, keep_count)

    def score(self, kept_dice):
        # Simple scoring mechanism: return the sum of kept dice
        return sum(kept_dice)