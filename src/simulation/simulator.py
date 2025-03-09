class Simulator:
    def __init__(self):
        self.results = []

    def run_simulation(self, strategy, game_state, dice_roll):
        kept_dice, score = strategy.select_dice_to_keep(game_state, dice_roll)
        self.results.append({
            'kept_dice': kept_dice,
            'score': score
        })
        return kept_dice, score

    def get_results(self):
        return self.results