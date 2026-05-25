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


def _tokens(points):
    toks = []
    for x, y in points:
        toks.extend((x, y))
    return toks


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

    def test_core_accepts_prefix_override(self):
        points = [(0, 0), (10, 10), (11, 10), (100, 100), (200, 200)]
        packed = {_pack(x, y) for x, y in points}
        self.assertEqual(challenge6._round_best_sq(challenge6._closest_pair_sq_core(packed, 4)), 1.0)

    def test_case_prefix_keeps_large_cases_on_default(self):
        self.assertEqual(challenge6._case_prefix(1_000), 64)
        self.assertEqual(challenge6._case_prefix(300_000), 128)

    def test_parallel_x_finds_pair_across_partition_boundary(self):
        points = [(-1000, 0), (0, 500), (1, 500), (1000, 0)]
        packed = {_pack(x, y) for x, y in points}
        self.assertEqual(challenge6._closest_pair_parallel_x(packed, 2), 1.0)

    def test_axis_structure_detector_separates_random_and_grid_shapes(self):
        random_like = {_pack(i * 17, i * 31 + 7) for i in range(2048)}
        grid_like = {_pack(i % 64, i // 64) for i in range(4096)}
        self.assertFalse(challenge6._looks_axis_structured(random_like))
        self.assertTrue(challenge6._looks_axis_structured(grid_like))

    def test_rotate_scan_matches_bruteforce_and_rejects_grid_shape(self):
        points = [(0, 0), (7, 11), (5, 5), (9, 5), (100, 100)]
        packed = {_pack(x, y) for x, y in points}
        grid_like = {_pack(i % 64, i // 64) for i in range(4096)}
        self.assertEqual(challenge6._closest_pair_rotate_scan(packed), _brute(points))
        self.assertFalse(challenge6._rotate_scan_is_safe(grid_like))

    def test_raw_rotate_scan_matches_bruteforce_and_guards_shapes(self):
        points = [(0, 0), (7, 11), (5, 5), (9, 5), (100, 100)]
        self.assertEqual(
            challenge6._closest_pair_rotate_scan_raw(_tokens(points), 0, len(points)),
            _brute(points),
        )

        diag = _tokens((i, i) for i in range(20_000))
        line = _tokens((i, 0) for i in range(20_000))
        perp = []
        for i in range(20_000):
            perp.extend((19_362 * i, 6_767 * i))
        mixed_tail = _tokens((i, i) for i in range(10_000)) + _tokens(
            (19_362 * (i + 1), 6_767 * (i + 1)) for i in range(10_000)
        )

        self.assertTrue(challenge6._rotate_scan_raw_is_safe(diag, 0, 20_000))
        self.assertFalse(challenge6._rotate_scan_raw_is_safe(line, 0, 20_000))
        self.assertFalse(challenge6._rotate_scan_raw_is_safe(perp, 0, 20_000))
        self.assertFalse(challenge6._rotate_scan_raw_is_safe(mixed_tail, 0, 20_000))

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
