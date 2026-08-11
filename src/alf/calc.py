"""
Mathematical calculation support.

Provides safe evaluation of basic mathematical expressions.
"""

import ast
import operator

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression):
    """
    Evaluate a basic mathematical expression safely.
    """

    expression = expression.replace("^", "**")

    tree = ast.parse(expression, mode="eval")

    return _evaluate(tree.body)


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)

        return OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        operand = _evaluate(node.operand)

        return OPERATORS[type(node.op)](operand)

    raise ValueError("Unsupported expression")
