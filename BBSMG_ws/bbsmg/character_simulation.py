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
    load_brush,
    load_render_config,
    sample_single_point_stroke,
)

IMAGE_SIZE = 1024


def render_character_from_waypoints(path: Path) -> tuple[np.ndarray, list[dict[str, Any]]]:
    waypoints, config = load_waypoint_input(path)
    image = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.uint8)
    debug = []

    for origin, brush in waypoints:
        stroke = sample_single_point_stroke(origin, brush, config.samples_per_curve)
        contour = np.rint([(point.x, point.y) for point in stroke.contour]).astype(np.int32)
        cv2.fillPoly(image, [contour], 255)
        debug.append(
            {
                "origin": asdict(origin),
                "brush": asdict(brush),
                "shape": asdict(stroke.shape),
                "sample_count": len(stroke.contour),
            }
        )

    return image, debug


def normalized_pixel_difference(simulated: np.ndarray, target: np.ndarray) -> float:
    if simulated.shape != target.shape:
        raise ValueError(f"image shapes must match: {simulated.shape} != {target.shape}")
    difference = np.abs(simulated.astype(np.float32) - target.astype(np.float32))
    return float(difference.mean() / 255.0)


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
                load_brush(point.get("brush", default_brush)),
            )
        )
    if not waypoints:
        raise ValueError("waypoints must not be empty")

    return waypoints, load_render_config(data.get("render", {}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("out/character"))
    parser.add_argument("--output-name", help="output filename without extension")
    parser.add_argument("--debug", action="store_true", help="write stroke debug JSON")
    parser.add_argument("--target", type=Path, help="white-ink-on-black grayscale reference image")
    args = parser.parse_args()

    image, debug = render_character_from_waypoints(args.input)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output_name = args.output_name or f"{args.input.stem}_sim"
    image_path = args.out_dir / f"{output_name}.png"
    cv2.imwrite(str(image_path), image)

    print(f"input={args.input}")
    print(f"image={image_path}")
    if args.debug:
        debug_path = args.out_dir / f"{output_name}_debug.json"
        debug_path.write_text(json.dumps({"strokes": debug}, indent=2) + "\n", encoding="utf-8")
        print(f"debug={debug_path}")
    print(f"stroke_count={len(debug)}")
    if args.target:
        target = cv2.imread(str(args.target), cv2.IMREAD_GRAYSCALE)
        if target is None:
            raise ValueError(f"failed to read target image: {args.target}")
        difference = normalized_pixel_difference(image, target)
        print(f"pixel_difference={difference:.6f}")
        print(f"pixel_score={1.0 - difference:.6f}")
    return 0


def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"missing required field: {key}")
    return data[key]


if __name__ == "__main__":
    raise SystemExit(main())
