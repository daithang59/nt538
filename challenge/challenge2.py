from library4students import *

MAX_A = 200_000_001

def _fib_pair(n, mod):
    if n == 0:
        return (0, 1 % mod)
    a, b = 0, 1
    for bit in range(n.bit_length() - 1, -1, -1):
        d = a * ((b << 1) - a) % mod
        e = (a * a + b * b) % mod
        if (n >> bit) & 1:
            a, b = e, (d + e) % mod
        else:
            a, b = d, e
    return a, b

def _choose_window(mx):
    if mx <= 0:
        return -1
    best_w, best_c = 6, (1 << 6) + (mx >> 6)
    for w in range(7, 22):
        c = (1 << w) + (mx >> w)
        if c < best_c:
            best_c = c
            best_w = w
    return best_w if best_c <= 1_200_000 else -1

def _build_tables(mod, mx, window):
    base = 1 << window
    mask = base - 1
    f0 = [0] * base
    fp0 = [0] * base
    a, b = 0, 1 % mod
    for i in range(base):
        f0[i] = a
        fp0[i] = b
        c = a + b
        if c >= mod:
            c -= mod
        a, b = b, c
    max_high = mx >> window
    hfm = [0] * (max_high + 1)
    hf = [0] * (max_high + 1)
    sf, sfp = _fib_pair(base, mod)
    sfm = (sfp - sf) % mod
    cf, cfp, cfm = 0, 1 % mod, 1 % mod
    for h in range(max_high + 1):
        hfm[h] = cfm
        hf[h] = cf
        nf = (cf * sfm + cfp * sf) % mod
        nfp = (cf * sf + cfp * sfp) % mod
        nfm = (nfp - nf) % mod
        cf, cfp, cfm = nf, nfp, nfm
    return f0, fp0, hfm, hf, mask

_RAW = None
_OUT = None
_MOD = 1
_F0 = None
_FP0 = None
_HFM = None
_HF = None
_MASK = 0
_WIN = 14

def _worker_window(args):
    byte_start, byte_end, out_start = args
    f0 = _F0
    fp0 = _FP0
    hfm = _HFM
    hf = _HF
    mask = _MASK
    win = _WIN
    mod = _MOD

    tokens = _RAW[byte_start:byte_end].split()
    nt = len(tokens)
    buf = [0] * nt
    for j in range(nt):
        x = int(tokens[j])
        lo = x & mask
        hi = x >> win
        buf[j] = (f0[lo] * hfm[hi] + fp0[lo] * hf[hi]) % mod
    _OUT[out_start:out_start + nt] = buf

def _worker_doubling(args):
    byte_start, byte_end, out_start = args
    mod = _MOD

    tokens = _RAW[byte_start:byte_end].split()
    nt = len(tokens)
    buf = [0] * nt
    for j in range(nt):
        n = int(tokens[j])
        if n == 0:
            continue
        a, b = 0, 1
        for bit in range(n.bit_length() - 1, -1, -1):
            d = a * ((b << 1) - a) % mod
            e = (a * a + b * b) % mod
            if (n >> bit) & 1:
                a, b = e, (d + e) % mod
            else:
                a, b = d, e
        buf[j] = a
    _OUT[out_start:out_start + nt] = buf

def _find_query_start(raw, rlen):
    i = 0
    while i < rlen and raw[i] <= 32:
        i += 1
    j = i
    while j < rlen and raw[j] > 32:
        j += 1
    n = int(raw[i:j])

    i = j
    while i < rlen and raw[i] <= 32:
        i += 1
    j = i
    while j < rlen and raw[j] > 32:
        j += 1
    mod = int(raw[i:j])

    return n, mod, j


def MAIN(input_file_path):
    global _RAW, _OUT, _MOD
    global _F0, _FP0, _HFM, _HF, _MASK, _WIN

    with open(input_file_path, "rb") as f:
        raw = f.read()
    rlen = len(raw)

    n, mod, query_start = _find_query_start(raw, rlen)
    while query_start < rlen and raw[query_start] <= 32:
        query_start += 1

    if n <= 0:
        return []
    if mod == 1:
        return [0] * n

    _RAW = raw
    _MOD = mod

    window = _choose_window(MAX_A)
    use_window = window > 0

    if use_window:
        tables = _build_tables(mod, MAX_A, window)
        _F0, _FP0, _HFM, _HF, _MASK = tables
        _WIN = window
        wfunc = _worker_window
    else:
        wfunc = _worker_doubling

    if mod <= 0xFFFFFFFF:
        _OUT = multiprocessing.RawArray("I", n)
    else:
        _OUT = multiprocessing.RawArray("Q", n)

    cpus = multiprocessing.cpu_count()
    workers = min(cpus, 16)
    if n < 50_000:
        workers = 1
    elif n < 200_000:
        workers = min(workers, 4)
    elif n < 500_000:
        workers = min(workers, 8)

    if workers <= 1:
        wfunc((query_start, rlen, 0))
        return _OUT[:]

    total_bytes = rlen - query_start
    chunk_bytes = total_bytes // workers

    byte_bounds = [query_start]
    for w in range(1, workers):
        pos = query_start + w * chunk_bytes
        if pos >= rlen:
            byte_bounds.append(rlen)
        else:
            nl = raw.find(b'\n', pos)
            byte_bounds.append(nl + 1 if 0 <= nl < rlen else rlen)
    byte_bounds.append(rlen)

    chunk_counts = []
    for w in range(len(byte_bounds) - 1):
        bs = byte_bounds[w]
        be = byte_bounds[w + 1]
        if bs >= be:
            chunk_counts.append(0)
        else:
            chunk_counts.append(raw.count(b'\n', bs, be))
    total_counted = sum(chunk_counts)
    if total_counted != n:
        for w in range(len(chunk_counts) - 1, -1, -1):
            bs = byte_bounds[w]
            be = byte_bounds[w + 1]
            if bs < be:
                chunk_counts[w] += n - total_counted
                break

    args_list = []
    out_pos = 0
    for w in range(len(byte_bounds) - 1):
        bs = byte_bounds[w]
        be = byte_bounds[w + 1]
        if bs >= be:
            continue
        args_list.append((bs, be, out_pos))
        out_pos += chunk_counts[w]

    if not args_list:
        return _OUT[:]
    try:
        ctx = multiprocessing.get_context("fork")
    except ValueError:
        for args in args_list:
            wfunc(args)
        return _OUT[:]

    procs = []
    for args in args_list:
        p = ctx.Process(target=wfunc, args=(args,))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()

    return _OUT[:]