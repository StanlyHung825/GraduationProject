import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bbsmg.character_simulation import (  # noqa: E402
    normalized_pixel_difference,
    render_character_from_waypoints,
)


class CharacterSimulationTest(unittest.TestCase):
    def test_render_uses_waypoints_as_1024_pixel_coordinates(self):
        image, debug = render_character_from_waypoints(
            ROOT / "samples" / "waypoint_path" / "robot_path.json"
        )

        self.assertEqual(image.shape, (1024, 1024))
        self.assertEqual(image.dtype, np.uint8)
        self.assertGreater(int(image.sum()), 0)
        self.assertEqual(debug[0]["origin"], {"x": 428.0, "y": 824.0})
        self.assertEqual(image[824, 428], 255)

    def test_normalized_pixel_difference(self):
        black = np.zeros((2, 2), dtype=np.uint8)
        white = np.full((2, 2), 255, dtype=np.uint8)

        self.assertEqual(normalized_pixel_difference(black, black), 0.0)
        self.assertEqual(normalized_pixel_difference(black, white), 1.0)

    def test_pixel_difference_requires_matching_shapes(self):
        with self.assertRaises(ValueError):
            normalized_pixel_difference(np.zeros((2, 2)), np.zeros((3, 3)))


if __name__ == "__main__":
    unittest.main()
