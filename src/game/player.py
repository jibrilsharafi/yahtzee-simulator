from typing import Dict, Optional
from src.game.scorecard import Scorecard

class Player:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.scorecard: Scorecard = Scorecard()
        
    def get_total_score(self) -> int:
        return self.scorecard.get_total_score()
