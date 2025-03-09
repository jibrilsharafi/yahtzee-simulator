# Yahtzee Simulator

## Overview

A Python implementation of the classic Yahtzee dice game with strategy testing capabilities. The project allows for simulation and analysis of different game strategies through both CLI gameplay and automated testing.

## Project Structure

- `src/game`: Core game logic (dice, scorecard, game flow)
- `src/strategies`: Strategy implementations (random, rule-based)
- `src/simulation`: Game simulation framework
- `src/cli`: Command-line interface
- `analysis`: Jupyter notebooks for strategy analysis
- `tests`: Unit and integration tests

## Installation

`git clone <https://github.com/jibrilsharafi/yahtzee-simulator>`

`cd yahtzee-simulator`

`pip install -r requirements.txt`

## Usage

- Command-line gameplay:
    `python main.py`

- Run strategy simulations:

    ```python
    from src.simulation.simulator import Simulator
    from src.strategies.random_strategy import RandomStrategy
    from src.strategies.rule_based_strategy import RuleBasedStrategy
    
    # Create simulator with strategies
    simulator = Simulator()
    results = simulator.run_game_simulation(1000, {
        "Random": RandomStrategy(),
        "RuleBased": RuleBasedStrategy()
    })
    ```

- For detailed analysis, use the Jupyter notebook:
    `jupyter notebook analysis/yahtzee_analysis.ipynb`

## Next Steps

- **Enhanced Visualization**: Expanding the analysis notebook with more Plotly visualizations
- **Data Management**: Standardizing result storage and analysis formats
- **Strategy Development**: Implementing more sophisticated AI strategies
- **Performance**: Optimizing parallel simulation capabilities

## License

MIT License
