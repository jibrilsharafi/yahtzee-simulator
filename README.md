# Yahtzee Simulator

## Overview
The Yahtzee Simulator is a Python project that simulates the classic dice game Yahtzee. The project is designed to allow for the implementation and testing of various strategies for playing the game, including rule-based and random strategies. The game can be played through a command-line interface, and it supports extensive simulation capabilities for strategy testing.

## Project Structure
The project is organized into several modules:

- **src/game**: Contains the core game logic, including dice management, scoring, and overall game flow.
- **src/strategies**: Implements different strategies for playing the game, allowing for both rule-based and random decision-making.
- **src/simulation**: Provides functionality to run simulations of the game using different strategies and collect results for analysis.
- **src/cli**: Implements the command-line interface for user interaction with the game.
- **tests**: Contains unit tests for both the game logic and strategy implementations to ensure correctness.

## Installation
To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd yahtzee-simulator
pip install -r requirements.txt
```

## Usage
To run the game from the command line, execute the following command:

```bash
python main.py
```

This will start the command-line interface, allowing you to play the game interactively.

## Testing
To run the tests for the game logic and strategies, use the following command:

```bash
pytest tests/
```

## Future Work
The project is designed to be extensible, allowing for the addition of new strategies and enhancements to the game logic. Future work may include:

- Implementing more advanced AI strategies.
- Adding a graphical user interface (GUI) for a more interactive experience.
- Enhancing the simulation capabilities to analyze strategy performance in greater detail.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss potential improvements or features.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.