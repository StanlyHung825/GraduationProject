import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bbsmg.visualize_comparison import create_overlay  # noqa: E402


class VisualizeComparisonTest(unittest.TestCase):
    def test_overlay_colors_show_matches_and_misses(self):
        simulated = np.array([[0, 255, 0, 255]], dtype=np.uint8)
        ideal = np.array([[255, 255, 0, 0]], dtype=np.uint8)

        overlay = create_overlay(simulated, ideal)

        np.testing.assert_array_equal(
            overlay[0],
            [[0, 0, 0], [255, 0, 255], [0, 255, 0], [255, 255, 255]],
        )

    def test_overlay_requires_matching_shapes(self):
        with self.assertRaises(ValueError):
            create_overlay(np.zeros((2, 2)), np.zeros((3, 3)))


if __name__ == "__main__":
    unittest.main()
