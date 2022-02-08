"""
The only usage of this file is to make it possible to run
a game via a terminal command
"""


import sys

from bot import SimpleBot
from game_client import GameSession, WrongPayloadFormatException, game_loop

HELP_TEXT = (
    "Usage:\n"
    "python terminal_interface.py {name}\n"
    "python terminal_interface.py {name} {game}\n"
    "python terminal_interface.py "
    "{username} {game} {num_turns} {num_players}\n"
)


def game_init(**login_info):
    try:
        return GameSession(**login_info)
    except WrongPayloadFormatException:
        print(HELP_TEXT)
        sys.exit(1)


def main():
    if len(sys.argv) == 2:
        game = game_init(name=sys.argv[1])

    elif len(sys.argv) == 3:
        game = game_init(name=sys.argv[1], game=sys.argv[2])

    elif len(sys.argv) == 5:
        game = game_init(
            name=sys.argv[1],
            game=sys.argv[2],
            num_turns=sys.argv[3],
            num_players=sys.argv[4],
        )

    else:
        print(HELP_TEXT)
        sys.exit(1)

    game_loop(SimpleBot(game.map), game)


if __name__ == "__main__":
    main()
