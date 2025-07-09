import unittest

import helper


class TestGPProcessor(unittest.TestCase):
    """testing class for helper.py"""

    def test_preprocess_building_outlines(self):
        """tests for successfully preprocessing building outlines returned by geocoding API"""
        building_outlines = [
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-92.42324, 36.23432423],
                        [-92.32432, 36.23423],
                        [-92.235235, 36.235235],
                        [-92.325552, 36.2343243],
                        [-92.25245245, 36.425245245],
                    ]
                ],
            },
            None,
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-92.324234, 36.34141],
                            [-92.325235, 36.325235],
                            [-92.2352353, 36.235235],
                            [-92.235235, 36.2352353],
                            [-92.23523523, 36.3252353],
                        ]
                    ],
                    [
                        [
                            [-346534634, 45245245],
                            [-42524524, 2525223452],
                            [-25234532523, 2454254254],
                            [-245234523532, 5235325],
                            [-235235325, 2352353254],
                        ]
                    ],
                ],
            },
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [-92.13413414, 36.13414],
                        [-92.3124314, 36.23532],
                        [-92.5352, 36.245245],
                        [-92.25245, 36.245245],
                        [-92.245245, 36.5245245],
                    ],
                    [
                        [-5245245, 52452],
                        [-52352, 253252],
                        [-235235, 2534525],
                        [-23525, 5235323523525],
                        [-2352, 252352],
                    ],
                ],
            },
        ]

        preprocessed_outlines = helper.preprocess_building_outlines(
            building_outlines[0]
        )
        self.assertEqual(preprocessed_outlines[:7], "POLYGON")
        preprocessed_outlines = helper.preprocess_building_outlines(
            building_outlines[1]
        )
        self.assertIsNone(preprocessed_outlines)
        preprocessed_outlines = helper.preprocess_building_outlines(
            building_outlines[2]
        )
        self.assertEqual(preprocessed_outlines[:12], "MULTIPOLYGON")
        with self.assertRaises(Exception):
            helper.preprocess_building_outlines(building_outlines[3])
