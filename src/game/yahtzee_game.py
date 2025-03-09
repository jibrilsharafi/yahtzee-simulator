from typing import Any, Dict, List, Optional, Set

from src.game.dice import Dice
from src.game.player import Player
from src.strategies.base_strategy import BaseStrategy


class YahtzeeGame:
    def __init__(self) -> None:
        self.players: List[Player] = []
        self.current_player_index: int = 0
        self.current_turn: int = 0
        self.dice: Dice = Dice(5)
        self.current_roll: List[int] = []
        self.rounds: int = 13
        self.roll_count: int = 0
        self.max_rolls_per_turn: int = 3

    def add_player(self, player_name: str) -> None:
        self.players.append(Player(player_name))

    def roll_dice(self, dice_to_keep: Optional[Set[int]] = None) -> List[int]:
        if self.roll_count >= self.max_rolls_per_turn:
            raise ValueError("Cannot roll more than 3 times per turn")

        if dice_to_keep is None:
            # Roll all dice
            self.current_roll = self.dice.roll()
        else:
            # Calculate indices to roll (all except the ones to keep)
            indices_to_roll = set(range(5)) - dice_to_keep
            self.current_roll = self.dice.roll(indices_to_roll)

        self.roll_count += 1
        return self.current_roll

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def select_score(self, category: str) -> int:
        if not self.current_roll:
            raise ValueError("Must roll dice before selecting a score")

        player = self.get_current_player()
        score = player.scorecard.calculate_score(category, self.current_roll)
        player.scorecard.set_score(category, score)

        # Reset for next turn
        self.roll_count = 0
        self.current_roll = []
        self.next_turn()

        return score

    def next_turn(self) -> None:
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.current_turn += 1

    def play_turn(self, strategy: BaseStrategy) -> None:
        # Reset roll count for new turn
        self.roll_count = 0

        # First roll
        self.roll_dice()

        # Allow up to 2 more rolls with dice selection
        for _ in range(2):
            if self.roll_count >= 3:
                break

            dice_to_keep = strategy.select_dice_to_keep(
                self.current_roll, self.get_current_player().scorecard
            )
            if len(dice_to_keep) == 5:  # Player wants to keep all dice
                break

            indices_to_keep = {
                i for i, val in enumerate(self.current_roll) if i in dice_to_keep
            }
            self.roll_dice(indices_to_keep)

        # Select category to score
        category = strategy.select_category(
            self.current_roll, self.get_current_player().scorecard
        )
        self.select_score(category)

    def play_game(self, strategies: Dict[str, BaseStrategy]) -> None:
        while not self.is_game_over():
            current_player = self.get_current_player()
            strategy = strategies.get(current_player.name)
            if strategy:
                self.play_turn(strategy)

    def determine_winner(self) -> str:
        if not self.players:
            raise ValueError("No players in the game")

        max_score = -1
        winner = ""

        for player in self.players:
            score = player.get_total_score()
            if score > max_score:
                max_score = score
                winner = player.name

        return winner

    def is_game_over(self) -> bool:
        if not self.players:
            return False

        # Game is over when all players have completed their scorecard
        return all(player.scorecard.is_complete() for player in self.players)

    def current_player(self) -> Player:
        return self.get_current_player()

    def get_current_state(self) -> Dict[str, Any]:
        return {
            "current_roll": self.current_roll,
            "current_player": self.get_current_player(),
            "roll_count": self.roll_count,
            "turn": self.current_turn,
        }

    def update_game_state(self, dice_to_keep: Set[int], category: str) -> None:
        if self.roll_count < self.max_rolls_per_turn and len(dice_to_keep) < 5:
            self.roll_dice(dice_to_keep)
        else:
            self.select_score(category)

    def get_winner(self) -> str:
        return f"The winner is {self.determine_winner()}!"
