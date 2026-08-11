import pytest
from sympy import Integer, Symbol, sqrt

from alf.calc import CalculationError, calculate


def test_basic_arithmetic():
    assert calculate("12 * 7") == 84
    assert calculate("(10 + 5) / 3") == Integer(5)


def test_power_operator():
    assert calculate("2^4") == 16


def test_implicit_multiplication():
    x = Symbol("x")

    assert calculate("2x") == 2 * x
    assert calculate("3(x + 1)") == 3 * (x + 1)


def test_allowed_functions():
    x = Symbol("x")

    assert calculate("diff(x^2, x)") == 2 * x
    assert calculate("integrate(x^2, x)") == x**3 / 3
    assert calculate("solve(x^2 - 4, x)") == [-2, 2]
    assert calculate("sin(pi / 2)") == 1
    assert calculate("sqrt(2)") == sqrt(2)


def test_allowed_constants():
    assert calculate("log(E)") == 1
    assert calculate("cos(0)") == 1


def test_unknown_function_is_rejected():
    with pytest.raises(CalculationError):
        calculate("tan(pi / 4)")


def test_python_import_is_rejected():
    with pytest.raises(CalculationError):
        calculate("__import__('os')")

    with pytest.raises(CalculationError):
        calculate("__import__('subprocess')")
