import itertools

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
from trufont.objects.layoutEngine import LayoutEngine
from trufont.util.canvasDelete import filterSelection
from trufont.util.drawing import CreateMatrix, CreatePath
from tfont.objects import Component, Font, Layer, Path


def componentClosedGraphicsPathFactory(component):
    graphicsPath = CreatePath()
    graphicsPath.AddPath(component.layer.closedGraphicsPath)
    graphicsPath.Transform(CreateMatrix(*component.transformation))
    return graphicsPath


def componentOpenGraphicsPathFactory(component):
    graphicsPath = CreatePath()
    graphicsPath.AddPath(component.layer.openGraphicsPath)
    graphicsPath.Transform(CreateMatrix(*component.transformation))
    return graphicsPath


def fontLayoutEngineFactory(font):
    # this could be font.buildFeatures() although we might
    # want a pluggable generator so one can write custom codegen...
    features = "\n".join(
        [str(featHdr) for featHdr in font.featureHeaders]
        + [str(featCls) for featCls in font.featureClasses]
        + [str(feature) for feature in font.features]
    )
    glyphOrder = [glyph.name for glyph in font.glyphs]
    tables = {}
    # TODO: no kernWriter, but markWriter?
    if features.strip():
        otf = TTFont()
        otf.setGlyphOrder(glyphOrder)
        addOpenTypeFeaturesFromString(otf, features)
        for name in ("GDEF", "GSUB", "GPOS"):
            if name in otf:
                tables[name] = otf[name].compile(otf)
    return LayoutEngine(font, tables)


def layerClosedComponentsGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for component in layer._components:
        graphicsPath.AddPath(component.closedGraphicsPath)
    return graphicsPath


def layerClosedGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for path in layer._paths:
        if not path.open:
            graphicsPath.AddPath(path.graphicsPath)
    return graphicsPath


def layerOpenComponentsGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for component in layer._components:
        graphicsPath.AddPath(component.openGraphicsPath)
    return graphicsPath


def layerOpenGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for path in layer._paths:
        if path.open:
            graphicsPath.AddPath(path.graphicsPath)
    return graphicsPath


def pathGraphicsPathFactory(path):
    graphicsPath = CreatePath()
    points = path._points
    if not points:
        return graphicsPath
    start = points[0]
    open_ = skip = start.type == "move"
    if open_:
        graphicsPath.MoveToPoint(start.x, start.y)
    else:
        start = points[-1]
        graphicsPath.MoveToPoint(start.x, start.y)
    stack = []
    for point in points:
        if skip:
            skip = False
        elif point.type == "line":
            assert not stack
            graphicsPath.AddLineToPoint(point.x, point.y)
        else:
            stack.append(point.x)
            stack.append(point.y)
            if point.type == "curve":
                graphicsPath.AddCurveToPoint(*stack)
                stack.clear()
            # If we encounter a qcurve or the entire outline consists of
            # offcurves, we need to add implied on-curve points.
            elif point.type == "qcurve" or point is points[-1]:
                if len(stack) == 1:
                    graphicsPath.AddQuadCurveToPoint(*stack)
                    stack.clear()
                # If the stack contains just off-curve points, an on-curve
                # point is implied halfway in-between them all.
                else:
                    stack_offcurves = grouper(stack, 2)
                    for (cx1, cy1), (cx2, cy2) in pairwise(stack_offcurves):
                        graphicsPath.AddQuadCurveToPoint(cx1, cy1, (cx1 + cx2) / 2, (cy1 + cy2) / 2)
                        last_offcurve = (cx2, cy2)
                    graphicsPath.AddQuadCurveToPoint(*last_offcurve, point.x, point.y)
                stack.clear()
    if not open_:
        graphicsPath.CloseSubpath()
    return graphicsPath


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks

    grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    """
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def registerAllFactories():
    Component.closedGraphicsPathFactory = componentClosedGraphicsPathFactory
    Component.openGraphicsPathFactory = componentOpenGraphicsPathFactory
    Font.layoutEngineFactory = fontLayoutEngineFactory
    Layer.closedComponentsGraphicsPathFactory = layerClosedComponentsGraphicsPathFactory
    Layer.closedGraphicsPathFactory = layerClosedGraphicsPathFactory
    Layer.openComponentsGraphicsPathFactory = layerOpenComponentsGraphicsPathFactory
    Layer.openGraphicsPathFactory = layerOpenGraphicsPathFactory
    Layer.selectedPathsFactory = lambda layer: filterSelection(layer._paths)
    Path.graphicsPathFactory = pathGraphicsPathFactory
