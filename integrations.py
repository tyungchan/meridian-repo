import ast
import operator

import requests


def fetch_provider_status(url):
    return requests.get(url, timeout=5).text


_MAX_EXPRESSION_LENGTH = 1000

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

_UNARY_OPS = {
    ast.Not: operator.not_,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}


def _safe_eval_node(node, names):
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body, names)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        raise ValueError(f"Unknown name in rule: {node.id!r}")
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result = True
            for value in node.values:
                result = _safe_eval_node(value, names)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = _safe_eval_node(value, names)
                if result:
                    return result
            return result
        raise ValueError("Unsupported boolean operator")
    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported unary operator")
        return op(_safe_eval_node(node.operand, names))
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported binary operator")
        return op(_safe_eval_node(node.left, names), _safe_eval_node(node.right, names))
    if isinstance(node, ast.Compare):
        left = _safe_eval_node(node.left, names)
        for op_node, comparator in zip(node.ops, node.comparators):
            op = _CMP_OPS.get(type(op_node))
            if op is None:
                raise ValueError("Unsupported comparison operator")
            right = _safe_eval_node(comparator, names)
            if not op(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Subscript):
        container = _safe_eval_node(node.value, names)
        key = _safe_eval_node(node.slice, names)
        return container[key]
    if isinstance(node, ast.Attribute):
        if node.attr.startswith("_"):
            raise ValueError("Access to private attributes is not allowed")
        value = _safe_eval_node(node.value, names)
        if isinstance(value, dict):
            return value[node.attr]
        return getattr(value, node.attr)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        items = [_safe_eval_node(elt, names) for elt in node.elts]
        if isinstance(node, ast.List):
            return items
        if isinstance(node, ast.Tuple):
            return tuple(items)
        return set(items)
    if isinstance(node, ast.Dict):
        return {
            _safe_eval_node(k, names): _safe_eval_node(v, names)
            for k, v in zip(node.keys, node.values)
        }
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def evaluate_rule(expression, claim):
    if not isinstance(expression, str):
        raise ValueError("Rule expression must be a string")
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise ValueError("Rule expression is too long")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid rule expression: {exc}") from exc
    return _safe_eval_node(tree, {"claim": claim})
