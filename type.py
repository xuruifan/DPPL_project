from lark import Tree, Token
from dataclasses import dataclass, field
from typing import List, Dict, Union
from collections import defaultdict
from argparse import ArgumentParser

from objects import *


class TypeException(Exception):
    def __init__(self, message, node: Union[Tree, Token]):
        self.message = message
        if isinstance(node, Tree):
            node = node.data
        self.line = node.line
        self.column = node.column

    def __str__(self):
        return f'Line {self.line}: {self.message}'



@dataclass
class Typing:
    variables: 'defaultdict[str, List[int]]' = field(default_factory=lambda: defaultdict(list))
    arrays: Dict[str, List[int]] = field(default_factory=dict)


def eval_exp(tree: Union[Tree, Token], state: Typing):
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
                    raise TypeException('Division by zero', tree.children[1])
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


def union(first: Typing, second: Typing) -> Typing:
    return second


def type(tree: Tree, state: Typing) -> Typing:
    def assert_int(x, node):
        import math
        if not math.isclose(x, int(x)):
            raise TypeException(f'{x} is not an integer', node)
        return int(x)

    def get_object(tree: Tree, state: Typing):
        var = tree.children[0].value
        dims = tuple(assert_int(eval_exp(node, state), node) for node in tree.children[1:])
        return var, dims

    if tree.data == 'terms':
        for term in tree.children:
            state = type(term, state)
        return state
    elif tree.data == 'for':
        nv1 = eval_exp(tree.children[1], state)
        nv2 = eval_exp(tree.children[2], state)
        var = tree.children[0].value
        while nv1 <= nv2:
            state.variables[var].append(nv1)
            state = type(tree.children[3], state)
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
            raise TypeException(f'{var} is already moving', tree.children[0])
        if obj[0] == 1:
            raise TypeException(f'{var} has not appeared', tree.children[0])
        obj[2] = 1
        return state
    elif tree.data == 'duration':
        state = type(tree.children[1], state)
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
