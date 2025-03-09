import unittest
from src.game.yahtzee_game import YahtzeeGame
from src.game.scorecard import Scorecard
from src.game.dice import Dice

class TestYahtzeeGame(unittest.TestCase):

    def setUp(self):
        self.game = YahtzeeGame()
        self.scorecard = Scorecard()

    def test_initial_state(self):
        self.assertEqual(len(self.game.players), 0)
        self.assertEqual(self.game.current_turn, 0)

    def test_add_player(self):
        self.game.add_player("Alice")
        self.assertEqual(len(self.game.players), 1)
        self.assertEqual(self.game.players[0].name, "Alice")

    def test_roll_dice(self):
        self.game.add_player("Bob")
        self.game.roll_dice()
        self.assertEqual(len(self.game.current_roll), 5)

    def test_score_selection(self):
        self.game.add_player("Charlie")
        self.game.roll_dice()
        initial_score = self.scorecard.get_score("Ones")
        self.game.select_score("Ones")
        new_score = self.scorecard.get_score("Ones")
        self.assertNotEqual(initial_score, new_score)

    def test_winner_determination(self):
        self.game.add_player("Alice")
        self.game.add_player("Bob")
        self.game.roll_dice()
        self.game.select_score("Ones")
        self.game.roll_dice()
        self.game.select_score("Twos")
        winner = self.game.determine_winner()
        self.assertIn(winner, ["Alice", "Bob"])

if __name__ == '__main__':
    unittest.main()