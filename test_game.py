from game_client.server_interaction import GameSession, ActionCode
from bot.step_score_bot import StepScoreBot


def game_loop(bot, game):
    while True:
        game_state = game.game_state()
        if game_state["finished"]:
            print("You won" if game_state["winner"] == game.player_id else "You lost")
            print(f"Winner: {game_state['winner']}")
            break

        if game_state["current_player_idx"] == game.player_id:
            print(f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}")
            for action in bot.get_actions(game_state):
                game.action(*action.server_format)
                print(
                    f"  Action: "
                    f'{"shoot" if action.action_code == ActionCode.SHOOT else "move"}'
                    f" Actor: {action.actor} Target: {action.target}"
                )

        game.turn()


if __name__ == "__main__":
    game_session = GameSession(name="Bot_test_1")
    gbot = StepScoreBot(game_session.map)
    game_loop(gbot, game_session)

