from lark import Lark, Tree, Token
from lark.tree import Meta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Union
from collections import defaultdict
from copy import deepcopy
from argparse import ArgumentParser

import generate
from objects import *
from check import covered, overlap


class EvalException(Exception):
    def __init__(self, message, node: Union[Tree, Token]):
        self.message = message
        if isinstance(node, Tree):
            node = node.data
        self.line = node.line
        self.column = node.column

    def __str__(self):
        return f'Line {self.line}: {self.message}'


def get_parser():
    with open('grammar.lark') as f:
        return Lark(f)


@dataclass
class EvalState:
    variables: 'defaultdict[str, List[int]]' = field(default_factory=lambda: defaultdict(list))
    arrays: Dict[str, List[int]] = field(default_factory=dict)


def eval_exp(tree: Union[Tree, Token], state: EvalState):
    if isinstance(tree, Tree):
        if tree.data == 'exp_prod':
            lhs = eval_exp(tree.children[0], state)
            rhs = eval_exp(tree.children[2], state)
            if tree.children[1].value == '*':
                return lhs * rhs
            elif tree.children[1].value == '/':
                try:
                    return lhs / rhs
                except ZeroDivisionError:
                    raise EvalException('Division by zero', tree.children[1])
            else:
                raise Exception(f'unexpected operator {tree.children[1].data}')
        elif tree.data == 'exp_sum':
            lhs = eval_exp(tree.children[0], state)
            rhs = eval_exp(tree.children[2], state)
            if tree.children[1].value == '+':
                return lhs + rhs
            elif tree.children[1].value == '-':
                return lhs - rhs
            else:
                raise Exception(f'unexpected operator {tree.children[1].data}')
        elif tree.data == 'exp_max':
            return max(eval_exp(child, state) for child in tree.children)
        else:
            raise Exception(f'unexpected node {tree.data}')
    else:
        assert isinstance(tree, Token)
        if tree.type == 'N':
            return int(tree.value)
        elif tree.type == 'X':
            return state.variables[tree.value][-1]
        else:
            raise Exception(f'unexpected token type {tree.type}')


def union(first: EvalState, second: EvalState) -> EvalState:
    return second


def eval(tree: Tree, state: EvalState) -> EvalState:
    def assert_int(x, node):
        import math
        if not math.isclose(x, int(x)):
            raise EvalException(f'{x} is not an integer', node)
        return int(x)

    def get_object(tree: Tree, state: EvalState):
        var = tree.children[0].value
        dims = tuple(assert_int(eval_exp(node, state), node) for node in tree.children[1:])
        return var, dims

    if tree.data == 'terms':
        for term in tree.children:
            state = eval(term, state)
        return state
    elif tree.data == 'for':
        nv1 = eval_exp(tree.children[1], state)
        nv2 = eval_exp(tree.children[2], state)
        var = tree.children[0].value
        while nv1 <= nv2:
            state.variables[var].append(nv1)
            state = eval(tree.children[3], state)
            state.variables[var].pop()
            nv1 += 1
        return state
    elif tree.data == 'object_init':
        return state
    elif tree.data == 'shape_init':
        var, dims = get_object(tree.children[0], state)
        state.arrays[var + str(dims)] = [1, 1, 0]
        return state
    elif tree.data == 'move':
        var, dims = get_object(tree.children[0], state)
        obj = state.arrays[var + str(dims)]
        if obj[2] == 1:
            raise EvalException(f'{var} is already moving', tree.children[0])
        if obj[0] == 1:
            raise EvalException(f'{var} has not appeared', tree.children[0])
        obj[2] = 1
        return state
    elif tree.data == 'duration':
        state = eval(tree.children[1], state)
        for object in state.arrays:
            state.arrays[object][2] = 0
        return state
    else:
        assert tree.data == 'term'
        assert len(tree.children) == 2
        var, dims = get_object(tree.children[1], state)
        obj = state.arrays[var + str(dims)]
        if tree.children[0].value == 'appear' and obj[0] != 0:
            obj[0] = 0
        elif tree.children[0].value == 'disappear' and obj[0] != 1:
            obj[0] = 1
        elif tree.children[0].value == 'ignore' and obj[1] != 0:
            obj[1] = 0
        elif tree.children[0].value == 'consider' and obj[1] != 1:
            obj[1] = 1
        else:
            raise Exception(f'unexpected action {tree.children[0].value}')
        state.arrays[var + str(dims)] = obj
        return state


def get_args(args=None):
    parser = ArgumentParser()
    parser.add_argument('--input', type=str, default='input.txt')
    parser.add_argument('--output', type=str, default='test.svg')
    return parser.parse_args(args)


def main():
    from pathlib import Path
    args = get_args()
    parser = get_parser()
    tree = parser.parse(Path(args.input).read_text())
    state = EvalState()
    try:
        state = eval(tree, state)
    except EvalException as e:
        print(f'Error: {e}')
        return
    print("{")
    for object, state in state.arrays.items():
        print("\t", object, ":", "Disappear" if state[0] else "Appear", "Consider" if state[0] else "Ignore",
              "Move" if state[0] else "Static", ",")
    print("}")


if __name__ == '__main__':
    main()
