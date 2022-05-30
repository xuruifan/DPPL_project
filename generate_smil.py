class SMILBase():
    def __init__(self):
        pass

    def get_smil(self):
        return "SMILBase"

    def get_name(self):
        return "Base"


class SVG(SMILBase):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.objects = []
        self.animations = []

    def get_name(self):
        return f"<svg width={self.width} height={self.height}>\n"

    def get_smil(self):
        smil = self.get_name()
        for object in self.objects:
            smil = smil + object.get_smil()
        for animation in self.animations:
            smil = smil + animation.get_smil()
        smil = smil + "</svg>"
        return smil

    def append_object(self, object):
        self.objects.append(object)

    def append_animation(self, animation):
        self.animations.append(animation)


class Object(SMILBase):
    def __init__(self):
        self.animations = []

    def append_animation(self, animation):
        self.animations.append(animation)

    def get_smil(self):
        smil = self.get_name()
        for animation in self.animations:
            smil = smil + animation.get_smil()
        return smil


class Circle(Object):
    def __init__(self, id, cx, cy, r, color):
        Object.__init__(self)
        self.cx = cx
        self.cy = cy
        self.r = r
        self.color = color
        self.id = id

    def get_name(self):
        return  f"  <circle id=\"{self.id}\" r={self.r} cx={self.cx} cy={self.cy} fill=\"{self.color}\"/>\n"


class Circle(Object):
    def __init__(self, id, cx, cy, r, color):
        Object.__init__(self)
        self.cx = cx
        self.cy = cy
        self.r = r
        self.color = color
        self.id = id

    def get_name(self):
        return  f"  <circle id=\"{self.id}\" r={self.r} cx={self.cx} cy={self.cy} fill=\"{self.color}\"/>\n"


class Rectangle(Object):
    def __init__(self, id, x, y, width, height, color):
        Object.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.id = id

    def get_name(self):
        return  f"  <rect id=\"{self.id}\" x={self.x} y={self.y} width={self.width} height={self.height} fill=\"{self.color}\"/>\n"


class Text(Object):
    def __init__(self, id, x, y, color, text):
        Object.__init__(self)
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.id = id

    def get_name(self):
        return  f"  <text id=\"{self.id}\" x={self.x} y={self.y} fill=\"{self.color}\">{self.text}</text>\n"


class Animation(SMILBase):
    def __init__(self, id, attribute, _from, to, dur, begin):
        self.id = id
        self.attribute = attribute
        self._from = _from
        self.to = to
        self.dur = dur
        self.begin = begin

    def get_smil(self):
        smil = f"  <animate xlink:href=\"#{self.id}\" from={self._from} to={self.to} dur=\"{self.dur}\""
        smil = smil + f" begin=\"{self.begin}\" fill=\"freeze\" attributeName=\"{self.attribute}\""
        smil = smil + "/>\n"
        return smil


class Set(SMILBase):
    def __init__(self, id, attribute, to, begin):
        self.id = id
        self.attribute = attribute
        self.to = to
        self.begin = begin

    def get_smil(self):
        smil = f"  <set xlink:href=\"#{self.id}\" to={self.to}"
        smil = smil + f" begin=\"{self.begin}\" attributeName=\"{self.attribute}\""
        smil = smil + "/>\n"
        return smil


svg = SVG(500, 100)
svg.append_object(Circle("circle", 50, 50, 30, "orange"))
svg.append_object(Rectangle("rect", 30, 30, 30, 30, "blue"))
svg.append_object(Text("text", 50, 50, "red", "test"))
svg.append_animation(Animation("circle", "cx", 50, 450, "1s", "click"))
svg.append_animation(Set("rect", "opacity", 0, "click"))
svg.append_animation(Animation("text", "x", 50, 450, "1s", "click"))
print(svg.get_smil())
with open("test.html", "w") as f:
    f.write(svg.get_smil())