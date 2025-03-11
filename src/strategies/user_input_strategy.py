from typing import List, Set

from src.game.scorecard import Scorecard, ScorecardCategory


class UserInputStrategy:
    def select_dice_to_keep(
        self, current_dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> Set[int]:
        """
        Asks the user which dice to keep based on the current state of the game.

        Args:
            current_dice: List of current dice values.
            scorecard: Current scorecard of the player.
            debug: If True, show detailed information.

        Returns:
            Set of indices of dice to keep.
        """
        # If this is the last roll, keep all dice
        if scorecard.current_roll >= 3:
            return set([i for i in range(len(current_dice))])

        # Show current state
        print("\n==== YOUR TURN ====")
        print(f"Roll #{scorecard.current_roll}/3")

        # Display the scorecard if debug is active
        if debug:
            self._display_scorecard(scorecard)

        # Display the dice with their indices
        print("\nCurrent dice:")
        for i, die in enumerate(current_dice):
            print(f"Die #{i}: {die}")

        # Get user input
        while True:
            try:
                input_str = input(
                    "\nEnter indices of dice to keep (e.g., '0 2 4' or 'all' or none): "
                )

                # Handle special cases
                if input_str.lower() == "all":
                    return set(range(len(current_dice)))
                elif not input_str.strip():
                    return set()

                # Parse indices
                indices = {int(idx) for idx in input_str.split() if idx.isdigit()}

                # Validate indices
                if any(idx < 0 or idx >= len(current_dice) for idx in indices):
                    print(
                        f"Invalid index! Please use numbers between 0 and {len(current_dice)-1}"
                    )
                    continue

                # Display confirmation
                kept_dice = [current_dice[i] for i in indices]
                print(f"Keeping dice: {kept_dice}")
                return indices

            except ValueError:
                print("Invalid input! Please enter space-separated numbers.")

    def select_category(
        self, dice: List[int], scorecard: Scorecard, debug: bool = False
    ) -> ScorecardCategory:
        """
        Asks the user which category to score in.

        Args:
            dice: Current dice values.
            scorecard: Current scorecard of the player.
            debug: If True, show detailed information.

        Returns:
            Category to score in.
        """
        # Get available categories
        available_categories = [
            cat for cat in list(ScorecardCategory) if scorecard.get_score(cat) is None
        ]

        if not available_categories:
            raise ValueError("No available categories to select")

        # Show current state
        print("\n==== CHOOSE CATEGORY ====")
        print(f"Current dice: {dice}")

        # Display the scorecard if debug is active
        if debug:
            self._display_scorecard(scorecard)

        # Display available categories with potential scores
        print("\nAvailable categories:")
        for i, category in enumerate(available_categories):
            score = scorecard.calculate_score(category, dice)
            print(f"{i+1}. {category.name}: {score} points")

        # Get user input
        while True:
            try:
                choice = input("\nEnter category number: ")
                idx = int(choice) - 1

                if idx < 0 or idx >= len(available_categories):
                    print(
                        f"Invalid choice! Please enter a number between 1 and {len(available_categories)}"
                    )
                    continue

                selected_category = available_categories[idx]
                score = scorecard.calculate_score(selected_category, dice)
                print(f"Selected {selected_category.name} for {score} points")
                return selected_category

            except ValueError:
                print("Invalid input! Please enter a number.")

    def _display_scorecard(self, scorecard: Scorecard) -> None:
        """Displays the current scorecard state."""
        print("\n----- SCORECARD -----")

        # Upper section
        print("Upper Section:")
        upper_categories = [
            ScorecardCategory.ONES,
            ScorecardCategory.TWOS,
            ScorecardCategory.THREES,
            ScorecardCategory.FOURS,
            ScorecardCategory.FIVES,
            ScorecardCategory.SIXES,
        ]

        for cat in upper_categories:
            score = scorecard.get_score(cat)
            status = f"{score}" if score is not None else "open"
            print(f"  {cat.name}: {status}")

        # Show upper section bonus
        upper_total = sum(scorecard.get_score(cat) or 0 for cat in upper_categories)
        bonus = 35 if upper_total >= 63 else 0
        print(f"  Upper total: {upper_total}/63 (Bonus: {bonus})")

        # Lower section
        print("Lower Section:")
        lower_categories = [
            ScorecardCategory.THREE_OF_A_KIND,
            ScorecardCategory.FOUR_OF_A_KIND,
            ScorecardCategory.FULL_HOUSE,
            ScorecardCategory.SMALL_STRAIGHT,
            ScorecardCategory.LARGE_STRAIGHT,
            ScorecardCategory.YAHTZEE,
            ScorecardCategory.CHANCE,
        ]

        for cat in lower_categories:
            score = scorecard.get_score(cat)
            status = f"{score}" if score is not None else "open"
            print(f"  {cat.name}: {status}")

        # Show total score
        lower_total = sum(scorecard.get_score(cat) or 0 for cat in lower_categories)
        total = upper_total + bonus + lower_total
        print(f"  Total score: {total}")
        print("-------------------")
