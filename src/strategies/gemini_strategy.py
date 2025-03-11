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
            return set([i for i in range(len(current_dice))])

        # Get rolls remaining
        rolls_remaining = 3 - scorecard.current_roll

        # Construct prompt for Gemini
        prompt = f"""
            You are an expert Yahtzee player whose goal is to maximize score. You need to decide which dice to keep after this roll.
            
            CURRENT GAME STATE:
            - Current Dice: {current_dice}
            - Rolls Remaining: {rolls_remaining} (currently on roll #{scorecard.current_roll})
            - Available Categories: {available_categories_str}
            
            CRITICAL INSTRUCTION: You MUST ONLY consider strategies for the AVAILABLE CATEGORIES listed above. DO NOT aim for categories that aren't in this list as they have already been used.
            
            YAHTZEE STRATEGY GUIDELINES:
            1. Dice Retention Priority:
               - ONLY keep dice that contribute toward AVAILABLE categories - don't keep dice just for the sake of keeping them
               - Always keep sequences like 1-2-3-4-5 or similar unless SMALL_STRAIGHT or LARGE_STRAIGHT are not in your available categories
               - Keep high-value dice (5s, 6s) if they help with available upper section or sum-based categories
               - Rerolling ALL dice is appropriate when your current dice don't align with any available categories
            
            2. Early Game Strategy:
               - Prioritize attempts at high-value categories IF THEY ARE AVAILABLE: YAHTZEE (50pts), LARGE_STRAIGHT (40pts), SMALL_STRAIGHT (30pts)
               - Keep pairs, three-of-a-kinds as they could develop into valuable combinations for available categories
               - Don't sacrifice good combinations for upper section unless you already have multiple high scores
            
            3. Upper Section Strategy:
               - Aim for at least 3 dice of each number to reach the 35-point bonus (63+ points needed)
               - Higher numbers (4,5,6) are more valuable in the upper section if those categories are still available
            
            4. When to Keep vs. Reroll:
               - Always keep 4-of-a-kind, attempt YAHTZEE (but only if YAHTZEE is still available)
               - Keep 3-of-a-kind if THREE_OF_A_KIND, FOUR_OF_A_KIND, FULL_HOUSE, or YAHTZEE are available
               - Keep sequences (1-2-3-4 or 2-3-4-5) ONLY if SMALL_STRAIGHT or LARGE_STRAIGHT are available
               - For Full House, keep the 3-of-a-kind part if you need to reroll (only if FULL_HOUSE is available)
            
            5. Avoid wasting CHANCE early - save it as a safety net for otherwise poor rolls late game
            
            Which dice indices should you keep (0-indexed) to maximize expected value?
            
            Format your answer with detailed reasoning first, then a clear conclusion, followed by your final selection between triple exclamation marks:
            
            *REASONING*
            [Your detailed dice analysis here - ONLY consider the available categories listed above]
            
            *CONCLUSION*
            [Your summarized strategy here - ONLY aim for available categories]
            
            Result: !!![indices to keep]!!!
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
        prompt = f"""
            You are an expert Yahtzee player deciding which category to score with these final dice.
            
            CURRENT GAME STATE:
            - Final Dice: {dice}
            - Available Categories: {available_categories_str}
            
            CRITICAL INSTRUCTION: You MUST ONLY select from the AVAILABLE CATEGORIES listed above. These are your only options.
            
            YAHTZEE SCORING STRATEGY GUIDELINES:
            1. Category Valuation (only if available in your list):
               - YAHTZEE (50pts), LARGE_STRAIGHT (40pts), SMALL_STRAIGHT (30pts), FULL_HOUSE (25pts) are highest value
               - Upper section categories depend on dice count (e.g., five 6s = 30pts)
               - THREE_OF_A_KIND and FOUR_OF_A_KIND score the sum of all dice
               - Remember: 63+ points in the upper section earns a 35pt bonus
            
            2. Opportunity Cost Considerations:
               - Save CHANCE for poor rolls later - don't use early unless scoring 25+ points
               - If a roll scores 0 in most categories, use your weakest upper section category
               - Consider the probability of getting better combinations for remaining categories
            
            3. End Game Strategy:
               - With few categories left, calculate exact values rather than keeping options open
               - Sometimes it's better to take 0 points in a low-value category to save high-value categories
            
            4. Upper Section Management:
               - Each upper section category needs average of 3 dice to reach bonus
               - If bonus is secured or impossible, be more strategic with remaining categories
            
            Which category from the AVAILABLE CATEGORIES maximizes your expected value for the rest of the game?
            
            Format your answer with detailed reasoning first, then a clear conclusion, followed by your final selection between triple exclamation marks:
            
            *REASONING*
            [Your detailed category analysis here - ONLY consider the available categories listed above]
            
            *CONCLUSION*
            [Your summarized choice here - must be one of the available categories]
            
            Result: !!!CATEGORY_NAME!!!
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
            if indices_str == "[]":
                return []
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
