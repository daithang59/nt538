from library4students import *



_G_TOKENS = None
_G_RANGES = None
_G_SORTED_PTS = None
_G_WORKER_PREFIX = 128

_OFFSET = 2000000000
_MASK = (1 << 32) - 1
_SHIFT = 1 << 32

_PREFIX = 128
_SMALL_PREFIX = 64
_STRUCTURED_PREFIX = 384
_ROT_ANGLE = 1.23456789
_ROT_C = math.cos(_ROT_ANGLE)
_ROT_S = math.sin(_ROT_ANGLE)

_NEIGH_DELTA = (
    -_SHIFT - 1, -_SHIFT, -_SHIFT + 1,
    -1,          0,       1,
     _SHIFT - 1,  _SHIFT,  _SHIFT + 1,
)


def _round_best_sq(best_sq):
    if best_sq <= 1:
        return float(best_sq)
    return round(math.sqrt(best_sq), 4)


def _closest_pair_sq_core(pts_source, prefix):
    n = len(pts_source)

    if n < 2:
        return 0

    MASK = _MASK
    NEIGH_DELTA = _NEIGH_DELTA
    int_type = int
    isqrt = math.isqrt

    pts = list(pts_source)

    prefix_len = prefix if n >= prefix else n

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
                    return ds
                best_sq = ds

    if n <= prefix_len:
        return best_sq

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
                            return ds
                        best_sq = ds
                        updated = True
                else:
                    for q in b:
                        dx = px - (q >> 32)
                        dy = py - (q & MASK)
                        ds = dx * dx + dy * dy

                        if ds < best_sq:
                            if ds <= 1:
                                return ds
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

    return best_sq


def _case_prefix(n):
    if n <= 1500:
        return _SMALL_PREFIX
    return _PREFIX


def _closest_pair_core(pts_set, prefix=None):
    if prefix is None:
        prefix = _PREFIX
    return _round_best_sq(_closest_pair_sq_core(pts_set, prefix))


def _looks_axis_structured(pts_set):
    sample_limit = 2048

    xs = set()
    ys = set()
    count = 0

    for p in pts_set:
        xs.add(p >> 32)
        ys.add(p & _MASK)
        count += 1
        if count >= sample_limit:
            break

    if count < 512:
        return False

    duplicate_x = count - len(xs)
    duplicate_y = count - len(ys)
    return duplicate_x >= count // 8 or duplicate_y >= count // 8


def _rotate_scan_is_safe(pts_set):
    n = len(pts_set)
    if n < 20000:
        return False

    MASK = _MASK
    OFFSET = _OFFSET
    C = _ROT_C
    S = _ROT_S

    sample_limit = 2048
    sample = []
    xs = set()
    ys = set()

    for p in pts_set:
        x = (p >> 32) - OFFSET
        y = (p & MASK) - OFFSET
        sample.append(complex(x * C - y * S, x * S + y * C))
        xs.add(x)
        ys.add(y)
        if len(sample) >= sample_limit:
            break

    count = len(sample)
    if count < 512:
        return False

    duplicate_x = count - len(xs)
    duplicate_y = count - len(ys)
    if duplicate_x >= count // 8 or duplicate_y >= count // 8:
        return False

    sample.sort(key=lambda p: p.real)

    best = float("inf")
    for i in range(count - 1):
        pi = sample[i]
        limit = i + 9
        if limit > count:
            limit = count
        for j in range(i + 1, limit):
            d = abs(sample[j] - pi)
            if d < best:
                best = d

    if best == float("inf"):
        return False

    total_candidates = 0
    max_total = count * 5
    for i in range(count - 1):
        px = sample[i].real
        for j in range(i + 1, count):
            if sample[j].real - px >= best:
                break
            total_candidates += 1
            if total_candidates > max_total:
                return False

    return True


def _rotate_scan_raw_is_safe(toks, start, n):
    if n < 20000:
        return False

    C = _ROT_C
    S = _ROT_S

    sample_limit = 2048
    sample_count = sample_limit if n >= sample_limit else n

    sample = []
    xs = set()
    ys = set()

    for i in range(sample_count):
        k = start + 2 * ((i * n) // sample_count)
        x = toks[k]
        y = toks[k + 1]
        sample.append(complex(x * C - y * S, x * S + y * C))
        xs.add(x)
        ys.add(y)

    count = len(sample)
    if count < 512:
        return False

    duplicate_x = count - len(xs)
    duplicate_y = count - len(ys)
    if duplicate_x >= count // 8 or duplicate_y >= count // 8:
        return False

    sample.sort(key=lambda p: p.real)

    best = float("inf")
    for i in range(count - 1):
        pi = sample[i]
        limit = i + 9
        if limit > count:
            limit = count
        for j in range(i + 1, limit):
            d = abs(sample[j] - pi)
            if d < best:
                best = d

    if best == float("inf"):
        return False

    total_candidates = 0
    max_total = count * 5
    for i in range(count - 1):
        px = sample[i].real
        for j in range(i + 1, count):
            if sample[j].real - px >= best:
                break
            total_candidates += 1
            if total_candidates > max_total:
                return False

    return True


def _closest_pair_rotate_scan(pts_set):
    n = len(pts_set)
    if n < 2:
        return 0.0

    MASK = _MASK
    OFFSET = _OFFSET
    C = _ROT_C
    S = _ROT_S

    pts = [
        complex(
            ((p >> 32) - OFFSET) * C - ((p & MASK) - OFFSET) * S,
            ((p >> 32) - OFFSET) * S + ((p & MASK) - OFFSET) * C,
        )
        for p in pts_set
    ]

    pts.sort(key=lambda p: p.real)

    best = float("inf")
    for i in range(n):
        pi = pts[i]
        px = pi.real

        for j in range(i + 1, n):
            pj = pts[j]
            if pj.real - px >= best:
                break

            d = abs(pj - pi)
            if d < best:
                if d <= 1e-7:
                    return 0.0
                best = d

    return round(best, 4)


def _closest_pair_rotate_scan_raw(toks, start, n):
    if n < 2:
        return 0.0

    C = _ROT_C
    S = _ROT_S
    end = start + 2 * n

    pts = [
        complex(toks[k] * C - toks[k + 1] * S, toks[k] * S + toks[k + 1] * C)
        for k in range(start, end, 2)
    ]

    pts.sort(key=lambda p: p.real)

    best = float("inf")
    for i in range(n):
        pi = pts[i]
        px = pi.real

        for j in range(i + 1, n):
            pj = pts[j]
            if pj.real - px >= best:
                break

            d = abs(pj - pi)
            if d < best:
                if d <= 1e-7:
                    return 0.0
                best = d

    return round(best, 4)


def _closest_pair_range_worker(rng):
    global _G_SORTED_PTS, _G_WORKER_PREFIX

    lo, hi = rng
    if hi - lo < 2:
        return 10 ** 40
    return _closest_pair_sq_core(_G_SORTED_PTS[lo:hi], _G_WORKER_PREFIX)


def _strip_best_sq(strip, best_sq):
    MASK = _MASK

    strip.sort(key=lambda p: p & MASK)

    m = len(strip)
    for i in range(m - 1):
        p = strip[i]
        px = p >> 32
        py = p & MASK

        j = i + 1
        while j < m:
            q = strip[j]
            dy = (q & MASK) - py
            dy_sq = dy * dy
            if dy_sq >= best_sq:
                break

            dx = px - (q >> 32)
            ds = dx * dx + dy_sq
            if ds < best_sq:
                if ds <= 1:
                    return ds
                best_sq = ds

            j += 1

    return best_sq


def _closest_pair_parallel_x(pts_set, workers):
    global _G_SORTED_PTS

    n = len(pts_set)
    if n < 2:
        return 0.0
    if workers <= 1 or n < 120000:
        return _closest_pair_core(pts_set)

    workers = min(workers, 4, n // 30000)
    if workers <= 1:
        return _closest_pair_core(pts_set)

    pts = sorted(pts_set)
    step = (n + workers - 1) // workers
    ranges = []

    start = 0
    while start < n:
        end = start + step
        if end > n:
            end = n
        ranges.append((start, end))
        start = end

    try:
        ctx = multiprocessing.get_context("fork")
    except ValueError:
        return _closest_pair_core(pts_set)

    _G_SORTED_PTS = pts
    _G_WORKER_PREFIX = _STRUCTURED_PREFIX
    try:
        with ctx.Pool(processes=len(ranges)) as pool:
            best_sq = min(pool.map(_closest_pair_range_worker, ranges))
    finally:
        _G_SORTED_PTS = None
        _G_WORKER_PREFIX = _PREFIX

    if best_sq <= 1:
        return float(best_sq)

    strip_limit = 200000
    for _, end in ranges[:-1]:
        split_x = pts[end] >> 32
        strip = []
        append = strip.append

        i = end - 1
        while i >= 0:
            p = pts[i]
            dx = split_x - (p >> 32)
            if dx * dx >= best_sq:
                break
            append(p)
            i -= 1

        i = end
        while i < n:
            p = pts[i]
            dx = (p >> 32) - split_x
            if dx * dx >= best_sq:
                break
            append(p)
            i += 1

        if len(strip) > strip_limit:
            return _closest_pair_core(pts_set)

        best_sq = _strip_best_sq(strip, best_sq)
        if best_sq <= 1:
            return 1.0

    return _round_best_sq(best_sq)


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


def _solve_one_raw(case_idx, use_inner_parallel=False):
    global _G_TOKENS, _G_RANGES

    toks = _G_TOKENS
    start, N = _G_RANGES[case_idx]

    OFFSET = _OFFSET
    end = start + 2 * N

    if _rotate_scan_raw_is_safe(toks, start, N):
        return case_idx, _closest_pair_rotate_scan_raw(toks, start, N)

    pts_set = {
        ((toks[k] + OFFSET) << 32) | (toks[k + 1] + OFFSET)
        for k in range(start, end, 2)
    }

    if len(pts_set) < N:
        return case_idx, 0.0

    if use_inner_parallel and _looks_axis_structured(pts_set):
        return case_idx, _closest_pair_parallel_x(pts_set, multiprocessing.cpu_count())

    return case_idx, _closest_pair_core(pts_set, _case_prefix(N))


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
        return [_solve_one_raw(0, True)[1]]

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
