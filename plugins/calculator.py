# ============================================================
#  FreedomForge AI — plugins/calculator.py
#  Safe math calculator plugin
# ============================================================

import ast
import operator

TRIGGERS = ["calculate", "calc", "math", "/calc"]
DESCRIPTION = "Simple math calculator — try: calc 2 + 2"

ALLOWED_OPERATORS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.USub: operator.neg,
}


def _eval_expr(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left  = _eval_expr(node.left)
        right = _eval_expr(node.right)
        op    = ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator {type(node.op)}")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand)
        op      = ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator {type(node.op)}")
        return op(operand)
    else:
        raise ValueError(f"Unsupported expression type {type(node)}")


def safe_eval(expr: str):
    tree = ast.parse(expr, mode='eval')
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in ['True', 'False', 'None']:
            raise ValueError("Variable names not allowed")
        if isinstance(node, ast.Call):
            raise ValueError("Function calls not allowed")
    return _eval_expr(tree.body)


def handle(message: str) -> str:
    try:
        expr = message.lower()
        for word in ["calculate", "calc", "math", "/calc"]:
            expr = expr.replace(word, "")
        expr = expr.strip()
        if not expr:
            return "Usage: calc 2 + 2"
        result = safe_eval(expr)
        return f"✅  {expr} = {result}"
    except Exception as e:
        return f"❌  Invalid math expression: {e}"
