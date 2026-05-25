import importlib
import math
import multiprocessing
import os
import random
import sys
import tempfile
import types
import unittest


stub = types.ModuleType("library4students")
stub.math = math
stub.multiprocessing = multiprocessing
sys.modules.setdefault("library4students", stub)

challenge6 = importlib.import_module("challenge.challenge6")


def _pack(x, y):
    return ((x + challenge6._OFFSET) << 32) | (y + challenge6._OFFSET)


def _brute(points):
    best = 10**40
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        for j in range(i + 1, len(points)):
            x2, y2 = points[j]
            dx = x1 - x2
            dy = y1 - y2
            ds = dx * dx + dy * dy
            if ds < best:
                best = ds
    return round(math.sqrt(best), 4)


class Challenge6Tests(unittest.TestCase):
    def test_main_matches_statement_sample(self):
        raw = b"""2
4
4 0
8 9
0 4
2 0
4
2 0
1 6
3 9
3 10
"""
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            fh.write(raw)
            path = fh.name
        try:
            self.assertEqual(challenge6.MAIN(path), [2.0, 1.0])
        finally:
            os.unlink(path)

    def test_duplicate_points_return_zero(self):
        raw = b"""1
3
1 2
5 8
1 2
"""
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            fh.write(raw)
            path = fh.name
        try:
            self.assertEqual(challenge6.MAIN(path), [0.0])
        finally:
            os.unlink(path)

    def test_core_matches_bruteforce_on_small_random_sets(self):
        random.seed(1234)
        for n in range(2, 50):
            for _ in range(40):
                seen = set()
                points = []
                while len(points) < n:
                    p = (random.randint(-100, 100), random.randint(-100, 100))
                    if p not in seen:
                        seen.add(p)
                        points.append(p)
                packed = {_pack(x, y) for x, y in points}
                self.assertEqual(challenge6._closest_pair_core(packed), _brute(points))

    def test_parallel_x_finds_pair_across_partition_boundary(self):
        points = [(-1000, 0), (0, 500), (1, 500), (1000, 0)]
        packed = {_pack(x, y) for x, y in points}
        self.assertEqual(challenge6._closest_pair_parallel_x(packed, 2), 1.0)

    def test_parallel_plan_keeps_small_two_case_inputs_serial(self):
        ranges = [(1, 20_000), (40_002, 20_000)]
        self.assertEqual(challenge6._choose_parallel_plan(2, 40_000, ranges, 8), (1, 1))

    def test_parallel_plan_starts_moderate_multi_case_inputs(self):
        ranges = [(1, 10_000), (20_002, 10_000), (40_003, 10_000), (60_004, 10_000)]
        self.assertEqual(challenge6._choose_parallel_plan(4, 40_000, ranges, 8), (4, 1))

    def test_parallel_plan_batches_many_tiny_balanced_cases(self):
        ranges = [(1 + i * 2001, 1_000) for i in range(100)]
        self.assertEqual(challenge6._choose_parallel_plan(100, 100_000, ranges, 20), (20, 2))


if __name__ == "__main__":
    unittest.main()
