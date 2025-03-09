class BaseStrategy:
    def select_dice_to_keep(self, current_dice, player_score):
        """
        Selects which dice to keep based on the current state of the game.
        
        :param current_dice: List of current dice values.
        :param player_score: Current score of the player.
        :return: List of dice values to keep.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")

    def score(self, kept_dice, player_score):
        """
        Calculates the score based on the kept dice.
        
        :param kept_dice: List of dice values that are kept.
        :param player_score: Current score of the player.
        :return: Score to be added to the player's score.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")