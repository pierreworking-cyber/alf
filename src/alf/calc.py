"""
Mathematical calculation support.

Provides mathematical expression evaluation using SymPy.
"""

import re

from sympy import (
    E,
    Float,
    Function,
    I,
    Integer,
    Symbol,
    cos,
    diff,
    expand,
    factor,
    integrate,
    limit,
    log,
    pi,
    sin,
    solve,
    sqrt,
)
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


class CalculationError(ValueError):
    """
    Raised when a mathematical expression cannot be calculated.
    """


TRANSFORMATIONS = standard_transformations + (
    convert_xor,
    implicit_multiplication_application,
)


PARSER_GLOBALS = {
    "Integer": Integer,
    "Float": Float,
    "Symbol": Symbol,
    "Function": Function,
}


LOCAL_DICT = {
    "E": E,
    "I": I,
    "pi": pi,
    "cos": cos,
    "diff": diff,
    "expand": expand,
    "factor": factor,
    "integrate": integrate,
    "limit": limit,
    "log": log,
    "sin": sin,
    "solve": solve,
    "sqrt": sqrt,
}


def _validate_functions(expression):
    """
    Reject function calls outside ALF's allowed mathematical vocabulary.
    """

    for name in re.findall(r"\b[A-Za-z_]\w*\s*\(", expression):
        name = name.rstrip("(").strip()

        if name not in LOCAL_DICT:
            raise CalculationError("unsupported expression")


def calculate(expression, symbolic=False, places=3):
    """
    Evaluate a mathematical expression using the allowed SymPy vocabulary.
    """

    expression = expression.replace("^", "**")
    _validate_functions(expression)

    try:
        result = parse_expr(
            expression,
            global_dict=PARSER_GLOBALS,
            local_dict=LOCAL_DICT,
            transformations=TRANSFORMATIONS,
        )
    except (SyntaxError, TypeError, ValueError) as error:
        raise CalculationError("unsupported expression") from error

    if symbolic:
        return result

    if not result.is_number:
        raise CalculationError("invalid numeric entry")

    return round(float(result), places)
