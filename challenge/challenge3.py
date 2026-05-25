from library4students import *

_A_DATA = []
_BT_DATA = []
_N = 0



def _int_stream(path, chunk=1 << 20):
    with open(path, "rb", buffering=chunk) as fh:
        buf = fh.read(chunk)
        num = 0
        sign = 1
        in_num = False

        while buf:
            for b in buf:
                if 48 <= b <= 57:             
                    num = num * 10 + (b - 48)
                    in_num = True
                elif b == 45:                 
                    sign = -1
                else:
                    if in_num:
                        yield sign * num
                        num = 0
                        sign = 1
                        in_num = False
                    else:
                        sign = 1
            buf = fh.read(chunk)

        if in_num:
            yield sign * num


def _mul_chunk(task):
    start_row, end_row = task
    A = _A_DATA
    BT = _BT_DATA
    N = _N

    rows_out = []
    diag_main_part = []
    diag_sec_part = []
    local_sum = 0

    for i in range(start_row, end_row):
        row_A = A[i]    
        dot_row = [0] * N
        row_sum = 0

        for j in range(N):
            row_BT = BT[j]   
            dot = sum([a * b for a, b in zip(row_A, row_BT)])
            dot_row[j] = dot
            row_sum += dot

        rows_out.append(dot_row)
        diag_main_part.append(dot_row[i])         
        diag_sec_part.append(dot_row[N - 1 - i]) 
        local_sum += row_sum

    return start_row, rows_out, diag_main_part, diag_sec_part, local_sum


def MAIN(path):
    global _A_DATA, _BT_DATA, _N

    ints = _int_stream(path)
    N = next(ints)
    _N = N

    A_data = [None] * N
    for i in range(N):
        A_data[i] = [next(ints) for _ in range(N)]

    BT_data = [[0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            BT_data[j][i] = next(ints)

    _A_DATA = A_data
    _BT_DATA = BT_data

    workers = multiprocessing.cpu_count() or 1
    if workers < 1:
        workers = 1
    if workers > N:
        workers = N

    chunks_per_worker = 4
    total_chunks = workers * chunks_per_worker
    step = (N + total_chunks - 1) // total_chunks
    if step < 1:
        step = 1
    tasks = []
    s = 0
    while s < N:
        e = s + step
        if e > N:
            e = N
        tasks.append((s, e))
        s = e

    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(processes=workers) as pool:
        res = pool.imap_unordered(_mul_chunk, tasks, chunksize=1)

        C = [None] * N
        diag_main = [0] * N
        diag_sec = [0] * N
        total_sum = 0

        for s_row, rows, dm, ds, ls in res:
            n = len(rows)
            C[s_row:s_row + n] = rows
            diag_main[s_row:s_row + n] = dm
            diag_sec[s_row:s_row + n] = ds
            total_sum += ls

    _A_DATA = []
    _BT_DATA = []
    _N = 0

    return {
        "matrix":          C,
        "diag_main":      diag_main,
        "diag_secondary": diag_sec,
        "total_sum":      total_sum,
    }
