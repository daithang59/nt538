from library4students import *



_G_TOKENS = None
_G_RANGES = None

_OFFSET = 2000000000
_MASK = (1 << 32) - 1
_SHIFT = 1 << 32

_PREFIX = 256

_NEIGH_DELTA = (
    -_SHIFT - 1, -_SHIFT, -_SHIFT + 1,
    -1,          0,       1,
     _SHIFT - 1,  _SHIFT,  _SHIFT + 1,
)


def _closest_pair_core(pts_set):
    n = len(pts_set)

    if n < 2:
        return 0.0

    pts = list(pts_set)

    MASK = _MASK
    NEIGH_DELTA = _NEIGH_DELTA
    int_type = int
    isqrt = math.isqrt
    sqrt = math.sqrt

    prefix_len = _PREFIX if n >= _PREFIX else n

    seed = 123456789
    for i in range(prefix_len):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        j = i + (seed % (n - i))
        pts[i], pts[j] = pts[j], pts[i]

    best_sq = 10 ** 40

    for i in range(prefix_len - 1):
        pi = pts[i]
        px = pi >> 32
        py = pi & MASK

        for j in range(i + 1, prefix_len):
            q = pts[j]
            dx = px - (q >> 32)
            dy = py - (q & MASK)
            ds = dx * dx + dy * dy

            if ds < best_sq:
                if ds <= 1:
                    return float(ds)
                best_sq = ds

    if n <= prefix_len:
        return round(sqrt(best_sq), 4)

    d = isqrt(best_sq)
    if d == 0:
        d = 1

    grid = {}
    gget = grid.get

    for i in range(prefix_len):
        p = pts[i]

        key = (((p >> 32) // d) << 32) | ((p & MASK) // d)

        old = gget(key)
        if old is None:
            grid[key] = p
        elif type(old) is int_type:
            grid[key] = [old, p]
        else:
            old.append(p)

    for i in range(prefix_len, n):
        p = pts[i]

        px = p >> 32
        py = p & MASK

        cx = px // d
        cy = py // d
        base_key = (cx << 32) | cy

        updated = False

        for delta in NEIGH_DELTA:
            b = gget(base_key + delta)

            if b is not None:
                if type(b) is int_type:
                    dx = px - (b >> 32)
                    dy = py - (b & MASK)
                    ds = dx * dx + dy * dy

                    if ds < best_sq:
                        if ds <= 1:
                            return 1.0
                        best_sq = ds
                        updated = True
                else:
                    for q in b:
                        dx = px - (q >> 32)
                        dy = py - (q & MASK)
                        ds = dx * dx + dy * dy

                        if ds < best_sq:
                            if ds <= 1:
                                return 1.0
                            best_sq = ds
                            updated = True

        if updated:
            new_d = isqrt(best_sq)
            if new_d == 0:
                new_d = 1

            if new_d != d:
                d = new_d

                grid.clear()
                gget = grid.get

                for j in range(i + 1):
                    q = pts[j]

                    key = (((q >> 32) // d) << 32) | ((q & MASK) // d)

                    old = gget(key)
                    if old is None:
                        grid[key] = q
                    elif type(old) is int_type:
                        grid[key] = [old, q]
                    else:
                        old.append(q)
                continue

        old = gget(base_key)
        if old is None:
            grid[base_key] = p
        elif type(old) is int_type:
            grid[base_key] = [old, p]
        else:
            old.append(p)

    return round(sqrt(best_sq), 4)


def _choose_parallel_plan(Q, total_n, ranges, cpu):
    if Q <= 1 or cpu <= 1:
        return 1, 1

    workers = min(cpu, Q)
    if workers <= 1:
        return 1, 1

    max_n = 0
    for _, n in ranges:
        if n > max_n:
            max_n = n

    if max_n < 128:
        return 1, 1

    if Q == 2 and total_n < 80000:
        return 1, 1

    if Q < 4 and total_n < 60000:
        return 1, 1

    if Q < 8 and total_n < 30000:
        return 1, 1

    chunksize = 1
    avg_n = total_n // Q
    if Q >= workers * 4 and avg_n <= 2000 and max_n <= avg_n * 2:
        chunksize = 2

    return workers, chunksize


def _solve_one_raw(case_idx):
    global _G_TOKENS, _G_RANGES

    toks = _G_TOKENS
    start, N = _G_RANGES[case_idx]

    OFFSET = _OFFSET
    end = start + 2 * N

    pts_set = {
        ((toks[k] + OFFSET) << 32) | (toks[k + 1] + OFFSET)
        for k in range(start, end, 2)
    }

    if len(pts_set) < N:
        return case_idx, 0.0

    return case_idx, _closest_pair_core(pts_set)


def MAIN(input_file_path):
    global _G_TOKENS, _G_RANGES

    with open(input_file_path, "rb") as f:
        tokens = list(map(int, f.read().split()))

    if not tokens:
        return []

    Q = tokens[0]

    if Q == 0:
        return []

    ranges = []
    total_n = 0
    idx = 1

    for _ in range(Q):
        N = tokens[idx]
        idx += 1

        start = idx
        idx += 2 * N

        ranges.append((start, N))
        total_n += N

    _G_TOKENS = tokens
    _G_RANGES = ranges

    if Q == 1:
        return [_solve_one_raw(0)[1]]

    cpu = multiprocessing.cpu_count()
    workers, chunksize = _choose_parallel_plan(Q, total_n, ranges, cpu)

    if workers <= 1:
        return [_solve_one_raw(i)[1] for i in range(Q)]

    order = list(range(Q))
    order.sort(key=lambda i: ranges[i][1], reverse=True)

    answers = [0.0] * Q

    try:
        ctx = multiprocessing.get_context("fork")
    except ValueError:
        return [_solve_one_raw(i)[1] for i in range(Q)]

    with ctx.Pool(processes=workers) as pool:
        for idx_result, ans in pool.imap_unordered(_solve_one_raw, order, chunksize=chunksize):
            answers[idx_result] = ans

    return answers
