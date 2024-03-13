import math

from solver import NewtonRaphson11
from solver_2 import NewtonRaphson22


def fonction_11(x):
    return x - 2

def fonction_22(x, y):
    return x - 2, 4 * y - 2


def test_newton_raphson_11():
    root_11 = NewtonRaphson11(fonction_11, [3]).final_roots
    assert math.isclose(root_11, 5.)

def test_newton_raphson_22():
    root_22 = NewtonRaphson22(fonction_22, [3, 1]).final_roots
    assert math.isclose(root_22[0], 5.)
    assert math.isclose(root_22[1], 0.75)
