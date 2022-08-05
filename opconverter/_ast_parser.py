from ast import (
    BinOp,
    Call,
    Load,
    Module,
    Name,
    NodeTransformer,
    fix_missing_locations,
    parse,
    unparse,
)
from ._import_helper import add_ImportFromNode
from ._constants import BIN_OP_SPECIAL_CASES
from typing import Any


def _get_bin_conversion(op_name: str) -> str:
    return BIN_OP_SPECIAL_CASES.get(op_name, op_name.lower())


def _get_cls_name_of(obj: Any) -> str:
    cls = type(obj)
    return cls.__name__


class OperationNodeTransformer(NodeTransformer):
    def __init__(self, tree) -> None:
        self.operator_import_symbols = set()
        self.result = fix_missing_locations(self.visit(tree))

    def visit_BinOp(self, node: BinOp) -> Call:
        lhs, rhs = node.left, node.right
        op_name = _get_bin_conversion(_get_cls_name_of(node.op))
        self.operator_import_symbols.add(op_name)
        new_node = OperationNodeTransformer(
            Call(
                func=Name(id=op_name, ctx=Load()),
                args=[lhs, rhs],
                keywords=[],
            )
        )
        self.operator_import_symbols.update(new_node.operator_import_symbols)
        return new_node.result


def convert_operations(py_code: str) -> str:
    tree: Module = parse(py_code)
    new = OperationNodeTransformer(tree)
    add_ImportFromNode(new.result, "operator", new.operator_import_symbols)
    return unparse(new.result)


source = """\
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


print(fib(5))
"""
print(convert_operations(source))