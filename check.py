from geometer import *
import objects
from dataclasses import replace


def cached(cache):
  def decorator(f):
    def wrapper(a, b):
      rel = (a.x - b.x, a.y - b.y)
      if b.moving is not None:
        m = (a.moving[0] - b.moving[0], a.moving[1] - b.moving[1])
      else:
        m = a.moving
      slot = (rel, m, replace(a.value, fill=''), replace(b.value, fill=''))
      if slot in cache:
        return cache[slot]
      ret = f(a, b)
      cache[slot] = ret
      return ret
    return wrapper
  return decorator


overlap_cache = {}
@cached(overlap_cache)
def overlap(a: objects.Variable, b: objects.Variable):
  ma, mb = a.moving, b.moving
  assert ma is not None and mb is not None
  ma, mb = Point(ma[0], ma[1]), Point(mb[0], mb[1])
  m = mb - ma
  pa, pb = Point(a.x, a.y), Point(b.x, b.y)
  def get_moving_object(a: Rectangle, m: Point):
    a2 = a + m
    if m[0] > 0:
      if m[1] > 0:
        return Polygon(a[0], a[1], a2[1], a2[2], a2[3], a[3])
      elif m[1] == 0:
        return Polygon(a[0], a2[1], a2[2], a[3])
      else:
        return Polygon(a[0], a2[0], a2[1], a2[2], a[2], a[3])
    elif m[0] == 0:
      if m[1] > 0:
        return Polygon(a[0], a[1], a2[2], a2[3])
      elif m[1] == 0:
        return a
      else:
        return Polygon(a2[0], a2[1], a[2], a[3])
    else:
      if m[1] > 0:
        return Polygon(a[0], a[1], a[2], a2[2], a2[3], a2[0])
      elif m[1] == 0:
        return Polygon(a2[0], a[1], a[2], a2[3])
      else:
        return Polygon(a[1], a[2], a[3], a2[3], a2[0], a2[1])
  if isinstance(a.value, objects.Circle) and isinstance(b.value, objects.Circle):
    if m == Point(0, 0):
      return dist(pa, pb) <= a.value.r + b.value.r
    return dist(pa, Segment(pb, pb + m)) <= a.value.r + b.value.r
  elif isinstance(a.value, objects.Rect) and isinstance(b.value, objects.Rect):
    polya = Polygon(pa, pa + Point(a.value.width, 0), pa + Point(a.value.width, a.value.height), pa + Point(0, a.value.height))
    polyb = Polygon(pb, pb + Point(b.value.width, 0), pb + Point(b.value.width, b.value.height), pb + Point(0, b.value.height))
    polygon = get_moving_object(polyb, m)
    if polygon.contains(polya.vertices):
      return True
    if polya.contains(polyb.vertices):
      return True
    for i in range(4):
      if polygon.intersect(polya.edges[i]):
        return True
    return False
  elif isinstance(a.value, objects.Rect) and isinstance(b.value, objects.Circle):
    return overlap(b, a)
  elif isinstance(a.value, objects.Circle) and isinstance(b.value, objects.Rect):
    polyb = Polygon(pb, pb + Point(b.value.width, 0), pb + Point(b.value.width, b.value.height), pb + Point(0, b.value.height))
    polygon = get_moving_object(polyb, m)
    for i in range(polygon.edges.size):
      if dist(pa, polygon.edges[i]) <= a.value.r:
        return True
    return False
  else:
    raise Exception('Unsupported object type')


covered_cache = {}
@cached(covered_cache)
def covered(moving: objects.Variable, static: objects.Variable):
  m = Point(moving.moving[0], moving.moving[1])
  pm = Point(moving.x, moving.y)
  ps = Point(static.x, static.y)
  if isinstance(moving.value, objects.Circle) and isinstance(static.value, objects.Circle):
    if m == Point(0, 0):
      return dist(ps, pm) <= static.value.r - moving.value.r
    return dist(ps, Segment(pm, pm + m)) <= static.value.r - moving.value.r
  elif isinstance(moving.value, objects.Rect) and isinstance(static.value, objects.Rect):
    if moving.value.width > static.value.width:
      return False
    if moving.value.height > static.value.height:
      return False
    l = Segment(Point(0, 0), m) + pm + Point(moving.value.width/2, moving.value.height/2)
    x0 = moving.value.width / 2
    x1 = static.value.width - moving.value.width / 2
    y0 = moving.value.height / 2
    y1 = static.value.height - moving.value.height / 2
    if moving.value.width == static.moving.width:
      if moving.value.height == static.moving.height:
        p = Point(x0, y0) + ps
        return l.contains(p)
      else:
        p = Segment(Point(x0, y0), Point(x0, y1)) + ps
    else:
      if moving.value.height == static.moving.height:
        p = Segment(Point(x0, y0), Point(x1, y0)) + ps
      else:
        p = Polygon(Point(x0, y0), Point(x0, y1), Point(x1, y1), Point(x1, y0)) + ps
    return len(l.intersect(p)) > 0
  elif isinstance(moving.value, objects.Circle) and isinstance(static.value, objects.Rect):
    equivalent = objects.Variable(
      name='',
      x=moving.x - moving.value.r,
      y=moving.y - moving.value.r,
      value=objects.Rect(
        width=moving.value.r * 2,
        height=moving.value.r * 2,
        fill=''
      ),
      depth=0,
      moving=moving.moving
    )
    return covered(equivalent, static)
  elif isinstance(moving.value, objects.Rect) and isinstance(static.value, objects.Circle):
    l = Segment(Point(0, 0), -m) + ps
    points = [pm, pm + Point(moving.value.width, 0), pm + Point(moving.value.width, moving.value.height), pm + Point(0, moving.value.height)]
    for point in points:
      if dist(point, l) > static.value.r:
        return False
    return True
  else:
    raise Exception('Unsupported object type')
