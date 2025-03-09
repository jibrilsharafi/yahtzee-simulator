class YahtzeeGame:
    def __init__(self):
        self.players = []
        self.current_player_index = 0
        self.dice = [0] * 5
        self.rounds = 13
        self.scorecard = None  # This will be an instance of Scorecard

    def add_player(self, player_name):
        self.players.append(player_name)

    def roll_dice(self, dice_to_roll=None):
        import random
        if dice_to_roll is None:
            dice_to_roll = range(5)
        for i in dice_to_roll:
            self.dice[i] = random.randint(1, 6)

    def get_current_player(self):
        return self.players[self.current_player_index]

    def score_turn(self, strategy, rolled_dice):
        keep_dice, score = strategy.select_dice_and_score(self.get_current_player(), rolled_dice)
        # Update the scorecard and other game state here

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def play_game(self):
        for _ in range(self.rounds):
            for player in self.players:
                self.roll_dice()
                # Implement turn logic here
                self.next_turn()

    def determine_winner(self):
        # Logic to determine the winner based on the scorecard
        pass