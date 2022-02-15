def straight_dist(pos1, pos2):
    return sum(map(lambda i: abs(i[0] - i[1]), zip(pos1, pos2))) / 2


def delta(pos1, pos2):
    return tuple(map(lambda c: abs(c[0] - c[1]), zip(pos1, pos2)))


def normal(pos1, pos2):
    return tuple(
        map(
            lambda x: x[0] - x[1]
            if x[0] - x[1] == 0
            else (x[0] - x[1]) / abs(x[0] - x[1]),
            zip(pos1, pos2),
        )
    )


def multiply(c, pos):
    return tuple(map(lambda x: c * x, pos))


def summarize(pos1, pos2):
    return tuple(map(sum, zip(pos1, pos2)))
