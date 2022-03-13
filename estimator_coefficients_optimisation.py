import csv
import threading
from random import uniform

from bot.step_score_bot import StepScoreBot
from game_client.server_interaction import GameSession

MAX = 10
MIN = -10


def main_game_loop(bot: StepScoreBot, game: GameSession):
    game_state = game.game_state()

    while True:
        if game_state["finished"]:
            print(game_state["players"][game_state["winner"]]["name"])
            break

        if game_state["current_player_idx"] == game.player_id:
            for action in bot.get_actions(game_state):
                game.action(*action.server_format)

        game.turn()


def game_loop(bot: StepScoreBot, game: GameSession):
    game_state = game.game_state()

    while True:
        if game_state["finished"]:
            break

        if game_state["current_player_idx"] == game.player_id:
            for action in bot.get_actions(game_state):
                game.action(*action.server_format)

        game.turn()


def main():
    prev_winner = [
        uniform(MIN, MAX),
        uniform(MIN, MAX),
        uniform(MIN, MAX),
        uniform(MIN, MAX),
    ]
    for _ in range(100):
        random_values = [
            uniform(MIN, MAX),
            uniform(MIN, MAX),
            uniform(MIN, MAX),
            uniform(MIN, MAX),
        ]
        for _ in range(5):
            ...

        with open("latest_winners.txt", "r") as f:
            for line in f:
                pass
            prev_winner: list = line.split(sep=" ")
