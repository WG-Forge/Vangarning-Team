# World of Tanks: Strategy
## Vangarning-Team

### Team
 - [Anna Konkolovich](https://github.com/anyakonkolovich)
 - [Vladislav Yakshuk](https://github.com/liquidgoo)
 - [Vasilii Safronov](https://github.com/VaSeWS)

### How to launch
Python version: 3.9

 - Install dependencies: `pip install  -r  requirements.txt` 
 - Change directory: `cd WoT_Strategy`

Use one of the following:
 - To create game without name for one player: `python
   terminal_interface.py {name}`
 - To connect to existing game/create game for one player: `python
   terminal_interface.py {name} {game}`
 - To create game: `python terminal_interface.py {username} {game}
   {num_turns} {num_players}`
 - To play game with 3 simple bots: `python test_game.py`
 
If you want to see GUI add `--gui` after file name (not supported by `test_game.py`)
### Project structure
- `server_interaction.py` - classes for interaction with server.
- `game_client.py` - classes and fucntions needed to play game.
- `vehicles.py` - classes to desctibe vehicles.
- `bot.py` - base `Bot` class ans simple bot. OUTDATED.
- `hex.py` - functions to deal with hexes coordinates transformations.
- `mcst.py` and `mcst_bot.py` - Monte-Carlo Search Tree and bot that uses it. WIP.
- `settings.py` - some constants which can be used in different places of the project.
- `step_score_bot.py` - bot that uses formula (pretty simple for now) to find the best possible steps. Will be used in MCST Bot.
- `terminal_interface.py` and `test_game.py` - *you can launch game from them!*
- `assets`, `gui.py`, `WoTStrategyApp.kv` - GUI made using [kivy](https://kivy.org/#home).
