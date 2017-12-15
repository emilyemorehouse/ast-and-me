import unittest
from test import support
from io import StringIO
import pstats


class AddCallersTestCase(unittest.TestCase):
    """Tests for pstats.add_callers helper."""

    def test_combine_results(self):
        target = {'a': (1, 2, 3, 4)}
        source = {'a': (1, 2, 3, 4), 'b': (5, 6, 7, 8)}
        new_callers = pstats.add_callers(target, source)
        self.assertEqual(new_callers, {'a': (2, 4, 6, 8), 'b': (5, 6, 7, 8)})
        target = {'a': 1}
        source = {'a': 1, 'b': 5}
        new_callers = pstats.add_callers(target, source)
        self.assertEqual(new_callers, {'a': 2, 'b': 5})


class StatsTestCase(unittest.TestCase):

    def setUp(self):
        stats_file = support.findfile('pstats.pck')
        self.stats = pstats.Stats(stats_file)

    def test_add(self):
        stream = StringIO()
        stats = pstats.Stats(stream=stream)
        stats.add(self.stats, self.stats)


if __name__ == '__main__':
    unittest.main()
