import threading
from time import perf_counter

from game_client.server_interaction import GameSession, ActionCode
from bot.step_score_bot import StepScoreBot
from gui.gui import WoTStrategyApp
from gui.game_state_property import game_state_property


def game_loop(bot, game):
    movements = 0
    shots = 0
    while True:
        game_state = game.game_state()
        game_state_property.game_state = game_state
        if game_state["finished"]:
            print("You won" if game_state["winner"] == game.player_id else "You lost")
            print(f"Shots to movements ratio: {shots/movements}")
            print(f"Winner: {game_state['winner']}")
            break

        if game_state["current_player_idx"] == game.player_id:
            print(f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}")
            for action in bot.get_actions(game_state):
                if action.action_code == ActionCode.SHOOT:
                    shots += 1
                else:
                    movements += 1
                game.action(*action.server_format)
                print(
                    f"  Action: "
                    f'{"shoot" if action.action_code == ActionCode.SHOOT else "move"}'
                    f" Actor: {action.actor} Target: {action.target}"
                )

        game.turn()


if __name__ == "__main__":
    game_name = "VT_test3"

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

    simple_bot = StepScoreBot(game_session.map)

    tr1 = threading.Thread(target=game_loop, args=(simple_bot, game_session))
    tr2 = threading.Thread(target=game_loop, args=(simple_bot, game_session_1))
    tr3 = threading.Thread(target=game_loop, args=(simple_bot, game_session_2))

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

#
# if __name__ == "__main__":
#     game_session = GameSession(name="Bot_test_1")
#     gbot = StepScoreBot(game_session.map)
#     game_loop(gbot, game_session)

