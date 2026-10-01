import unittest

from ncontrol import ParameterAxis, SerpentineTraversal


class NControlTests(unittest.TestCase):
    def test_serpentine_is_bijective(self):
        traversal = SerpentineTraversal((
            ParameterAxis(0, 2, 3),
            ParameterAxis(-1, 1, 4),
            ParameterAxis(10, 20, 2),
        ))
        seen = {traversal.digits(i) for i in range(traversal.count)}
        self.assertEqual(len(seen), traversal.count)
        for i in range(traversal.count):
            self.assertEqual(traversal.index(traversal.digits(i)), i)

    def test_consecutive_states_are_grid_neighbors(self):
        traversal = SerpentineTraversal(
            tuple(ParameterAxis(0, 1, n) for n in (3, 4, 5, 2))
        )
        previous = traversal.digits(0)
        for i in range(1, traversal.count):
            current = traversal.digits(i)
            distance = sum(abs(a - b) for a, b in zip(previous, current))
            self.assertEqual(distance, 1)
            previous = current

    def test_values_and_reverse_lookup(self):
        traversal = SerpentineTraversal((
            ParameterAxis(-2, 2, 5),
            ParameterAxis(0, 10, 11),
        ))
        index = traversal.nearest_index((0.9, 7.1))
        self.assertEqual(traversal.values(index), (1.0, 7.0))
        self.assertEqual(
            traversal.from_normalized(traversal.normalized(index)),
            index,
        )


if __name__ == "__main__":
    unittest.main()
