from library4students import *

DATA = None
PATTERNS = None
KEY_LEN = 0
DATA_LEN = 0

def is_ws(c):
    return c <= 32

def find_first_token_start(data, pos, n):
    while pos < n and is_ws(data[pos]):
        pos += 1
    return pos

def find_first_token_end(data, pos, n):
    while pos < n and not is_ws(data[pos]):
        pos += 1
    return pos

def worker_find(bounds):
    lo, hi = bounds
    data = DATA
    patterns = PATTERNS
    key_len = KEY_LEN
    n = DATA_LEN
    best = n

    search_end = min(n, hi + key_len + 1)
    for pat in patterns:
        start = lo - 1
        if start < 0:
            start = 0

        while True:
            found = data.find(pat, start, search_end)
            if found < 0:
                break

            token_pos = found + 1
            if token_pos >= hi:
                break

            after = token_pos + key_len
            if token_pos >= lo and (after == n or (after < n and is_ws(data[after]))):
                if token_pos < best:
                    best = token_pos
                break

            start = found + 1

    return -1 if best == n else best


def make_ranges(start, end, workers):
    size = end - start
    if size <= 0:
        return []

    chunk = (size + workers - 1) // workers
    ranges = []
    lo = start
    while lo < end:
        hi = lo + chunk
        if hi > end:
            hi = end
        ranges.append((lo, hi))
        lo = hi
    return ranges


def parallel_find(data, arr_start, key):
    global DATA, PATTERNS, KEY_LEN, DATA_LEN

    n = len(data)
    key_len = len(key)

    after_first = arr_start + key_len
    if data.startswith(key, arr_start) and (
        after_first == n or (after_first < n and is_ws(data[after_first]))
    ):
        return arr_start

    cores = multiprocessing.cpu_count()
    if cores > 4:
        cores = 4
    if cores < 2:
        cores = 2

    patterns = (b" " + key, b"\n" + key)
    ranges = make_ranges(arr_start + 1, n, cores)
    if not ranges:
        return -1

    DATA = data
    PATTERNS = patterns
    KEY_LEN = key_len
    DATA_LEN = n

    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(len(ranges)) as pool:
        hits = list(pool.map(worker_find, ranges))

    best = -1
    for hit in hits:
        if hit != -1 and (best == -1 or hit < best):
            best = hit
    return best


def index_from_offset(data, arr_start, pos):
    return data.count(b" ", arr_start, pos) + data.count(b"\n", arr_start, pos)

def MAIN(input_file_path):
    with open(input_file_path, "rb") as f:
        data = f.read()

    n = len(data)
    if n == 0:
        return -1

    key_start = find_first_token_start(data, 0, n)
    if key_start >= n:
        return -1

    key_end = find_first_token_end(data, key_start, n)
    key = data[key_start:key_end]
    arr_start = find_first_token_start(data, key_end, n)
    if arr_start >= n:
        return -1

    pos = parallel_find(data, arr_start, key)
    if pos < 0:
        return -1
    return index_from_offset(data, arr_start, pos)
