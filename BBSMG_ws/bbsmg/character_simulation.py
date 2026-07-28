from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bbsmg.single_point import (  # noqa: E402
    BrushControl,
    Point2D,
    RenderConfig,
    render_stroke_mask,
    sample_single_point_stroke,
)


def render_character_from_waypoints(path: Path) -> tuple[np.ndarray, list[dict[str, Any]]]:
    waypoints, config = load_waypoint_input(path)
    image = np.zeros((config.height, config.width), dtype=np.uint8)
    debug = []

    for origin, brush in waypoints:
        stroke = sample_single_point_stroke(origin, brush, config.samples_per_curve)
        image = np.maximum(image, render_stroke_mask(stroke, config))
        debug.append(
            {
                "origin": asdict(origin),
                "brush": asdict(brush),
                "shape": asdict(stroke.shape),
                "sample_count": len(stroke.contour),
            }
        )

    return image, debug


def load_waypoint_input(path: Path) -> tuple[list[tuple[Point2D, BrushControl]], RenderConfig]:
    data = json.loads(path.read_text(encoding="utf-8"))
    default_brush = data.get("brush")
    waypoints = []
    for point in _required(data, "waypoints"):
        point_type = point.get("type", "write")
        if point_type == "travel":
            continue
        if point_type != "write":
            raise ValueError(f"unknown waypoint type: {point_type}")
        waypoints.append(
            (
                Point2D(float(_required(point, "x")), float(_required(point, "y"))),
                _load_brush(point.get("brush", default_brush)),
            )
        )
    if not waypoints:
        raise ValueError("waypoints must not be empty")

    render = data.get("render", {})
    return (
        waypoints,
        RenderConfig(
            width=int(render.get("width", RenderConfig.width)),
            height=int(render.get("height", RenderConfig.height)),
            scale=float(render.get("scale", RenderConfig.scale)),
            samples_per_curve=int(render.get("samples_per_curve", RenderConfig.samples_per_curve)),
            padding_px=int(render.get("padding_px", RenderConfig.padding_px)),
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("BBSMG_ws/out/phase1"))
    args = parser.parse_args()

    image, debug = render_character_from_waypoints(args.input)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    image_path = args.out_dir / "character_simulation.png"
    debug_path = args.out_dir / "character_simulation_debug.json"
    cv2.imwrite(str(image_path), image)
    debug_path.write_text(json.dumps({"strokes": debug}, indent=2) + "\n", encoding="utf-8")

    print(f"input={args.input}")
    print(f"image={image_path}")
    print(f"debug={debug_path}")
    print(f"stroke_count={len(debug)}")
    return 0


def _load_brush(data: Any) -> BrushControl:
    if data is None:
        raise ValueError("missing required field: brush")
    return BrushControl(
        h=float(_required(data, "h")),
        alpha=float(_required(data, "alpha")),
        beta=float(_required(data, "beta")),
    )


def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"missing required field: {key}")
    return data[key]


if __name__ == "__main__":
    raise SystemExit(main())
