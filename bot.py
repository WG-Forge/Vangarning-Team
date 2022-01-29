from server_interaction import ActionCode


class Bot:
    def __init__(self, game_map):
        self.map = game_map


class SimpleBot(Bot):
    # принимает словарь game_state
    # возвращает список списков. Внутренние списки: 1 позиция - ActionCode, 2 - id танка 3 - данные
    def get_actions(self, game_state):
        actions = []

        base = self.map["content"]["base"].copy()

        # выбор действия для каждого танка
        for vehicle in game_state["vehicles"].items():
            # танк не принадлежит текущему игроку
            if vehicle[1]["player_id"] != game_state["current_player_idx"]:
                continue

            # выстрел в танк с 1 хп
            made_action = False
            for enemy_vehicle in game_state["vehicles"].values():
                if enemy_vehicle["player_id"] == game_state["current_player_idx"]:
                    continue

                if enemy_vehicle["health"] == 1 and self.__can_shoot(
                    vehicle[1],
                    enemy_vehicle,
                    game_state["vehicles"],
                    game_state["attack_matrix"],
                ):
                    actions.append(
                        [ActionCode.SHOOT, vehicle[0], enemy_vehicle["position"].copy()]
                    )
                    enemy_vehicle["position"] = enemy_vehicle["spawn_position"].copy()
                    enemy_vehicle["health"] = 2
                    made_action = True
                    break
            if made_action:
                continue

            # поиск ближайшего хекса с базой
            min_dist = self.map["size"]
            closest_base = None
            for base_hex in base:
                dist = self.__dist(vehicle[1]["position"], base_hex)
                if dist < min_dist:
                    min_dist = dist
                    closest_base = base_hex
            base.remove(closest_base)

            # танк не стоит на найденной базе
            if closest_base != vehicle[1]["position"]:
                hex_closest_to_base = vehicle[1]["position"]

                # поиск ближайшего к базе хекса в зоне досягаемости танка
                for hex_pos in self.__get_hexes(vehicle[1]["position"], 0, 2):
                    dist = self.__dist(hex_pos, closest_base)
                    if dist < min_dist:

                        hex_blocked = False
                        for other_vehicle in game_state["vehicles"].values():
                            # хекс занят союзным танком / вражеским танком, хекс - не база /
                            # вражеским танком, хекс - база, невозможно выстрелить из-за расстояния
                            # - хекс отбрасывается в поиске
                            if other_vehicle["position"] == hex_pos and (
                                other_vehicle["player_id"] == vehicle[1]["player_id"]
                                or hex_pos != closest_base
                                or self.__dist(
                                    vehicle[1]["position"], other_vehicle["position"]
                                )
                                != 2
                            ):
                                hex_blocked = True
                                break
                        if hex_blocked:
                            continue

                        min_dist = dist
                        hex_closest_to_base = hex_pos

                # хекс занят вражеским танком
                # - если возможно, выстрел, иначе - пропуск хода (невозможно из-за нейтралитета)
                for other_vehicle in game_state["vehicles"].values():
                    if other_vehicle["position"] == hex_closest_to_base:
                        if self.__can_shoot(
                            vehicle[1],
                            other_vehicle,
                            game_state["vehicles"],
                            game_state["attack_matrix"],
                        ):

                            actions.append(
                                [
                                    ActionCode.SHOOT,
                                    vehicle[0],
                                    other_vehicle["position"].copy(),
                                ]
                            )
                            other_vehicle["health"] -= 1
                            made_action = True
                            break

                if made_action:
                    continue

                # хекс свободен - танк перемещается к нему
                actions.append(
                    [ActionCode.MOVE, vehicle[0], hex_closest_to_base.copy()]
                )
                vehicle[1]["position"] = hex_closest_to_base.copy()
                made_action = True

                if made_action:
                    continue

            # танк на базе, поиск противника, выстрел по возможности
            for enemy_vehicle in game_state["vehicles"].values():
                if enemy_vehicle["player_id"] == game_state["current_player_idx"]:
                    continue
                if self.__can_shoot(
                    vehicle[1],
                    enemy_vehicle,
                    game_state["vehicles"],
                    game_state["attack_matrix"],
                ):
                    actions.append(
                        [ActionCode.SHOOT, vehicle[0], enemy_vehicle["position"].copy()]
                    )
                    enemy_vehicle["health"] -= 1
                    break

        return actions

    # возвращает список с хексамами находищихся от position на расстоянии от min_dist до max_dist
    def __get_hexes(self, position, min_dist, max_dist):
        hexes = []
        for x in range(-max_dist, max_dist + 1):
            for y in range(
                max(-max_dist, -max_dist - x), min(max_dist + 1, max_dist - x + 1)
            ):
                z = -x - y
                hex_pos = {
                    "x": position["x"] + x,
                    "y": position["y"] + y,
                    "z": position["z"] + z,
                }
                dist = self.__dist(hex_pos, position)
                if dist >= min_dist:
                    hexes.append(hex_pos)
        return hexes

    # вычисляет расстояние между pos1 и pos2
    def __dist(self, pos1, pos2):
        return (
            abs(pos1["x"] - pos2["x"])
            + abs(pos1["y"] - pos2["y"])
            + abs(pos1["z"] - pos2["z"])
        ) / 2

    # проверяет, может ли shooter выстрелить в victim
    def __can_shoot(self, shooter, victim, vehicles, attack_matrix):
        # оба танка принадлежат одному игроку
        if shooter["player_id"] == victim["player_id"]:
            return False

        # проверка нейтралитета

        # атакующий был атакован целью на прошлом ходу
        shooter_was_attacked = False
        for attack in attack_matrix.items():
            if (
                vehicles[attack[1]]["player_id"] == shooter["player_id"]
                and attack[0] == victim["player_id"]
            ):
                shooter_was_attacked = True
                break

        # цель атакована другим игроком на прошлом ходу
        if not shooter_was_attacked:
            for attack in attack_matrix.items():
                if (
                    vehicles[attack[1]]["player_id"] == victim["player_id"]
                    and attack[0] != shooter["player_id"]
                ):
                    return False

        # проверка зоны поражения
        if self.__dist(shooter["position"], victim["position"]) == 2:
            return True
        return False
