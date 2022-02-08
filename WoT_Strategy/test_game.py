import threading
from time import perf_counter

from bot import SimpleBot
from game_client import GameSession, game_loop

if __name__ == "__main__":
    game_name = "VT_test"

    game_session = GameSession(
        name="Bot_test_1", game=game_name, num_turns=45, num_players=3
    )
    game_session_1 = GameSession(
        name="Bot_test_2",
        game=game_name,
    )
    game_session_2 = GameSession(
        name="Bot_test_3",
        game=game_name,
    )

    simple_bot = SimpleBot(game_session.map)

    tr1 = threading.Thread(target=game_loop, args=(simple_bot, game_session))
    tr2 = threading.Thread(target=game_loop, args=(simple_bot, game_session_1))
    tr3 = threading.Thread(target=game_loop, args=(simple_bot, game_session_2))

    a = perf_counter()
    tr1.start()
    tr2.start()
    tr3.start()
    tr1.join()
    tr2.join()
    tr3.join()
    b = perf_counter()
    print(f"\nGame duration: {b - a} seconds")
