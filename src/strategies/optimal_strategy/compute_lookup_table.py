from typing import (
    Dict,
    List,
    Tuple,
    Set,
    Optional,
    FrozenSet,
    TypeVar,
    Generic,
    Iterator,
)
from dataclasses import dataclass
from functools import lru_cache
from collections import Counter
import numpy as np
import itertools

# Type aliases for clarity
DiceConfiguration = Tuple[int, ...]  # Ordered dice values (1-6)
DiceState = FrozenSet[Tuple[int, int]]  # Set of (value, count) pairs
Category = str
KeepPattern = Tuple[bool, bool, bool, bool, bool]  # Which dice to keep
TurnNumber = int
GameState = Tuple[
    DiceState, FrozenSet[Category], int
]  # (dice, available_categories, rolls_remaining)


class YahtzeeScorer:
    @staticmethod
    def score_upper_section(dice: DiceConfiguration, value: int) -> int:
        """Score for upper section (sum of specific values)."""
        return sum(d for d in dice if d == value)

    @staticmethod
    def score_three_of_a_kind(dice: DiceConfiguration) -> int:
        """Score for three of a kind (sum of all dice if valid)."""
        counter = Counter(dice)
        if any(count >= 3 for count in counter.values()):
            return sum(dice)
        return 0

    @staticmethod
    def score_four_of_a_kind(dice: DiceConfiguration) -> int:
        """Score for four of a kind (sum of all dice if valid)."""
        counter = Counter(dice)
        if any(count >= 4 for count in counter.values()):
            return sum(dice)
        return 0

    @staticmethod
    def score_full_house(dice: DiceConfiguration) -> int:
        """Score for full house (25 if valid)."""
        counter = Counter(dice)
        if sorted(counter.values()) == [2, 3]:
            return 25
        return 0

    @staticmethod
    def score_small_straight(dice: DiceConfiguration) -> int:
        """Score for small straight (30 if valid)."""
        unique_sorted = sorted(set(dice))
        if len(unique_sorted) >= 4 and (
            unique_sorted[:4] == [1, 2, 3, 4]
            or unique_sorted[:4] == [2, 3, 4, 5]
            or unique_sorted[-4:] == [3, 4, 5, 6]
        ):
            return 30
        return 0

    @staticmethod
    def score_large_straight(dice: DiceConfiguration) -> int:
        """Score for large straight (40 if valid)."""
        if sorted(set(dice)) in ([1, 2, 3, 4, 5], [2, 3, 4, 5, 6]):
            return 40
        return 0

    @staticmethod
    def score_yahtzee(dice: DiceConfiguration) -> int:
        """Score for yahtzee (50 if all five dice are the same)."""
        if len(set(dice)) == 1:
            return 50
        return 0

    @staticmethod
    def score_chance(dice: DiceConfiguration) -> int:
        """Score for chance (sum of all dice)."""
        return sum(dice)

    @classmethod
    def score_category(cls, dice: DiceConfiguration, category: Category) -> int:
        """Score the given dice configuration for the specified category."""
        if category.startswith("ones"):
            return cls.score_upper_section(dice, 1)
        elif category.startswith("twos"):
            return cls.score_upper_section(dice, 2)
        elif category.startswith("threes"):
            return cls.score_upper_section(dice, 3)
        elif category.startswith("fours"):
            return cls.score_upper_section(dice, 4)
        elif category.startswith("fives"):
            return cls.score_upper_section(dice, 5)
        elif category.startswith("sixes"):
            return cls.score_upper_section(dice, 6)
        elif category.startswith("three_of_a_kind"):
            return cls.score_three_of_a_kind(dice)
        elif category.startswith("four_of_a_kind"):
            return cls.score_four_of_a_kind(dice)
        elif category.startswith("full_house"):
            return cls.score_full_house(dice)
        elif category.startswith("small_straight"):
            return cls.score_small_straight(dice)
        elif category.startswith("large_straight"):
            return cls.score_large_straight(dice)
        elif category.startswith("yahtzee"):
            return cls.score_yahtzee(dice)
        elif category.startswith("chance"):
            return cls.score_chance(dice)
        else:
            raise ValueError(f"Unknown category: {category}")


class YahtzeeSolver:
    def __init__(self) -> None:
        """Initialize the Yahtzee solver."""
        self.all_categories: FrozenSet[Category] = frozenset(
            [
                "ones",
                "twos",
                "threes",
                "fours",
                "fives",
                "sixes",
                "three_of_a_kind",
                "four_of_a_kind",
                "full_house",
                "small_straight",
                "large_straight",
                "yahtzee",
                "chance",
            ]
        )

        # Precompute all possible dice states (optimization)
        self.all_dice_states: List[DiceState] = self._generate_all_dice_states()

        # Lookup table for expected values
        self.expected_values: Dict[GameState, float] = {}
        self.best_actions: Dict[GameState, Tuple[KeepPattern, Category]] = {}

        # Precompute all possible 32 keep patterns (2^5)
        self.all_keep_patterns = list(itertools.product([True, False], repeat=5))

        # Precompute transition probabilities
        self.transition_probs: Dict[
            Tuple[DiceState, KeepPattern], Dict[DiceState, float]
        ] = {}
        self._precompute_transitions()

    def result_to_json(self) -> List[Dict[str, object]]:
        """Convert the expected values to a JSON-compatible format."""
        json_result: List[Dict[str, object]] = []

        for key, value in self.expected_values.items():
            dice_state, remaining_categories, rolls_remaining = key
            dice_state_list = sorted(list(dice_state), key=lambda x: x[0])
            json_result.append(
                # Optimize with only list. But the dice should be in format [1, 2, 3, 4, 5]
                [
                    [value for value, count in dice_state_list],
                    list(remaining_categories),
                    rolls_remaining,
                    value,
                ]
            )

        return json_result

    def _generate_all_dice_states(self) -> List[DiceState]:
        """Generate all possible unique dice states (not considering order)."""
        states = []
        # Consider all possible combinations of dice
        for c in itertools.combinations_with_replacement(range(1, 7), 5):
            # Convert to a canonical representation as a frozenset of (value, count) pairs
            counter = Counter(c)
            state = frozenset((value, count) for value, count in counter.items())
            if state not in states:
                states.append(state)
        return states

    def _dice_state_to_configurations(
        self, state: DiceState
    ) -> List[DiceConfiguration]:
        """Convert a dice state to all possible ordered configurations."""
        # Reconstruct the multiset from the state
        multiset = []
        for value, count in state:
            multiset.extend([value] * count)

        # Generate all permutations
        return list(set(itertools.permutations(multiset)))

    def _precompute_transitions(self) -> None:
        """Precompute transition probabilities for all (state, keep_pattern) combinations."""
        for state in self.all_dice_states:
            for keep_pattern in self.all_keep_patterns:
                # Get a sample configuration to apply the keep pattern
                config = next(iter(self._dice_state_to_configurations(state)))

                # Apply keep pattern to determine which dice to reroll
                kept_dice = []
                reroll_count = 0

                # If keep_pattern is shorter than config, assume False for remaining positions
                for i, die in enumerate(config):
                    if i < len(keep_pattern) and keep_pattern[i]:
                        kept_dice.append(die)
                    else:
                        reroll_count += 1

                # Calculate probabilities for all possible outcomes after rerolling
                next_states_prob: Dict[DiceState, float] = {}

                # If keeping all dice or no rerolls, the state doesn't change
                if reroll_count == 0:
                    next_states_prob[state] = 1.0
                    self.transition_probs[(state, keep_pattern)] = next_states_prob
                    continue

                # Otherwise, calculate probabilities for all possible reroll outcomes
                total_outcomes = 6**reroll_count

                # Consider all possible outcomes for rerolled dice
                for reroll in itertools.product(range(1, 7), repeat=reroll_count):
                    # Combine kept dice with rerolled dice
                    new_dice = kept_dice + list(reroll)
                    # Convert to canonical state representation
                    counter = Counter(new_dice)
                    new_state = frozenset(
                        (value, count) for value, count in counter.items()
                    )

                    # Update probability for this state
                    next_states_prob[new_state] = next_states_prob.get(new_state, 0) + (
                        1 / total_outcomes
                    )

                self.transition_probs[(state, keep_pattern)] = next_states_prob

    def compute_lookup_table(self) -> None:
        """Compute the complete lookup table for Yahtzee optimal play."""
        print("Computing lookup table...")

        # Start with empty table
        self.expected_values = {}
        self.best_actions = {}

        # Compute expected values for all game states
        total_states = len(self.all_dice_states) * 2 ** len(self.all_categories) * 3
        processed = 0

        # Process states with 0 rolls remaining first (base cases)
        for dice_state in self.all_dice_states:
            for remaining_categories in self._generate_category_subsets():
                self._compute_expected_value(dice_state, remaining_categories, 0)
                processed += 1
                if processed % 10000 == 0:
                    print(
                        f"Processed {processed}/{total_states} states ({processed/total_states*100:.2f}%)"
                    )

        # Then process states with 1 roll remaining
        for dice_state in self.all_dice_states:
            for remaining_categories in self._generate_category_subsets():
                self._compute_expected_value(dice_state, remaining_categories, 1)
                processed += 1
                if processed % 10000 == 0:
                    print(
                        f"Processed {processed}/{total_states} states ({processed/total_states*100:.2f}%)"
                    )

        # Finally process states with 2 rolls remaining
        for dice_state in self.all_dice_states:
            for remaining_categories in self._generate_category_subsets():
                self._compute_expected_value(dice_state, remaining_categories, 2)
                processed += 1
                if processed % 10000 == 0:
                    print(
                        f"Processed {processed}/{total_states} states ({processed/total_states*100:.2f}%)"
                    )

        print(f"Lookup table computed with {len(self.expected_values)} unique states.")

    def _generate_category_subsets(self) -> Iterator[FrozenSet[Category]]:
        """Generate all possible subsets of categories."""
        # For testing with small tables, we can limit to fewer categories
        # For full solution, use:
        for r in range(len(self.all_categories) + 1):
            for subset in itertools.combinations(self.all_categories, r):
                yield frozenset(subset)

    def _compute_expected_value(
        self,
        dice_state: DiceState,
        remaining_categories: FrozenSet[Category],
        rolls_remaining: int,
    ) -> float:
        """
        Compute the expected value for a given game state using dynamic programming.

        Args:
            dice_state: Current dice configuration
            remaining_categories: Set of categories still available to use
            rolls_remaining: Number of rolls remaining in the current turn

        Returns:
            Expected value for optimal play from this state
        """
        # Check if we've already computed this state
        state = (dice_state, remaining_categories, rolls_remaining)
        if state in self.expected_values:
            return self.expected_values[state]

        # Base case: No rolls remaining, must choose a category
        if rolls_remaining == 0:
            if not remaining_categories:  # No categories left
                return 0

            # Get all possible dice configurations for this state
            configs = self._dice_state_to_configurations(dice_state)

            # Find best category to use
            best_score = float("-inf")
            best_category = None

            for category in remaining_categories:
                # Average score across all equivalent dice configurations
                avg_score = sum(
                    YahtzeeScorer.score_category(config, category) for config in configs
                ) / len(configs)

                if avg_score > best_score:
                    best_score = avg_score
                    best_category = category

            # For the final roll, the keep pattern doesn't matter
            self.best_actions[state] = (None, best_category)
            self.expected_values[state] = best_score
            return best_score

        # Case: Has rolls remaining, can reroll some dice or stop
        # First, check if it's optimal to just stop and score now
        stop_value = self._compute_expected_value(dice_state, remaining_categories, 0)

        # Try all possible keep patterns to find best expected value
        best_value = stop_value
        best_keep = None

        for keep_pattern in self.all_keep_patterns:
            # Skip keep patterns that don't match the state length
            # Get expected value for this keep pattern
            ev = 0

            # Consider all possible next states and their probabilities
            transition_key = (dice_state, keep_pattern)
            if transition_key in self.transition_probs:
                for next_state, prob in self.transition_probs[transition_key].items():
                    # Recursive call to get expected value of next state
                    next_ev = self._compute_expected_value(
                        next_state, remaining_categories, rolls_remaining - 1
                    )
                    ev += prob * next_ev

            if ev > best_value:
                best_value = ev
                best_keep = keep_pattern

        # Store the best action and expected value
        best_category = (
            None
            if rolls_remaining > 0
            else self.best_actions[(dice_state, remaining_categories, 0)][1]
        )
        self.best_actions[state] = (best_keep, best_category)
        self.expected_values[state] = best_value

        return best_value

    def suggest_move(
        self,
        dice: DiceConfiguration,
        available_categories: Set[Category],
        rolls_remaining: int,
    ) -> Tuple[List[int], Optional[Category]]:
        """
        Suggest the optimal move for the current game state.

        Args:
            dice: Current dice values
            available_categories: Categories still available
            rolls_remaining: Number of rolls remaining

        Returns:
            Tuple of (indices of dice to keep, category to use or None)
        """
        # Convert inputs to internal representation
        counter = Counter(dice)
        dice_state = frozenset((value, count) for value, count in counter.items())
        remaining_categories = frozenset(available_categories)

        # Look up the best action
        state = (dice_state, remaining_categories, rolls_remaining)

        if state not in self.best_actions:
            # If state not in table, compute it on the fly
            self._compute_expected_value(
                dice_state, remaining_categories, rolls_remaining
            )

        keep_pattern, category = self.best_actions[state]

        # Convert keep_pattern to list of indices to keep
        dice_to_keep = []
        if keep_pattern is not None:
            for i, keep in enumerate(keep_pattern):
                if i < len(dice) and keep:
                    dice_to_keep.append(i)

        return dice_to_keep, category

    def get_expected_score(
        self,
        dice: DiceConfiguration,
        available_categories: Set[Category],
        rolls_remaining: int,
    ) -> float:
        """
        Get the expected score for the current game state.

        Args:
            dice: Current dice values
            available_categories: Categories still available
            rolls_remaining: Number of rolls remaining

        Returns:
            Expected score for optimal play from this state
        """
        # Convert inputs to internal representation
        counter = Counter(dice)
        dice_state = frozenset((value, count) for value, count in counter.items())
        remaining_categories = frozenset(available_categories)

        # Look up the expected value
        state = (dice_state, remaining_categories, rolls_remaining)

        if state not in self.expected_values:
            # If state not in table, compute it on the fly
            return self._compute_expected_value(
                dice_state, remaining_categories, rolls_remaining
            )

        return self.expected_values[state]


class YahtzeeGame:
    """A playable Yahtzee game that uses the solver for suggestions."""

    def __init__(self, use_solver: bool = True) -> None:
        """Initialize a new Yahtzee game."""
        self.scorecard: Dict[Category, Optional[int]] = {
            "ones": None,
            "twos": None,
            "threes": None,
            "fours": None,
            "fives": None,
            "sixes": None,
            "three_of_a_kind": None,
            "four_of_a_kind": None,
            "full_house": None,
            "small_straight": None,
            "large_straight": None,
            "yahtzee": None,
            "chance": None,
        }
        self.dice: List[int] = [0, 0, 0, 0, 0]
        self.rolls_remaining: int = 3
        self.turn: int = 1
        self.solver = YahtzeeSolver() if use_solver else None

        # If using solver, precompute lookup table
        if use_solver:
            self.solver.compute_lookup_table()

    def roll_dice(self, indices_to_roll: Optional[List[int]] = None) -> None:
        """
        Roll the dice at the specified indices.

        Args:
            indices_to_roll: Indices of dice to roll (None for all)
        """
        if self.rolls_remaining <= 0:
            print("No rolls remaining this turn.")
            return

        if indices_to_roll is None:
            indices_to_roll = list(range(5))

        for i in indices_to_roll:
            if 0 <= i < 5:
                self.dice[i] = np.random.randint(1, 7)

        self.rolls_remaining -= 1
        print(f"Dice: {self.dice}")

    def get_available_categories(self) -> Set[Category]:
        """Get the set of categories that haven't been used yet."""
        return {cat for cat, score in self.scorecard.items() if score is None}

    def score_category(self, category: Category) -> None:
        """
        Score the current dice in the specified category.

        Args:
            category: Category to score
        """
        if category not in self.scorecard or self.scorecard[category] is not None:
            print(f"Category {category} already used or invalid.")
            return

        score = YahtzeeScorer.score_category(tuple(self.dice), category)
        self.scorecard[category] = score
        print(f"Scored {score} in {category}")

        # Reset for next turn
        self.rolls_remaining = 3
        self.dice = [0, 0, 0, 0, 0]
        self.turn += 1

    def get_suggestion(self) -> Tuple[List[int], Optional[Category]]:
        """Get a suggestion for the optimal move."""
        if not self.solver:
            return [], None

        available_categories = self.get_available_categories()
        return self.solver.suggest_move(
            tuple(self.dice), available_categories, self.rolls_remaining
        )

    def get_expected_score(self) -> float:
        """Get the expected score for the current game state."""
        if not self.solver:
            return 0.0

        available_categories = self.get_available_categories()
        return self.solver.get_expected_score(
            tuple(self.dice), available_categories, self.rolls_remaining
        )

    def display_scorecard(self) -> None:
        """Display the current scorecard."""
        print("\n----- SCORECARD -----")

        upper_section = ["ones", "twos", "threes", "fours", "fives", "sixes"]
        upper_total = sum(self.scorecard[cat] or 0 for cat in upper_section)
        bonus = 35 if upper_total >= 63 else 0

        print("Upper Section:")
        for cat in upper_section:
            print(
                f"{cat.capitalize()}: {self.scorecard[cat] if self.scorecard[cat] is not None else '-'}"
            )
        print(f"Bonus: {bonus} (Upper total: {upper_total}/63)")

        print("\nLower Section:")
        lower_section = [
            "three_of_a_kind",
            "four_of_a_kind",
            "full_house",
            "small_straight",
            "large_straight",
            "yahtzee",
            "chance",
        ]
        for cat in lower_section:
            print(
                f"{cat.replace('_', ' ').capitalize()}: {self.scorecard[cat] if self.scorecard[cat] is not None else '-'}"
            )

        lower_total = sum(self.scorecard[cat] or 0 for cat in lower_section)
        grand_total = upper_total + bonus + lower_total

        print(f"\nUpper Section: {upper_total} + {bonus} (bonus)")
        print(f"Lower Section: {lower_total}")
        print(f"GRAND TOTAL: {grand_total}")
        print("--------------------\n")


# Example usage
def main() -> None:
    """Main function demonstrating solver capability."""
    print("Initializing Yahtzee solver...")

    # Create a reduced version for testing (faster)
    reduced_solver = YahtzeeSolver()

    # Compute a small lookup table for demonstration purposes
    reduced_solver.compute_lookup_table()

    # Save as pickle
    with open("yahtzee_solver.pkl", "wb") as f:
        import pickle

        pickle.dump(reduced_solver, f)

    # Export the results as JSON
    with open("yahtzee_solver.json", "w") as f:
        import json

        json.dump(reduced_solver.result_to_json(), f, indent=None)

    # Example: Get expected score for initial roll
    dice = (1, 2, 3, 4, 5)
    categories = {
        "ones",
        "twos",
        "threes",
        "fours",
        "fives",
        "sixes",
        "three_of_a_kind",
        "four_of_a_kind",
        "full_house",
        "small_straight",
        "large_straight",
        "yahtzee",
        "chance",
    }

    expected_score = reduced_solver.get_expected_score(dice, categories, 2)
    dice_to_keep, category = reduced_solver.suggest_move(dice, categories, 2)

    print(f"For dice {dice} with all categories available and 2 rolls remaining:")
    print(f"Expected score: {expected_score:.2f}")
    print(
        f"Suggested move: Keep dice at indices {dice_to_keep}"
        + (f" and use category {category}" if category else "")
    )

    # Play an interactive game
    print("\nStarting a new Yahtzee game with solver suggestions...")
    game = YahtzeeGame(use_solver=True)

    # Example of one turn
    game.roll_dice()  # First roll
    suggestion, _ = game.get_suggestion()
    print(f"Suggestion: Keep dice at indices {suggestion}")

    # Let solver play automatically
    print("\nHaving the solver play a full game automatically...")
    auto_game = YahtzeeGame(use_solver=True)

    while auto_game.get_available_categories():
        print(f"\n--- Turn {auto_game.turn} ---")
        auto_game.roll_dice()  # First roll

        # Make up to 2 more rolls following solver suggestions
        for _ in range(2):
            if auto_game.rolls_remaining > 0:
                indices_to_keep, _ = auto_game.get_suggestion()
                indices_to_roll = [i for i in range(5) if i not in indices_to_keep]
                print(f"Keeping dice at indices {indices_to_keep}")
                if indices_to_roll:
                    auto_game.roll_dice(indices_to_roll)

        # Score according to solver suggestion
        _, category = auto_game.get_suggestion()
        auto_game.score_category(category)

    # Display final score
    auto_game.display_scorecard()


if __name__ == "__main__":
    main()
