"""
Optimizes weights for step score bot
"""

from os import cpu_count
from queue import Queue
from random import randint, seed, uniform
from threading import Lock, Thread

from bot.step_score_bot import StepScoreBot
from game_client.game_loop import game_loop
from game_client.server_interaction import GameSession

MAX = 10
MIN = -10

# pylint: disable=C0103
# these are not constants
queue = Queue(maxsize=cpu_count())
game_count = 0
loses = 0
draws = 0
game_results_lock = Lock()
lock = Lock()


def generate_weights():
    """
    Generates WEIGHTS_COUNT number of random weights
    :return:
    """
    return tuple(uniform(MIN, MAX) for _ in range(WEIGHTS_COUNT))


# pylint: disable=W0603
# global variables needed for thread communication
def test_weights_once(weights):
    """
    Plays game with bot with given weighs and 2 bots with random weights
    :param weights:
    :return:
    """
    with lock:
        global game_count
        game_name = "optimize_" + str(game_count)
        game_count += 1

    game1 = GameSession(name="Bot_test_1", game=game_name, num_players=3)
    game2 = GameSession(
        name="Bot_test_2",
        game=game_name,
    )
    game3 = GameSession(
        name="Bot_test_3",
        game=game_name,
    )

    order = randint(0, 2)
    optimizing_bot = StepScoreBot(game1.map, estimator_weights=weights)

    games = [game1, game2, game3]
    bots = []
    for i in range(3):
        if i == order:
            bots.append(optimizing_bot)
        else:
            bots.append(StepScoreBot(game1.map, estimator_weights=generate_weights()))

    tr1 = Thread(target=game_loop, args=(bots[0], game1))
    tr2 = Thread(target=game_loop, args=(bots[1], game2))
    tr3 = Thread(target=game_loop, args=(bots[2], game3))

    tr1.start()
    tr2.start()
    tr3.start()

    tr1.join()
    tr2.join()
    tr3.join()

    game_state = games[order].game_state()
    player_id = games[order].player_id
    global loses
    global draws

    with game_results_lock:
        if game_state["winner"] is None:
            draws += 1
        elif isinstance(game_state["winner"], int):
            if player_id != game_state["winner"]:
                loses += 1
        else:
            if player_id in game_state["winner"]:
                draws += 1
            else:
                loses += 1


GAMES_TO_TEST_VALUE = 20


def test_weights(weights):
    """
    Test bot's weight in GAMES_TO_TEST_VALUE number of games
    :param weights:
    :return:
    """
    for _ in range(GAMES_TO_TEST_VALUE):
        queue.put(lambda: test_weights_once(weights))

    queue.join()

    with game_results_lock:
        global loses
        global draws
        result = (loses + draws / 2) / GAMES_TO_TEST_VALUE
        loses = 0
        draws = 0

    return result


THRESHOLD = 0.5
REFLECTION = 1.0
CONTRACTION = 0.5
EXTENSION = 2.0


def write_point(starting_point, point, value):
    """
    Writes point and it's value to the file named as starting point
    :param starting_point:
    :param point:
    :param value:
    :return:
    """
    file_name = ""
    for coef in starting_point:
        file_name += str(coef) + " "

    with open("weights/" + file_name + ".txt", "a", encoding="utf8") as file:
        file_str = ""
        for coef in point:
            file_str += str(coef) + " "
        file.write(file_str + "=== " + str(value) + "\n")


def replace_point(points, values, current_point, new_point):
    """
    Replaces point in points list and values dict with new point
    :param points:
    :param values:
    :param current_point:
    :param new_point:
    :return:
    """
    points.remove(current_point)
    points.append(new_point)
    values[new_point] = new_point
    values.pop(current_point)


def homothety(points, values, lowest_point):
    """
    Moves all points to the center of the distance to the lowest point
    :param points:
    :param values:
    :param lowest_point:
    :return:
    """
    points.remove(lowest_point)
    points = [
        tuple(
            (point[coord] + lowest_point[coord]) / 2
            for coord in range(len(lowest_point))
        )
        for point in points
    ]

    lowest_value = values[lowest_point]
    values = {}
    for point in points:
        values[point] = test_weights(point)
    values[lowest_point] = lowest_value

    points.append(lowest_point)
    return points, values


def exit_condition(points):
    """
    Exit condition for optimizing loop
    :param points:
    :return:
    """
    weights_count = len(points[0])
    average_values = [
        sum(point[coord] for point in points) / len(points)
        for coord in range(weights_count)
    ]
    dispersions = [
        sum(point[coord] ** 2 for point in points) / len(points)
        - average_values[coord] ** 2
        for coord in range(weights_count)
    ]

    return all(dispersion <= THRESHOLD for dispersion in dispersions)


def optimize_from_random(points: list[tuple]):
    """
    Optimizes weights using Nelder–Mead method
    :param points:
    :return:
    """
    starting_point = points[0]
    weights_count = len(points[0])

    values = {}
    for point in points:
        values[point] = test_weights(point)

    while exit_condition(points):

        points = sorted(points, reverse=True, key=lambda point: values[point])

        highest_point = points[0]
        average_point = points[1]
        lowest_point = points[len(points) - 1]

        write_point(starting_point, lowest_point, values[lowest_point])

        center_point = tuple(
            sum(point[coord] for point in points) / weights_count
            for coord in range(weights_count)
        )

        reflected_point = tuple(
            (1 + REFLECTION) * center_point[coord] - REFLECTION * highest_point[coord]
            for coord in range(weights_count)
        )
        reflected_value = test_weights(reflected_point)

        if reflected_value < values[lowest_point]:
            extended_point = tuple(
                (
                    (1 - EXTENSION) * center_point[coord]
                    + EXTENSION * reflected_point[coord]
                )
                for coord in range(weights_count)
            )
            extended_value = test_weights(extended_point)

            points.remove(highest_point)
            if extended_value < reflected_value:
                points.append(extended_point)
                values[extended_point] = extended_value
            else:
                points.append(reflected_point)
                values[reflected_point] = reflected_value
            values.pop(highest_point)

        elif values[lowest_point] <= reflected_value < values[average_point]:
            replace_point(points, values, highest_point, reflected_point)

        else:
            if values[average_point] <= reflected_value < values[highest_point]:
                replace_point(points, values, highest_point, reflected_point)

                highest_point, reflected_point = reflected_point, highest_point

            contraction_point = tuple(
                (
                    (1 - CONTRACTION) * center_point[coord]
                    + CONTRACTION * highest_point[coord]
                )
                for coord in range(weights_count)
            )
            contraction_value = test_weights(contraction_point)

            if contraction_value < values[highest_point]:
                replace_point(points, values, highest_point, contraction_point)

            else:
                points, values = homothety(points, values, lowest_point)

    points = sorted(points, reverse=True, key=lambda point: values[point])
    write_point(
        starting_point, points[len(points) - 1], values[points[len(points) - 1]]
    )


def worker():
    """
    Function for worker threads
    :return:
    """
    while True:
        task = queue.get()
        task()
        queue.task_done()


WEIGHTS_COUNT = 5


def main():
    """
    Creates worker threads and call optimizing function
    :return:
    """
    max_threads = 20

    seed()
    threads = []
    for _ in range(max_threads):
        thread = Thread(target=worker)
        thread.start()
        threads.append(thread)

    optimize_from_random([generate_weights() for i in range(WEIGHTS_COUNT + 1)])


if __name__ == "__main__":
    main()
