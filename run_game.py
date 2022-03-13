import threading
from time import perf_counter

from bot.step_score_bot import StepScoreBot
from game_client.game_loop import game_loop
from game_client.server_interaction import GameSession
from gui.game_state_property import game_state_property
from gui.gui import WoTStrategyApp

if __name__ == "__main__":
    game_name = "VT_test"

    game_session = GameSession(name="Bot_test_1", game=game_name, num_players=3)
    game_session_1 = GameSession(
        name="Bot_test_2",
        game=game_name,
    )
    game_session_2 = GameSession(
        name="Bot_test_3",
        game=game_name,
    )

    bot_1 = StepScoreBot(game_session.map, estimator_weights=[1, 2, 3, 4])
    bot_2 = StepScoreBot(game_session.map, estimator_weights=[2, 2, 2, 2])
    bot_3 = StepScoreBot(game_session.map, estimator_weights=[4, 3, 2, 1])

    tr1 = threading.Thread(target=game_loop, args=(bot_1, game_session))
    tr2 = threading.Thread(target=game_loop, args=(bot_2, game_session_1))
    tr3 = threading.Thread(target=game_loop, args=(bot_3, game_session_2))

    a = perf_counter()
    tr1.start()
    tr2.start()
    tr3.start()

    WoTStrategyApp(game_session.map, game_state_property).run()

    tr1.join()
    tr2.join()
    tr3.join()
    b = perf_counter()
    print(f"\nGame duration: {b - a} seconds")

# if __name__ == "__main__":
#     game_session = GameSession(name="Bot_test_1")
#     gbot = StepScoreBot(game_session.map)
#     game_loop(gbot, game_session)
