import trufont.objects.factories
from tfont.objects import Path, Point


def test_pathGraphicsPathFactory_qcurves():
    path_qcurve_implied = Path()
    path_qcurve_implied.points.extend(
        [
            Point(375, 39),
            Point(349, 137),
            Point(320, 238),
            Point(292, 332),
            Point(534, 291, "qcurve"),
            Point(385, 0, "line"),
        ]
    )
    assert trufont.objects.factories.pathGraphicsPathFactory(path_qcurve_implied)
