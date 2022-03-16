"""
Test for utility.coords.Coords class.
"""
# pylint: disable=missing-class-docstring, missing-function-docstring, no-self-use
# Don't think that it is really needed here
from utility.coordinates import Coords


class TestCoords:
    # Fixtures are not working for some reason
    # @pytest.fixture()
    # def zeroes_coords(self):
    #     return Coords((0, 0, 0))
    #
    # @pytest.fixture()
    # def a_coords(self):
    #     return Coords((1, -1, 0))
    #
    # @pytest.fixture()
    # def b_coords(self):
    #     return Coords((-1, 1, 0))

    def test_eq(self):
        assert Coords((1, -1, 0)) != Coords((-1, 1, 0)), (
            "__eq__ method should return false if "
            "two Coords objects are not equal"
        )
        assert Coords((1, -1, 0)) == Coords((1, -1, 0)), (
            "__eq__ method should return true if two Coords objects are equal"
        )

    def test_created_from_tuple_equals_to_created_from_dict(self):
        assert Coords((1, -2, 1)) == Coords(
            {"x": 1, "y": -2, "z": 1}
        ), "Instances created from tuple and dict with the same data are not equal"

    def test_abs(self):
        assert isinstance(
            abs(Coords((-10, 4, 6))), Coords
        ), "abs method should return Coords instance"
        assert abs(Coords((-10, 4, 6))) == Coords(
            (10, 4, 6)
        ), "abs method doesn't work as intended."

    def test_add(self):
        assert isinstance(
            Coords((1, -1, 0)) + Coords((1, -1, 0)), Coords
        ), "Sum of two Coords objects must be a Coord object"
        assert Coords((1, -1, 0)) + Coords((1, -1, 0)) == Coords(
            (2, -2, 0)
        ), "__add__ method must return (x1 + x2, y1 + y2, z1 + z2)"

    def test_sub(self):
        assert isinstance(
            Coords((1, -1, 0)) - Coords((1, -1, 0)), Coords
        ), "Sub of two Coords objects must be a Coord object"
        assert Coords((1, -1, 0)) - Coords((1, -1, 0)) == Coords(
            (0, 0, 0)
        ), "__sub__ method must return (x1 - x2, y1 - y2, z1 - z2)"

    def test_mul(self):
        assert isinstance(
            Coords((1, -1, 0)) * 2, Coords
        ), "The product of two Coords objects must be a Coord object"
        assert Coords((1, -1, 0)) * 2 == Coords(
            (2, -2, 0)
        ), "__mul__ method must return (c * x, c * y, c * z)"
        assert all(isinstance(i, int) for i in Coords((1, -1, 0)) * 2.0), (
            "The product of float and Coords must return Coords with "
            "x, y, z as integers"
        )

    def str_representation_returns_right_value(self):
        assert str(Coords((1, -1, 0))) == "Coords(1, -1, 0)", (
            "String representation of Coords object " "must look like Coords(x, y, z)"
        )

    def test_delta(self):
        assert isinstance(
            Coords((1, -1, 0)).delta(Coords((1, -1, 0))), Coords
        ), "Delta between two Coords objects must be a Coord object"
        assert Coords((1, -1, 0)).delta(Coords((1, -1, 0))) == Coords(
            (0, 0, 0)
        ), "delta method must return (abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))"
        assert Coords((0, 0, 0)).delta(Coords((1, -1, 0))) == Coords(
            (1, 1, 0)
        ), "delta method must return (abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))"

    def test_straight_dist_to(self):
        assert isinstance(
            Coords((0, 0, 0)).straight_dist_to(Coords((1, -1, 0))), int
        ), "straight_dist_to method must return integer"
        assert (
            Coords((0, 0, 0)).straight_dist_to(Coords((1, -1, 0))) == 1
        ), "straight_dist_to method must return int(sum(self.delta(other)) / 2)"

    def test_unit_vector(self):
        assert isinstance(
            Coords((1, -1, 0)).unit_vector(Coords((0, 0, 0))), Coords
        ), "unit_vector method must return Coords instance"
        assert Coords((1, -1, 0)).unit_vector(Coords((0, 0, 0))) == Coords(
            (-1, 1, 0)
        ), "unit_vector method doesn't return right value"
        assert Coords((0, 0, 0)).unit_vector(Coords((0, 0, 0))) == Coords(
            (0, 0, 0)
        ), "unit_vector method doesn't return right value"
        assert Coords((1, -1, 0)).unit_vector(Coords((1, -1, 0))) == Coords(
            (0, 0, 0)
        ), "unit_vector method doesn't return right value"

    def test_server_format(self):
        assert isinstance(
            Coords((0, 0, 0)).server_format, dict
        ), "server_format must be a dict"
        assert Coords((0, 0, 0)).server_format == {
            "x": 0,
            "y": 0,
            "z": 0,
        }, "server_format must be {'x': x, 'y': y, 'z': z}"
