"""Safe mathematical-expression evaluation and function-surface generation."""

import ast
import math
import operator

import numpy as np

try:
    from .task1 import Polyhedron
except ImportError:
    from task1 import Polyhedron


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_MATH_FUNCTIONS = {
    "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh",
    "sqrt", "exp", "log", "log10", "fabs", "floor", "ceil",
}
_DIRECT_FUNCTIONS = {"abs": abs, "min": min, "max": max}


def _validate_expression(node):
    if isinstance(node, ast.Expression):
        _validate_expression(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed")
    elif isinstance(node, ast.Name):
        if node.id not in {"x", "y"} | set(_DIRECT_FUNCTIONS):
            raise ValueError(f"Unknown name: {node.id}")
    elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        _validate_expression(node.left)
        _validate_expression(node.right)
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        _validate_expression(node.operand)
    elif isinstance(node, ast.Call):
        if node.keywords:
            raise ValueError("Keyword arguments are not allowed")
        function = node.func
        if isinstance(function, ast.Attribute):
            if (not isinstance(function.value, ast.Name) or function.value.id != "math"
                    or function.attr not in _MATH_FUNCTIONS):
                raise ValueError("Only approved math functions can be called")
        elif isinstance(function, ast.Name) and function.id in _DIRECT_FUNCTIONS:
            pass
        else:
            raise ValueError("Only approved math functions can be called")
        for argument in node.args:
            _validate_expression(argument)
    elif isinstance(node, ast.Attribute):
        if (not isinstance(node.value, ast.Name) or node.value.id != "math"
                or node.attr not in _MATH_FUNCTIONS | {"pi", "e"}):
            raise ValueError("Only math constants and approved math functions are allowed")
    else:
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def _evaluate(node, x, y):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, x, y)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id == "x":
            return x
        if node.id == "y":
            return y
        return _DIRECT_FUNCTIONS[node.id]
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Pow):
            exponent = _evaluate(node.right, x, y)
            if abs(exponent) > 100:
                raise ValueError("Exponent magnitude must not exceed 100")
            return _BINARY_OPERATORS[type(node.op)](_evaluate(node.left, x, y), exponent)
        return _BINARY_OPERATORS[type(node.op)](
            _evaluate(node.left, x, y), _evaluate(node.right, x, y)
        )
    if isinstance(node, ast.UnaryOp):
        return _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand, x, y))
    if isinstance(node, ast.Attribute):
        return getattr(math, node.attr)
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute):
            callable_ = getattr(math, function.attr)
        else:
            callable_ = _DIRECT_FUNCTIONS[function.id]
        return callable_(*[_evaluate(argument, x, y) for argument in node.args])
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def compile_function(expression):
    """Parse and validate a mathematical expression, returning f(x, y)."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError(f"Invalid function expression: {error.msg}") from error
    _validate_expression(tree)

    def function(x, y):
        return _evaluate(tree, x, y)

    return function


class FunctionSurface:
    """Create a triangulated mesh for z = f(x, y)."""

    @staticmethod
    def create_surface(func, x_range, y_range, x_steps, y_steps):
        x_min, x_max = map(float, x_range)
        y_min, y_max = map(float, y_range)
        if not all(map(math.isfinite, (x_min, x_max, y_min, y_max))):
            raise ValueError("Surface ranges must be finite")
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("Each range minimum must be less than its maximum")
        if not isinstance(x_steps, int) or isinstance(x_steps, bool) or x_steps < 2:
            raise ValueError("x_steps must be an integer of at least 2")
        if not isinstance(y_steps, int) or isinstance(y_steps, bool) or y_steps < 2:
            raise ValueError("y_steps must be an integer of at least 2")

        x_values = np.linspace(x_min, x_max, x_steps)
        y_values = np.linspace(y_min, y_max, y_steps)
        vertices = []
        vertex_grid = []
        for x in x_values:
            row = []
            for y in y_values:
                try:
                    z = float(func(float(x), float(y)))
                except (ArithmeticError, TypeError, ValueError) as error:
                    raise ValueError(f"Function failed at x={x:g}, y={y:g}: {error}") from error
                if not math.isfinite(z):
                    raise ValueError(f"Function returned a non-finite value at x={x:g}, y={y:g}")
                vertices.append([x, y, z])
                row.append(len(vertices) - 1)
            vertex_grid.append(row)

        faces = []
        for i in range(x_steps - 1):
            for j in range(y_steps - 1):
                first = vertex_grid[i][j]
                second = vertex_grid[i][j + 1]
                third = vertex_grid[i + 1][j + 1]
                fourth = vertex_grid[i + 1][j]
                faces.extend(([first, second, third], [first, third, fourth]))
        return Polyhedron(vertices, faces)
