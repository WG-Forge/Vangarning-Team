# World of Tanks: Strategy
## Vangarning-Team

### Team
 - [Anna Konkolovich](https://github.com/anyakonkolovich)
 - [Vladislav Yakshuk](https://github.com/liquidgoo)
 - [Vasilii Safronov](https://github.com/VaSeWS)

### How to launch
Python version: 3.9

 - Install dependencies: `pip install  -r  requirements.txt` 

Use one of the following:
 - To create game without name for one player: `python
   terminal_interface.py {name}`
 - To connect to existing game/create game for one player: `python
   terminal_interface.py {name} {game}`
 - To create game: `python terminal_interface.py {username} {game}
   {num_turns} {num_players}`
 - To start game with 3 simple bots and gui: `python run_game.py`
 
If you want to see GUI add `--gui` (terminal_interface.py only, run_game.py runs with gui by default)
[![gui-screenshot-png.png](https://i.postimg.cc/j5jrGfLk/gui-screenshot-png.png)](https://postimg.cc/jWB9fL6z)
### Project structure
- #### `bot` module
    - `mcst` module - Bot based on Monte-Carlo Search Tre. WIP.
        - `mcst.py` - Monte-Carlo Search Tree
        - `mcst_bot.py` - Monte-Carlo Tree Search bot
        - `mcts_bot_game_state` Game state class for Monte-Carlo Tree Search Bot
    
    - `step_score_bot.py` - Bot that uses formula and predetermined weights to find the best possible steps.
    - `action_estimator.py` - Estimates quality of the given action using predetermined weights.
    - `action_generator.py` - Generates every possible action for given Vehicle and Game state.
    - `bot.py` - Base `Bot` class.
    - `bot_game_state.py` - Game state class describing game state in needed for bot way.
    
- #### `game_client` module - Low-level classes describing game logic.
    - `actions.py` - `Action` class representing action for single vehicle.
    - `game_loop.py` - `game_loop` function implementing main game loop.
    - `game_state.py` - Base `GameState` class describing game state.
    - `map.py` - `GameMap` class describing game map.
    - `map_hexes.py` - Classes to describe different hex types.
    - `player.py` - Class describing player.
    - `server_interaction.py` - Classes for interaction with server.
    - `state_hex.py` - Class to describe hex of a game state.
    - `vehicles.py` - Classes to describe vehicles.
    
- #### `gui` module - Graphic user interface made using [kivy](https://kivy.org/#home).
    - `assets` - Directory contains 2D and .kv assets.
    - `game_state_property.py` - Class with game state property. Used to update gui when game state is changed.
    - `gui.py` - Classes for graphic user interface.
    
- #### `tests` module - Unit tests. WIP.
    - `test_coords.py` - Tests for class `Coords` in `utility.coordinates.py`.

- #### `utility` module - Files with utility classes.
    - `coordinates.py` - Contains class for map coordinates.
    - `custom_typing.py` - Project-specific typings.
    - `singleton.py` - Contains singleton meta class.

- `estimator_coefficients_optimisation.py` - Functions to optimize `action_estimator.py` coefficients. WIP.
- `terminal_interface.py` and `run_game.py` - *you can launch game from them!*
