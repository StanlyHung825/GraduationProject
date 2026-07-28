import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bbsmg.single_point import (  # noqa: E402
    BezierControlPoints,
    BrushControl,
    Point2D,
    RenderConfig,
    estimate_stroke_shape,
    load_single_point_input,
    render_stroke_mask,
    sample_cubic_bezier,
    sample_single_point_stroke,
)


class SinglePointStrokeTest(unittest.TestCase):
    def test_estimate_stroke_shape_uses_table_coefficients(self):
        shape = estimate_stroke_shape(BrushControl(h=11.0, alpha=0.0, beta=0.0))

        self.assertAlmostEqual(shape.Lt, 0.7659)
        self.assertAlmostEqual(shape.Lh, 0.2528)
        self.assertAlmostEqual(shape.Lr, 0.3766)

    def test_sample_cubic_bezier_keeps_endpoints_and_count(self):
        controls = BezierControlPoints(
            Point2D(0.0, 0.0),
            Point2D(1.0, 2.0),
            Point2D(2.0, 2.0),
            Point2D(3.0, 0.0),
        )

        points = sample_cubic_bezier(controls, 5)

        self.assertEqual(points[0], controls.p0)
        self.assertEqual(points[-1], controls.p3)
        self.assertEqual(len(points), 5)

    def test_beta_changes_contour(self):
        origin = Point2D(0.0, 0.0)
        flat = sample_single_point_stroke(origin, BrushControl(11.0, 0.0, 0.0))
        rotated = sample_single_point_stroke(origin, BrushControl(11.0, 0.0, 5.0))

        self.assertNotEqual(flat.contour, rotated.contour)

    def test_render_stroke_mask_has_ink(self):
        stroke = sample_single_point_stroke(Point2D(0.0, 0.0), BrushControl(11.0, 0.0, 0.0))
        image = render_stroke_mask(stroke, RenderConfig())

        self.assertGreater(int(image.sum()), 0)

    def test_json_input_generates_stroke_shape(self):
        origin, brush, config = load_single_point_input(ROOT / "samples" / "single_point.json")

        stroke = sample_single_point_stroke(origin, brush, config.samples_per_curve)

        self.assertEqual(origin, Point2D(0.0, 0.0))
        self.assertAlmostEqual(stroke.shape.Lt, 0.7659)
        self.assertAlmostEqual(stroke.shape.Lh, 0.2528)
        self.assertAlmostEqual(stroke.shape.Lr, 0.3766)
        self.assertEqual(len(stroke.contour), 64)

    def test_cli_writes_png_and_debug_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "bbsmg" / "single_point.py"),
                    "--input",
                    str(ROOT / "samples" / "single_point.json"),
                    "--out-dir",
                    str(out_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )

            debug = json.loads((out_dir / "single_point_debug.json").read_text(encoding="utf-8"))
            self.assertTrue((out_dir / "single_point.png").exists())
            self.assertIn("upper_control_points", debug["bezier"])
            self.assertEqual(len(debug["samples"]), 64)


if __name__ == "__main__":
    unittest.main()
