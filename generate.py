class XML():
    def __init__(self, name, text="", *children, **attributes):
        self.name = name
        self.attributes = attributes
        self.children = list(children)
        self.text = text

        if 'from_' in self.attributes:
            self.attributes['from'] = self.attributes['from_']
            del self.attributes['from_']

    def append(self, child):
        self.children.append(child)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.attributes[key] = value
        else:
            assert isinstance(key, int)
            self.children[key] = value

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.attributes[key]
        else:
            assert isinstance(key, int)
            return self.children[key]

    def __delitem__(self, key):
        del self.attributes[key]

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __str__(self):
        return self.to_string()

    def to_string(self, indent=0):
        s = "  " * indent + "<" + self.name
        for key, value in self.attributes.items():
            s += f' {key}="{value}"'
        if self.children or self.text:
            s += ">\n"
            for child in self.children:
                s += child.to_string(indent + 1)
            if self.text:
                s += "  " * (indent + 1) + self.text + "\n"
            s += "  " * indent + "</" + self.name + ">\n"
        else:
            s += " />\n"
        return s

class SVG(XML):
    def __init__(self, width, height, *children, **attributes):
        attributes["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
        super().__init__("svg", *children, width="100%", height="100%", xmlns="http://www.w3.org/2000/svg", version="1.1", viewbox=f"0 0 {width} {height}", **attributes)


class Circle(XML):
    def __init__(self, cx, cy, r, *children, **attributes):
        super().__init__("circle", *children, cx=cx, cy=cy, r=r, **attributes)


class Rect(XML):
    def __init__(self, x, y, width, height, *children, **attributes):
        super().__init__("rect", *children, x=x, y=y, width=width, height=height, **attributes)


class Text(XML):
    def __init__(self, x, y, text, *children, **attributes):
        super().__init__("text", text, *children, x=x, y=y, **attributes)
        self.text = text


class Path(XML):
    def __init__(self, d, *children, **attributes):
        super().__init__("path", *children, d=d, **attributes)


class MPath(XML):
    def __init__(self, object, *children, **attributes):
        super().__init__("mpath", *children, **attributes)
        self.object = object
        assert 'id' in object.attributes
        self['xlink:href'] = "#" + object.attributes['id']


class Group(XML):
    def __init__(self, *children, **attributes):
        super().__init__("g", *children, **attributes)


class Animate(XML):
    """
    animate an attribute of an element over time
    """
    def __init__(self, attributeName, **attributes):
        if "object" in attributes:
            obj = attributes["object"]
            del attributes["object"]
            assert 'id' in obj.attributes
            attributes['xlink:href'] = "#" + obj.attributes['id']
            assert attributeName in obj.attributes
        if 'fill' not in attributes:
            attributes['fill'] = "freeze"
        super().__init__("animate", attributeName=attributeName, **attributes)


class AnimateMotion(XML):
    """
    define how an element moves along a motion path
    """
    def __init__(self, path, **attributes):
        if isinstance(path, str):
            super().__init__("animateMotion", path=path, **attributes)
        else:
            assert isinstance(path, Path)
            path = MPath(path)
            super().__init__("animateMotion", path, **attributes)


class AnimateTransform(XML):
    """
    animate a transformation attribute on its target element
    """
    def __init__(self, type, to, **attributes):
        if 'object' in attributes:
            obj = attributes['object']
            del attributes['object']
            assert 'id' in obj.attributes
            attributes['xlink:href'] = "#" + obj.attributes['id']
        super().__init__("animateTransform", type=type, to=to, attributeName="transform", **attributes)


class Set(XML):
    """
    just set the value of an attribute for a specified duration
    """
    def __init__(self, attributeName, to, **attributes):
        if 'object' in attributes:
            obj = attributes['object']
            del attributes['object']
            assert 'id' in obj.attributes
            attributes['xlink:href'] = "#" + obj.attributes['id']
        super().__init__("set", attributeName=attributeName, to=to, **attributes)


def main():
    svg = SVG(500, 100)

    circle = Circle(50, 50, 30, fill='orange', id='circle')
    svg.append(circle)
    text = Text(50, 50, "test", fill='red', id='text')
    svg.append(text)
    rect = Rect(30, 30, 30, 30, fill='blue', id='rect')
    svg.append(rect)

    svg.append(Animate('cx', from_=50, to=450, dur='1s', begin='click', object=circle))
    svg.append(Set('opacity', 0, begin='click', object=rect))
    svg.append(Animate('x', from_=50, to=450, dur='1s', begin='click', object=text))

    print(svg)
    with open("test.svg", "w") as f:
        f.write(svg.to_string())


if __name__ == "__main__":
    main()