from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def create_overlay(simulated: np.ndarray, ideal: np.ndarray) -> np.ndarray:
    if simulated.shape != ideal.shape:
        raise ValueError(f"image shapes must match: {simulated.shape} != {ideal.shape}")
    ideal_ink = 255 - ideal
    return cv2.merge((simulated, ideal_ink, simulated))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Overlay a white-on-black simulation with a black-on-white ideal image."
    )
    parser.add_argument("--simulated", type=Path, required=True)
    parser.add_argument("--ideal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    simulated = cv2.imread(str(args.simulated), cv2.IMREAD_GRAYSCALE)
    ideal = cv2.imread(str(args.ideal), cv2.IMREAD_GRAYSCALE)
    if simulated is None:
        parser.error(f"failed to read simulated image: {args.simulated}")
    if ideal is None:
        parser.error(f"failed to read ideal image: {args.ideal}")

    overlay = create_overlay(simulated, ideal)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), overlay):
        parser.error(f"failed to write output image: {args.output}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
