"""
Contains functions to play the game.

"""
from game_client.server_interaction import ActionCode
from gui.game_state_property import game_state_property


def game_loop(bot, game):
    """
    Function to play the game.

    :param bot: StepScoreBot instance
    :param game: GameSession instance
    """
    while True:
        game_state = game.game_state()

        game_state_property.game_state = game_state

        if game_state["finished"]:
            print("You won" if game_state["winner"] == game.player_id else "You lost")
            print(f"Winner: {game_state['winner']}")
            break

        if game_state["current_player_idx"] == game.player_id:
            print(
                f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}"
            )
            for action in bot.get_actions(game_state):
                game.action(*action.server_format)
                print(
                    f"  Action: "
                    f'{"shoot" if action.action_code == ActionCode.SHOOT else "move"}'
                    f" Actor: {action.actor} Target: {action.target}"
                )

        game.turn()
