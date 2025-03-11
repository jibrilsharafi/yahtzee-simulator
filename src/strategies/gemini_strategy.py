import os
import random
from typing import Any, Dict, List, Optional, Set

import google.generativeai as genai

from src.game.scorecard import Scorecard, ScorecardCategory
from src.strategies.base_strategy import BaseStrategy


class GeminiStrategy(BaseStrategy):
    def __init__(self, api_key: str) -> None:
        """Initialize the Gemini 2 Flash Strategy with API configuration."""
        self.api_key = api_key

        genai.configure(api_key=self.api_key)
        # Use Gemini 2.0 Flash if available, fall back to Gemini Pro
        self.model_name = "models/gemini-2.0-flash"
        list_available_models = [model.name for model in genai.list_models()]
        assert (
            self.model_name in list_available_models
        ), f"{self.model_name} is not available. Available models: {list_available_models}"
        self.model = genai.GenerativeModel(self.model_name)

    def _scorecard_to_dict(self, scorecard: Scorecard) -> Dict[str, Optional[int]]:
        """Convert Scorecard object to dictionary for API prompt."""
        scoreboard = {}
        for category in ScorecardCategory:
            category_name = category.name
            if scorecard.is_category_filled(category):
                scoreboard[category_name] = scorecard.get_score(category)
            else:
                scoreboard[category_name] = None
        return scoreboard

    def _category_name_to_enum(self, category_name: str) -> ScorecardCategory:
        """Convert category name string to ScorecardCategory enum."""
        try:
            return ScorecardCategory[category_name]
        except KeyError:
            # Default to CHANCE if category name is invalid
            return ScorecardCategory.CHANCE

    def select_dice_to_keep(
        self, current_dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> Set[int]:
        """Use Gemini to decide which dice to keep."""
        # Convert scorecard to dictionary for the prompt
        scoreboard = self._scorecard_to_dict(scorecard)

        available_categories_str = [
            cat.value.upper()
            for cat in ScorecardCategory
            if not scorecard.is_category_filled(cat)
        ]

        if scorecard.current_roll >= 3:
            # If no rolls remaining, keep all dice
            return set(range(len(current_dice)))

        # Get rolls remaining
        rolls_remaining = 3 - scorecard.current_roll

        # Construct prompt for Gemini
        prompt = f"""You are an expert Yahtzee player. Your goal is to maximize your score.

The points for each category are as follows:
- ONES: 1 point for each 1
- TWOS: 2 points for each 2
- THREES: 3 points for each 3
- FOURS: 4 points for each 4
- FIVES: 5 points for each 5
- SIXES: 6 points for each 6
- THREE_OF_A_KIND: Sum of all dice if at least three are the same
- FOUR_OF_A_KIND: Sum of all dice if at least four are the same
- FULL_HOUSE: 25 points if there are three of one number and two of another
- SMALL_STRAIGHT: 30 points for a sequence of four numbers
- LARGE_STRAIGHT: 40 points for a sequence of five numbers
- YAHTZEE: 50 points for five of a kind
- CHANCE: Sum of all dice, no restrictions

The current state is as follows:
- Current Dice: {current_dice}
- Rolls Remaining: {rolls_remaining} (so we are on the {scorecard.current_roll} roll)
- Available Categories: {available_categories_str}

Here's how the scoreboard works:
- Each category can only be scored once.
- If a category is None, it's available to be scored.
- Otherwise, the category has already been scored with the given value.

Your objective is to decide which dice to re-roll to maximize your expected score.

Given the current game state, which dice (by their index, starting at 0) do you want to re-roll to maximize your expected score?

Respond with a list of the indices of the dice to keep, in the format [0, 1, 2]. If no dice should be kept and we should re-roll all, respond with an empty list [].
Please explain your reasoning in detail. To help you, here are some examples of how to respond:

*REASONING PART*
Given the current dice and rolls remaining, ...

*CONCLUSION PART*
To sum up, ...

Result: !!![0, 1, 2]!!! 
"""

        if debug:
            print(f"\n========== Prompt for dice selection:\n\n{prompt}")

        try:
            response = self.model.generate_content(prompt)
            answer = response.text
            if debug:
                print(f"\n========== Gemini Response: \n\n{answer}")

            # Parse the indices to re-roll
            keep_indices = self._parse_indices(answer)

            if debug:
                print(f"Dice to keep (indices): {keep_indices}")

            return set(keep_indices)

        except Exception as e:
            if debug:
                print(f"Error during Gemini API call: {e}")
            # Default: Keep all dice in case of error
            return set(range(len(current_dice)))

    def select_category(
        self, dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> ScorecardCategory:
        """Use Gemini to select which category to score in."""
        available_categories_str = [
            cat.value for cat in scorecard.get_available_categories()
        ]

        # Construct prompt for Gemini
        prompt = f"""You are an expert Yahtzee player. Your goal is to maximize your score.

The points for each category are as follows:
- ONES: 1 point for each 1
- TWOS: 2 points for each 2
- THREES: 3 points for each 3
- FOURS: 4 points for each 4
- FIVES: 5 points for each 5
- SIXES: 6 points for each 6
- THREE_OF_A_KIND: Sum of all dice if at least three are the same
- FOUR_OF_A_KIND: Sum of all dice if at least four are the same
- FULL_HOUSE: 25 points if there are three of one number and two of another
- SMALL_STRAIGHT: 30 points for a sequence of four numbers
- LARGE_STRAIGHT: 40 points for a sequence of five numbers
- YAHTZEE: 50 points for five of a kind
- CHANCE: Sum of all dice, no restrictions

The current state is as follows:
- Final Dice: {dice}
- Available Categories: {available_categories_str}

Your objective is to decide which category to score in to maximize your overall expected score.

Given the current dice and available categories, which category should be scored?

Respond with the exact name of one category from the available categories list.

Please explain your reasoning in detail. To help you, here are some examples of how to respond:

*REASONING PART*
Given the current dice and rolls remaining, ...

*CONCLUSION PART*
To sum up, ...

Result: !!!LARGE_STRAIGHT!!! 
"""
        if debug:
            print(f"\n========== Prompt for category selection:\n\n{prompt}")

        try:
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            if debug:
                print(f"\n========== Gemini Response: \n\n{answer}")

            # Try to find the category in the available categories
            for category_str in available_categories_str:
                if category_str.upper() == answer.upper():
                    return self._category_name_to_enum(category_str.upper())

            # If no match is found, use the first available category
            if available_categories_str:
                return self._category_name_to_enum(available_categories_str[0].upper())
            else:
                # Fallback to a random available category
                return random.choice(scorecard.get_available_categories())

        except Exception as e:
            if debug:
                print(f"Error during Gemini API call: {e}")

            return random.choice(scorecard.get_available_categories())

    def _parse_indices(self, text: str) -> List[int]:
        """Parse Gemini's text response to extract indices."""
        try:
            # Find the text between !!! and !!!
            start = text.index("!!!") + 3
            end = text.rindex("!!!")
            indices_str = text[start:end].strip()
            # Convert to list of integers
            indices = list(map(int, indices_str.strip("[]").split(",")))
            return indices
        except (ValueError, IndexError):
            # If parsing fails, return an empty list
            print(f"Error parsing indices from Gemini response: {text}")
            return []
        except Exception as e:
            # Handle any other exceptions
            print(f"Error parsing indices: {e}")
            return []
