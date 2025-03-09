import unittest
from unittest.mock import MagicMock
from src.game.player import Player
from src.game.scorecard import Scorecard

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player("TestPlayer")
    
    def test_init(self):
        self.assertEqual(self.player.name, "TestPlayer")
        self.assertIsInstance(self.player.scorecard, Scorecard)
    
    def test_get_total_score(self):
        # Create a mock for the scorecard
        mock_scorecard = MagicMock()
        mock_scorecard.get_total_score.return_value = 150
        
        # Replace the player's scorecard with our mock
        self.player.scorecard = mock_scorecard
        
        # Test that get_total_score delegates to the scorecard
        self.assertEqual(self.player.get_total_score(), 150)
        mock_scorecard.get_total_score.assert_called_once()

if __name__ == '__main__':
    unittest.main()
