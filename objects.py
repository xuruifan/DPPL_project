from dataclasses import dataclass
from typing import Union, Optional, Tuple


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
