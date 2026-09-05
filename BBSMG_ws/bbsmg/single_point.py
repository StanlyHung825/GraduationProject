from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class BrushControl:
    h: float
    alpha: float
    beta: float


@dataclass(frozen=True)
class StrokeShape:
    Lt: float
    Lh: float
    Lr: float


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class BezierControlPoints:
    p0: Point2D
    p1: Point2D
    p2: Point2D
    p3: Point2D


@dataclass(frozen=True)
class SinglePointStroke:
    origin: Point2D
    brush: BrushControl
    shape: StrokeShape
    upper_controls: BezierControlPoints
    lower_controls: BezierControlPoints
    upper_curve: list[Point2D]
    lower_curve: list[Point2D]
    contour: list[Point2D]


@dataclass(frozen=True)
class RenderConfig:
    width: int = 1024
    height: int = 1024
    scale: float = 200.0
    samples_per_curve: int = 32


def estimate_stroke_shape(brush: BrushControl) -> StrokeShape:
    return StrokeShape(
        Lt=0.0672 * brush.h + 0.0263 * brush.alpha + 0.0191 * brush.beta + 0.0267,
        Lh=0.0196 * brush.h + 0.0039 * brush.alpha + 0.0073 * brush.beta + 0.0372,
        Lr=0.0239 * brush.h + 0.0061 * brush.alpha + 0.0096 * brush.beta + 0.1137,
    )


def build_bezier_controls(shape: StrokeShape) -> tuple[BezierControlPoints, BezierControlPoints]:
    p1x = (shape.Lt - 4.0 * shape.Lh) / 3.0
    p2x = shape.Lh
    py = 4.0 * shape.Lr / 3.0
    p0 = Point2D(-shape.Lt, 0.0)
    p3 = Point2D(shape.Lh, 0.0)
    upper = BezierControlPoints(p0, Point2D(p1x, py), Point2D(p2x, py), p3)
    lower = BezierControlPoints(p0, Point2D(p1x, -py), Point2D(p2x, -py), p3)
    return upper, lower


def sample_cubic_bezier(points: BezierControlPoints, samples: int) -> list[Point2D]:
    if samples < 2:
        raise ValueError("samples must be at least 2")
    out = []
    for i in range(samples):
        t = i / (samples - 1)
        u = 1.0 - t
        x = (
            u**3 * points.p0.x
            + 3.0 * u**2 * t * points.p1.x
            + 3.0 * u * t**2 * points.p2.x
            + t**3 * points.p3.x
        )
        y = (
            u**3 * points.p0.y
            + 3.0 * u**2 * t * points.p1.y
            + 3.0 * u * t**2 * points.p2.y
            + t**3 * points.p3.y
        )
        out.append(Point2D(x, y))
    return out


def sample_single_point_stroke(
    origin: Point2D, brush: BrushControl, samples_per_curve: int = 32
) -> SinglePointStroke:
    shape = estimate_stroke_shape(brush)
    upper_controls, lower_controls = build_bezier_controls(shape)
    upper = [_transform(point, origin, brush.beta) for point in sample_cubic_bezier(upper_controls, samples_per_curve)]
    lower = [_transform(point, origin, brush.beta) for point in sample_cubic_bezier(lower_controls, samples_per_curve)]
    return SinglePointStroke(
        origin=origin,
        brush=brush,
        shape=shape,
        upper_controls=upper_controls,
        lower_controls=lower_controls,
        upper_curve=upper,
        lower_curve=lower,
        contour=upper + list(reversed(lower)),
    )


def render_stroke_mask(stroke: SinglePointStroke, config: RenderConfig) -> np.ndarray:
    image = np.zeros((config.height, config.width), dtype=np.uint8)
    contour = np.array([_to_pixel(point, config) for point in stroke.contour], dtype=np.int32)
    cv2.fillPoly(image, [contour], 255)
    return image


def write_debug_json(stroke: SinglePointStroke, config: RenderConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "input": {
                    "x": stroke.origin.x,
                    "y": stroke.origin.y,
                    "h": stroke.brush.h,
                    "alpha": stroke.brush.alpha,
                    "beta": stroke.brush.beta,
                },
                "shape": asdict(stroke.shape),
                "bezier": {
                    "upper_control_points": _controls_to_dict(stroke.upper_controls),
                    "lower_control_points": _controls_to_dict(stroke.lower_controls),
                    "upper_samples": [asdict(point) for point in stroke.upper_curve],
                    "lower_samples": [asdict(point) for point in stroke.lower_curve],
                },
                "samples": [asdict(point) for point in stroke.contour],
                "render": asdict(config),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_single_point_input(path: Path) -> tuple[Point2D, BrushControl, RenderConfig]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return (
        Point2D(float(_required(data, "x")), float(_required(data, "y"))),
        load_brush(_required(data, "brush")),
        load_render_config(data.get("render", {})),
    )


def load_brush(data: Any) -> BrushControl:
    if data is None:
        raise ValueError("missing required field: brush")
    return BrushControl(
        h=float(_required(data, "h")),
        alpha=float(_required(data, "alpha")),
        beta=float(_required(data, "beta")),
    )


def load_render_config(data: dict[str, Any]) -> RenderConfig:
    return RenderConfig(
        width=int(data.get("width", RenderConfig.width)),
        height=int(data.get("height", RenderConfig.height)),
        scale=float(data.get("scale", RenderConfig.scale)),
        samples_per_curve=int(data.get("samples_per_curve", RenderConfig.samples_per_curve)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("out/single_point"))
    args = parser.parse_args()

    origin, brush, config = load_single_point_input(args.input)
    stroke = sample_single_point_stroke(origin, brush, config.samples_per_curve)
    image = render_stroke_mask(stroke, config)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    image_path = args.out_dir / "single_point.png"
    debug_path = args.out_dir / "single_point_debug.json"
    cv2.imwrite(str(image_path), image)
    write_debug_json(stroke, config, debug_path)

    print(f"input={args.input}")
    print(f"image={image_path}")
    print(f"debug={debug_path}")
    print(f"sample_count={len(stroke.contour)}")
    return 0


def _transform(point: Point2D, origin: Point2D, beta_degrees: float) -> Point2D:
    theta = math.radians(beta_degrees)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    return Point2D(
        origin.x + point.x * cos_t - point.y * sin_t,
        origin.y + point.x * sin_t + point.y * cos_t,
    )


def _to_pixel(point: Point2D, config: RenderConfig) -> tuple[int, int]:
    return (
        round(config.width / 2 + point.x * config.scale),
        round(config.height / 2 - point.y * config.scale),
    )


def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"missing required field: {key}")
    return data[key]


def _controls_to_dict(points: BezierControlPoints) -> dict[str, dict[str, float]]:
    return {
        "p0": asdict(points.p0),
        "p1": asdict(points.p1),
        "p2": asdict(points.p2),
        "p3": asdict(points.p3),
    }


if __name__ == "__main__":
    raise SystemExit(main())
