"""
The only usage of this file is to make it possible to run
a game via a terminal command
"""


import sys

from game_client import game_loop
from server_interaction import GameSession, WrongPayloadFormatError
from step_score_bot import StepScoreBot

HELP_TEXT = (
    "Usage:\n"
    "python terminal_interface.py {name}\n"
    "python terminal_interface.py {name} {game}\n"
    "python terminal_interface.py "
    "{username} {game} {num_turns} {num_players}\n"
    "--gui - launch the game with gui"
)


def game_init(**login_info):
    try:
        return GameSession(**login_info)
    except WrongPayloadFormatError:
        print(HELP_TEXT)
        sys.exit(1)


def game_launch(bot, game, gui):
    if gui:
        from gui import WoTStrategyApp
        WoTStrategyApp(game.map, game.game_state()["vehicles"], bot, game).run()
    else:
        game_loop(bot, game)


def main():
    try:
        with_gui = sys.argv[1] == "--gui"
    except IndexError:
        print(HELP_TEXT)
        sys.exit(1)

    len_modifier = 1 if with_gui else 0

    if len(sys.argv) == 2 + len_modifier:
        game = game_init(name=sys.argv[1 + len_modifier])

    elif len(sys.argv) == 3 + len_modifier:
        game = game_init(name=sys.argv[1 + len_modifier], game=sys.argv[2 + len_modifier])

    elif len(sys.argv) == 5 + len_modifier:
        game = game_init(
            name=sys.argv[1 + len_modifier],
            game=sys.argv[2 + len_modifier],
            num_turns=sys.argv[3 + len_modifier],
            num_players=sys.argv[4 + len_modifier],
        )

    else:
        print(HELP_TEXT)
        sys.exit(1)

    bot = StepScoreBot(game.map)
    game_launch(bot, game, with_gui)


if __name__ == "__main__":
    main()
