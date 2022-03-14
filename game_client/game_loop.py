"""
Contains functions to play the game.

"""
import logging

from game_client.server_interaction import ActionCode
from gui.game_state_property import game_state_property


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


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
            for player in game_state["players"]:
                if player["idx"] == game_state['winner']:
                    winner = player["name"]
            logger.info(f"Winner: {game_state['winner']}, {winner}. Your id: {game.player_id}")
            break

        if game_state["current_player_idx"] == game.player_id:
            logger.info(
                f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}"
            )
            for action in bot.get_actions(game_state):
                game.action(*action.server_format)
                action_type = "SHOOT" if action.action_code == ActionCode.SHOOT else "MOVE"
                logger.info(
                    f"Action type: {action_type} Actor: {action.actor} Target: {action.target}"
                )

        game.turn()
