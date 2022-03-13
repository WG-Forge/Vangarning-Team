from game_client.server_interaction import ActionCode
from gui.game_state_property import game_state_property


def game_loop(bot, game):
    movements = 0
    shots = 0
    while True:
        game_state = game.game_state()

        game_state_property.game_state = game_state

        if game_state["finished"]:
            print("You won" if game_state["winner"] == game.player_id else "You lost")
            print(f"Shots to movements ratio: {shots / movements if movements != 0 else '-'}")
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
