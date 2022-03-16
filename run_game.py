"""
Launches game with 3 bots.

"""
import threading

from bot.step_score_bot import StepScoreBot
from game_client.game_loop import game_loop
from game_client.server_interaction import GameSession
from gui.game_state_property import game_state_property
from gui.gui import WoTStrategyApp

GAME_NAME = "VT_test1"

if __name__ == "__main__":
    game_session = GameSession(name="Bot_test_1", game=GAME_NAME, num_players=3)
    game_session_1 = GameSession(
        name="Bot_test_2",
        game=GAME_NAME,
    )
    game_session_2 = GameSession(
        name="Bot_test_3",
        game=GAME_NAME,
    )

    bot_1 = StepScoreBot(game_session.map)
    bot_2 = StepScoreBot(game_session.map)
    bot_3 = StepScoreBot(game_session.map)

    tr1 = threading.Thread(target=game_loop, args=(bot_1, game_session))
    tr2 = threading.Thread(target=game_loop, args=(bot_2, game_session_1))
    tr3 = threading.Thread(target=game_loop, args=(bot_3, game_session_2))

    tr1.start()
    tr2.start()
    tr3.start()

    WoTStrategyApp(game_session.map, game_state_property).run()

    tr1.join()
    tr2.join()
    tr3.join()
