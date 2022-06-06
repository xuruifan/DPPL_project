from lark import Lark, Tree, Token
import generate
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Union, Optional
from collections import defaultdict
from copy import deepcopy


def get_parser():
  with open('grammar.lark') as f:
    return Lark(f)


@dataclass(frozen=True)
class Rect:
  width: int
  height: int
@dataclass(frozen=True)
class Circle:
  r: int
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

  svgs: List[generate.SVG] = field(default_factory=list)


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
    elif tree.data == 'exp_max':
      lhs = eval_exp(tree.children[2], state)
      rhs = eval_exp(tree.children[4], state)
      return max(lhs, rhs)
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
    shape_node = tree.children[1]
    if state.arrays[var].object_shape == 'Rect':
      assert len(shape_node.children) == 4
      x = eval_exp(shape_node.children[0], state)
      y = eval_exp(shape_node.children[1], state)
      width = eval_exp(shape_node.children[2], state)
      height = eval_exp(shape_node.children[3], state)
      value = Rect(width, height)
    elif state.arrays[var].object_shape == 'Circle':
      assert len(shape_node.children) == 3
      x = eval_exp(shape_node.children[0], state)
      y = eval_exp(shape_node.children[1], state)
      r = eval_exp(shape_node.children[2], state)
      value = Circle(r)
    else:
      raise Exception(f'unexpected object shape {state.arrays[var].object_shape}')
    variable = Variable(
      name='_'.join([var] + [str(i) for i in dims]),
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
    svg = generate.SVG(width=500, height=500)
    time = eval_exp(tree.children[0], state)
    state = eval(tree.children[1], state)
    previous_moving = []
    animations = []
    for var in state.variable_by_depth:
      if not var.appeared:
        continue
      if isinstance(var.value, Rect):
        obj = generate.Rect(
          x=var.x,
          y=var.y,
          width=var.value.width,
          height=var.value.height,
          fill='#ff0000',
          id=var.name
        )
        x_name = 'x'
        y_name = 'y'
      elif isinstance(var.value, Circle):
        obj = generate.Circle(
          cx=var.x,
          cy=var.y,
          r=var.value.r,
          fill='#00ff00',
          id=var.name
        )
        x_name = 'cx'
        y_name = 'cy'
      else:
        raise Exception(f'unexpected object type {type(var.value)}')
      svg.append(obj)
      if var.moving:
        if var.moving[0] != 0:
          animations.append(generate.Animate(
            attributeName=x_name,
            by=var.moving[0],
            dur=f'{time}s',
            object=obj
          ))
        if var.moving[1] != 0:
          animations.append(generate.Animate(
            attributeName=y_name,
            by=var.moving[1],
            dur=f'{time}s',
            object=obj
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
    for animation in animations:
      svg.append(animation)
    state.svgs.append(svg)
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


def main():
  parser = get_parser()
  tree = parser.parse("""
  C = Array(2, Array(2, Rect));
  for (i = 0 -> 2) for (j = 0 -> 2) {
    C[i][j] := Rect(i*50+300, j*50+300, 30, 30);
    appear C[i][j]
  };
  A = Array(2, Array(2, Circle));
  for (i = 0 -> 2) for (j = 0 -> 2) {
    A[i][j] := Circle(265-i*50-j*50, j*50+315, 5);
    appear A[i][j]
  };
  B = Array(2, Array(2, Circle));
  for (i = 0 -> 2) for (j = 0 -> 2) {
    B[i][j] := Circle(315+i*50, 265-i*50-j*50, 5);
    appear B[i][j]
  };
  tmp = Array(2, Array(2, Circle));
  for (i = 0 -> 2) for (j = 0 -> 2)
    tmp[i][j] := Circle(i*50+315, j*50+315, 10);
  duration 1
    for (i = 0 -> 2) for (j = 0 -> 2) {
      move A[i][j] by 10, 0;
      move B[i][j] by 0, 10
    };
  for (time = 0 -> 2) {
    duration 3
      for (i = 0 -> 2) for (j = 0 -> 2) {
        move A[i][j] by 30, 0;
        move B[i][j] by 0, 30
      };
    for (i = 0 -> 2) for (j = 0 -> 2) {
      ignore A[i][j];
      ignore B[i][j]
    };
    duration 2
      for (i = 0 -> 2) for (j = 0 -> 2) {
        move A[i][j] by 20, 0;
        move B[i][j] by 0, 20
      };
    for (i = 0 -> 2) for (j = 0 -> 2) {
      consider A[i][j];
      consider B[i][j]
    }
  };
  for (time = 0 -> 2) {
    for(i= 0 -> time) {
      disappear A[i][time-i];
      disappear B[i][time-i];
      appear tmp[i][time-i]
    };
    duration 3
      for (i = 0 -> 2) for (j = max(0, time+1-i) -> 2) {
        move A[i][j] by 30, 0;
        move B[i][j] by 0, 30
      };
    for (i = 0 -> 2) for (j = 0 -> 2) {
      ignore A[i][j];
      ignore B[i][j]
    };
    duration 2
      for (i = 0 -> 2) for (j = max(0, time+1-i) -> 2) {
        move A[i][j] by 20, 0;
        move B[i][j] by 0, 20
      };
    for (i = 0 -> 2) for (j = 0 -> 2) {
      consider A[i][j];
      consider B[i][j]
    }
  }
  """)
  from pathlib import Path
  state = EvalState()
  state = eval(tree, state)
  output_dir = Path('output')
  output_dir.mkdir(exist_ok=True)
  for file in output_dir.glob('*.svg'):
    file.unlink()
  for i, svg in enumerate(state.svgs):
    with open(f'output/{i}.svg', 'w') as f:
      f.write(svg.to_string())

if __name__ == '__main__':
  main()
