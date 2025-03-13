import sys

sys.path.append(".")  # Adjust the path to import from the current directory

import logging

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from src.game.scorecard import Scorecard, ScorecardCategory

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_optimal_training_data(num_games=100):
    logger.debug(f"Starting to generate {num_games} games of training data")
    all_games_data = []

    for game_num in range(num_games):
        logger.debug(f"Generating game {game_num+1}/{num_games}")

        # 1. First, simulate and record all rolls
        all_rolls = []
        logger.debug(f"Game {game_num+1}: Simulating all rolls for 13 turns")
        for turn in range(13):  # 13 turns in a game
            logger.debug(f"Game {game_num+1}, Turn {turn+1}: Simulating rolls")
            roll_data = {"turn_rolls": []}

            # First roll
            dice = np.random.randint(1, 7, size=5).tolist()
            roll_data["turn_rolls"].append(dice.copy())
            logger.debug(f"Game {game_num+1}, Turn {turn+1}, Roll 1: {dice}")

            # Second roll (randomly keep some dice)
            keep_indices = set(
                np.random.choice(range(5), size=np.random.randint(0, 6), replace=False)
            )
            logger.debug(
                f"Game {game_num+1}, Turn {turn+1}, Roll 1->2 keeping indices: {keep_indices}"
            )
            reroll_dice = [
                dice[i] if i in keep_indices else np.random.randint(1, 7)
                for i in range(5)
            ]
            roll_data["turn_rolls"].append(reroll_dice.copy())
            logger.debug(f"Game {game_num+1}, Turn {turn+1}, Roll 2: {reroll_dice}")

            # Third roll (randomly keep some dice)
            keep_indices = set(
                np.random.choice(range(5), size=np.random.randint(0, 6), replace=False)
            )
            logger.debug(
                f"Game {game_num+1}, Turn {turn+1}, Roll 2->3 keeping indices: {keep_indices}"
            )
            final_dice = [
                reroll_dice[i] if i in keep_indices else np.random.randint(1, 7)
                for i in range(5)
            ]
            roll_data["turn_rolls"].append(final_dice.copy())
            logger.debug(
                f"Game {game_num+1}, Turn {turn+1}, Roll 3 (final): {final_dice}"
            )

            # Store the final dice for this turn
            roll_data["final_dice"] = final_dice
            all_rolls.append(roll_data)

        # 2. Find optimal category arrangement using dynamic programming
        logger.debug(f"Game {game_num+1}: Finding optimal category assignments")

        # Calculate scores for each dice-category combination
        score_matrix = {}
        available_categories = list(ScorecardCategory)
        logger.debug(
            f"Game {game_num+1}: Calculating scores for all dice-category combinations"
        )

        for category in available_categories:
            for turn_idx, roll_data in enumerate(all_rolls):
                final_dice = roll_data["final_dice"]
                is_yahtzee = (
                    category == ScorecardCategory.YAHTZEE and len(set(final_dice)) == 1
                )
                score = Scorecard.calculate_score(category, final_dice, is_yahtzee)
                score_matrix[(turn_idx, category)] = score
                logger.debug(
                    f"Game {game_num+1}, Turn {turn_idx+1}, Category {category.name}: Score = {score}"
                )

        # Find optimal assignment (using Hungarian algorithm or similar in practice)
        # For simplicity, we'll use a greedy approach here
        best_score = 0
        best_assignment = None
        logger.debug(
            f"Game {game_num+1}: Finding optimal assignment using random permutations"
        )

        # In practice, we would use a more efficient algorithm like the Hungarian algorithm
        # But for small n like 13, even trying some random permutations can find good solutions
        for perm_idx in range(1000):  # Try 1000 random permutations
            perm = np.random.permutation(available_categories)
            total_score = sum(
                score_matrix[(turn_idx, cat)] for turn_idx, cat in enumerate(perm)
            )

            if total_score > best_score:
                best_score = total_score
                best_assignment = list(perm)
                logger.debug(
                    f"Game {game_num+1}, Permutation {perm_idx+1}: New best score = {best_score}"
                )

        logger.debug(f"Game {game_num+1}: Final optimal score = {best_score}")

        # 3. Generate training data based on optimal assignment
        logger.debug(
            f"Game {game_num+1}: Generating training data based on optimal assignment"
        )
        game_data = []

        for turn_idx, category in enumerate(best_assignment):
            logger.debug(
                f"Game {game_num+1}, Turn {turn_idx+1}: Assigned category = {category.name}"
            )
            roll_sequence = all_rolls[turn_idx]["turn_rolls"]

            # For roll 1 -> roll 2, what dice should be kept optimally?
            # This requires knowledge of the final category assignment
            # For simplicity, we'll use a heuristic here, but in practice we'd solve this subproblem too
            for roll_idx in range(2):  # For first and second roll
                current_dice = roll_sequence[roll_idx]
                next_dice = roll_sequence[roll_idx + 1]

                # Determine which dice were actually kept (in our simulation)
                kept_indices = {i for i in range(5) if next_dice[i] == current_dice[i]}
                logger.debug(
                    f"Game {game_num+1}, Turn {turn_idx+1}, Roll {roll_idx+1} -> {roll_idx+2}: Kept indices = {kept_indices}"
                )

                # In practice, we'd determine the optimal kept_indices given knowledge of the category

                game_data.append(
                    {
                        "dice": current_dice,
                        "roll_num": roll_idx + 1,
                        "turn": turn_idx + 1,
                        "action_type": "keep_dice",
                        "optimal_action": kept_indices,
                        "target_category": category.name,
                    }
                )
                logger.debug(
                    f"Game {game_num+1}, Turn {turn_idx+1}, Roll {roll_idx+1}: Added data entry for keeping dice"
                )

            # For the final roll, record the optimal category
            game_data.append(
                {
                    "dice": roll_sequence[2],  # Final dice roll
                    "roll_num": 3,
                    "turn": turn_idx + 1,
                    "action_type": "select_category",
                    "optimal_action": category.name,
                    "score": score_matrix[(turn_idx, category)],
                }
            )
            logger.debug(
                f"Game {game_num+1}, Turn {turn_idx+1}, Roll 3: Added data entry for category selection"
            )

        all_games_data.extend(game_data)
        logger.debug(f"Game {game_num+1}: Added {len(game_data)} data points")

    logger.debug(
        f"Generated a total of {len(all_games_data)} data points across {num_games} games"
    )
    return pd.DataFrame(all_games_data)


def find_optimal_assignment(all_rolls, available_categories):
    logger.debug("Finding optimal assignment using Hungarian algorithm")
    # Create cost matrix (negative scores since we're minimizing cost)
    cost_matrix = np.zeros((len(all_rolls), len(available_categories)))

    for turn_idx, roll_data in enumerate(all_rolls):
        final_dice = roll_data["final_dice"]
        for cat_idx, category in enumerate(available_categories):
            score = Scorecard.calculate_score(final_dice, category)
            cost_matrix[turn_idx, cat_idx] = -score
            logger.debug(f"Turn {turn_idx+1}, Category {category}: Score = {score}")

    # Apply Hungarian algorithm
    logger.debug("Applying Hungarian algorithm")
    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    # Create the optimal assignment
    optimal_assignment = [available_categories[col_idx] for col_idx in col_indices]
    optimal_score = -cost_matrix[row_indices, col_indices].sum()
    logger.debug(f"Optimal assignment found with total score: {optimal_score}")

    return optimal_assignment, optimal_score


if __name__ == "__main__":
    logger.info("Starting training data generation")
    df = generate_optimal_training_data(num_games=10)
    logger.info(f"Generated DataFrame with {len(df)} rows")
    logger.debug("Sample of generated data:\n" + str(df.head()))

    # Save to CSV
    logger.info("Saving training data to CSV")
    df.to_csv("optimal_training_data.csv", index=False)
    logger.info("Training data saved to optimal_training_data.csv")
