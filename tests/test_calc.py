import pytest
from sympy import Symbol

from alf.calc import CalculationError, calculate


def test_basic_arithmetic():
    assert calculate("12 * 7") == 84.0
    assert calculate("(10 + 5) / 3") == 5.0


def test_power_operator():
    assert calculate("2^4") == 16.0


def test_implicit_multiplication():
    assert calculate("2x", symbolic=True) == 2 * Symbol("x")
    assert calculate("3(x + 1)", symbolic=True) == 3 * (Symbol("x") + 1)


def test_allowed_functions():
    x = Symbol("x")

    assert calculate("diff(x^2, x)", symbolic=True) == 2 * x
    assert calculate("integrate(x^2, x)", symbolic=True) == x**3 / 3
    assert calculate("solve(x^2 - 4, x)", symbolic=True) == [-2, 2]
    assert calculate("sin(pi / 2)") == 1.0


def test_allowed_constants():
    assert calculate("log(E)") == 1.0
    assert calculate("cos(0)") == 1.0


def test_unknown_function_is_rejected():
    with pytest.raises(CalculationError):
        calculate("tan(pi / 4)")


def test_python_import_is_rejected():
    with pytest.raises(CalculationError):
        calculate("__import__('os')")

    with pytest.raises(CalculationError):
        calculate("__import__('subprocess')")
