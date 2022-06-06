from lark import Lark, Tree, Token
from sympy import im
import generate
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Union, Optional
from collections import defaultdict
from copy import deepcopy
from argparse import ArgumentParser


def get_parser():
  with open('grammar.lark') as f:
    return Lark(f)


@dataclass(frozen=True)
class Rect:
  width: int
  height: int
  fill: str
@dataclass(frozen=True)
class Circle:
  r: int
  fill: str
@dataclass
class Variable:
  name: str
  x: int
  y: int
  value: Union[Rect, Circle]
  depth: int
  # only consider `ignored` when `appeared` is True
  appeared: bool = False
  ignored: bool = False
  moving: Optional[Tuple[int, int]] = None
@dataclass
class Array:
  values: Dict[Tuple[int, ...], Variable]
  shape: Tuple[int, ...]
  object_shape: str

@dataclass
class EvalState:
  variables: defaultdict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
  arrays: Dict[str, Array] = field(default_factory=dict)
  variable_by_depth: List[Variable] = field(default_factory=list)
  depth: int = 0

  svg: generate.SVG = field(default_factory=lambda: generate.SVG(500, 500))

  @property
  def objects(self):
    return self.svg[0]

  @property
  def timeline(self):
    return self.svg[1]

  def __post_init__(self):
    self.svg.append(generate.Group(id='objects'))
    self.svg.append(generate.Group(id='timeline'))
    animations = generate.Group(x=0, id=f'group_0')
    point = generate.Animate(
      'x', to=10,
      dur=f'0.01s',
      id=f'animate_0',
    )
    animations.append(point)
    self.add_animations(animations)

  def add_object(self, object):
    self.objects.append(object)

  def add_animations(self, group):
    self.timeline.append(group)

def eval_exp(tree: Union[Tree, Token], state: EvalState):
  if isinstance(tree, Tree):
    if tree.data == 'exp_prod':
      lhs = eval_exp(tree.children[0], state)
      rhs = eval_exp(tree.children[2], state)
      if tree.children[1].value == '*':
        return lhs * rhs
      elif tree.children[1].value == '/':
        return lhs / rhs
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

def overlap(a: Variable, b: Variable):
  # TODO: implement
  return False

def covered(moving: Variable, static: Variable):
  # TODO: implement
  return False

def eval(tree: Tree, state: EvalState) -> EvalState:
  def assert_int(x):
    import math
    assert math.isclose(x, int(x))
    return int(x)

  def get_object(tree: Tree, state: EvalState):
      var = tree.children[0].value
      dims = tuple(assert_int(eval_exp(node, state)) for node in tree.children[1:])
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
    var = tree.children[0].value
    dims = []
    node = tree.children[1]
    while isinstance(node, Tree):
      dim = assert_int(eval_exp(node.children[0], state))
      assert dim > 0
      dims.append(dim)
      node = node.children[1]
    state.arrays[var] = Array(values={}, shape=tuple(dims), object_shape=node.value)
    return state
  elif tree.data == 'shape_init':
    var, dims = get_object(tree.children[0], state)
    assert var in state.arrays
    assert len(dims) == len(state.arrays[var].shape)
    for i in range(len(dims)):
      assert dims[i] <= state.arrays[var].shape[i]
    name = '_'.join([var] + [str(i) for i in dims])
    shape_node = tree.children[1]
    if state.arrays[var].object_shape == 'Rect':
      assert len(shape_node.children) == 4 or len(shape_node.children) == 5
      x = eval_exp(shape_node.children[0], state)
      y = eval_exp(shape_node.children[1], state)
      width = eval_exp(shape_node.children[2], state)
      height = eval_exp(shape_node.children[3], state)
      if len(shape_node.children) == 5:
        fill = shape_node.children[4].value
      else:
        fill = 'ff0000'
      value = Rect(width, height, fill)
      object = generate.Rect(x, y, width, height, fill='#'+fill, id=name, opacity=0)
    elif state.arrays[var].object_shape == 'Circle':
      assert len(shape_node.children) == 3 or len(shape_node.children) == 4
      x = eval_exp(shape_node.children[0], state)
      y = eval_exp(shape_node.children[1], state)
      r = eval_exp(shape_node.children[2], state)
      if len(shape_node.children) == 4:
        fill = shape_node.children[3].value
      else:
        fill = '00ff00'
      value = Circle(r, fill)
      object = generate.Circle(x, y, r, fill='#'+fill, id=name, opacity=0)
    else:
      raise Exception(f'unexpected object shape {state.arrays[var].object_shape}')
    state.add_object(object)
    for point in state.timeline:
      point.append(generate.Set('opacity', 0, object=object, begin=f'{point.children[0]["id"]}.begin'))
    variable = Variable(
      name=name,
      x=x,
      y=y,
      value=value,
      depth=state.depth
    )
    state.arrays[var].values[dims] = variable
    state.variable_by_depth.append(variable)
    state.depth += 1
    return state
  elif tree.data == 'move':
    var, dims = get_object(tree.children[0], state)
    by1 = eval_exp(tree.children[1], state)
    by2 = eval_exp(tree.children[2], state)
    obj = state.arrays[var].values[dims]
    assert obj.moving is None and obj.appeared
    obj.moving = (by1, by2)
    return state
  elif tree.data == 'duration':
    time = eval_exp(tree.children[0], state)
    state = eval(tree.children[1], state)
    animations = generate.Group(x=0, id=f'group_{len(state.timeline)}')
    point = generate.Animate(
      'x', to=10,
      dur=f'{time}s',
      id=f'animate_{len(state.timeline)}',
      begin=f'{state.timeline[-1][0]["id"]}.end'
    )
    point_dict = {'begin': f'{point["id"]}.begin'}
    animations.append(point)
    state.add_animations(animations)
    previous_moving = []
    for var, object in zip(state.variable_by_depth, state.objects):
      object_dict = {'object': object}
      animations.append(generate.Set('opacity', 1 if var.appeared else 0, **point_dict, **object_dict))
      if isinstance(var.value, Rect):
        x_name = 'x'
        y_name = 'y'
      elif isinstance(var.value, Circle):
        x_name = 'cx'
        y_name = 'cy'
      else:
        raise Exception(f'unexpected object type {type(var.value)}')
      if var.moving:
        if var.moving[0] != 0:
          animations.append(generate.Animate(
            attributeName=x_name,
            by=var.moving[0],
            dur=f'{time}s',
            **object_dict,
            **point_dict
          ))
        if var.moving[1] != 0:
          animations.append(generate.Animate(
            attributeName=y_name,
            by=var.moving[1],
            dur=f'{time}s',
            **object_dict,
            **point_dict
          ))
        copy = deepcopy(var)
        if not var.ignored:
          for previous in previous_moving:
            assert not overlap(var, previous)
          previous_moving.append(copy)
        var.x += var.moving[0]
        var.y += var.moving[1]
        var.moving = None
      else:
        if not var.ignored:
          for previous in previous_moving:
            assert not covered(previous, var)
    return state
  else:
    assert tree.data == 'term'
    assert len(tree.children) == 2
    var, dims = get_object(tree.children[1], state)
    obj = state.arrays[var].values[dims]
    if tree.children[0].value == 'appear':
      obj.appeared = True
    elif tree.children[0].value == 'disappear':
      obj.appeared = False
    elif tree.children[0].value == 'ignore':
      obj.ignored = True
    elif tree.children[0].value == 'consider':
      obj.ignored = False
    else:
      raise Exception(f'unexpected action {tree.children[0].value}')
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
  state = eval(tree, state)
  with open(args.output, 'w') as f:
    f.write(state.svg.to_string())

if __name__ == '__main__':
  main()
