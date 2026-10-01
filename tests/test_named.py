import unittest

from ncontrol import NamedParameter, NamedParameterSpace


class NamedParameterSpaceTests(unittest.TestCase):
    def setUp(self):
        self.space = NamedParameterSpace({
            "frequency": NamedParameter(20.0, 20000.0, 9, unit="Hz"),
            "amplitude": NamedParameter(0.0, 1.0, 5),
            "phase": NamedParameter(0.0, 360.0, 7, unit="deg"),
        })

    def test_names_survive_roundtrip(self):
        index = self.space.count // 3
        values = self.space.values(index)
        self.assertEqual(tuple(values), ("frequency", "amplitude", "phase"))
        self.assertEqual(self.space.nearest_index(values), index)

    def test_mapping_vector_roundtrip(self):
        values = {"frequency": 440.0, "amplitude": 0.25, "phase": 90.0}
        self.assertEqual(self.space.mapping(self.space.vector(values)), values)

    def test_dictionary_specs_are_accepted(self):
        space = NamedParameterSpace({
            "x": {"minimum": -1, "maximum": 1, "steps": 3},
            "y": {"minimum": 0, "maximum": 10, "steps": 11, "unit": "px"},
        })
        self.assertEqual(space.names, ("x", "y"))
        self.assertEqual(space.values(0), {"x": -1.0, "y": 0.0})


if __name__ == "__main__":
    unittest.main()
