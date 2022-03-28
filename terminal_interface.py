"""
Makes it possible to run a game through terminal.

"""
import sys
import threading

from bot.step_score_bot import StepScoreBot
from game_client.game_loop import game_loop
from game_client.server_interaction import GameSession, WrongPayloadFormatError

HELP_TEXT = (
    "Usage:\n"
    "python terminal_interface.py {username}\n"
    "python terminal_interface.py {username} {game}\n"
    "python terminal_interface.py "
    "{username} {game} {num_turns} {num_players}\n"
    "--gui - launch the game with gui"
)

CMD_FLAGS = ["--gui"]


def game_init(**login_info) -> GameSession:
    """
    Returns GameSession instance if acceptable login_info was provided.

    """
    try:
        return GameSession(**login_info)
    except WrongPayloadFormatError:
        print(HELP_TEXT)
        sys.exit(1)


def game_launch(bot, game, gui) -> None:
    """
    Launches the game.

    :param bot: bot that will play the game
    :param game: game to be played
    :param gui: to use gui or not
    """
    if gui:
        game_loop_thread = threading.Thread(target=game_loop, args=(bot, game))
        game_loop_thread.start()
        # pylint: disable=import-outside-toplevel
        # Written here as it opens empty window if --gui was not provided
        # if imported at the top of the file
        from gui.game_state_property import game_state_property
        from gui.gui import WoTStrategyApp

        WoTStrategyApp(game.map, game_state_property).run()

        game_loop_thread.join()
    else:
        game_loop(bot, game)


def main() -> None:
    """
    Parses terminal args and initiates game with given params.

    """
    args = sys.argv.copy()
    flags_dict = {}
    for flag in CMD_FLAGS:
        flags_dict[flag] = flag in args
        if flags_dict[flag]:
            args.remove(flag)

    if len(args) == 2:
        game = game_init(name=args[1])

    elif len(args) == 3:
        game = game_init(name=args[1], game=args[2])

    elif len(args) == 5:
        game = game_init(
            name=args[1],
            game=args[2],
            num_turns=args[3],
            num_players=args[4],
        )

    else:
        print(HELP_TEXT)
        sys.exit(1)

    bot = StepScoreBot(game.map)
    game_launch(bot, game, flags_dict["--gui"])


if __name__ == "__main__":
    main()
