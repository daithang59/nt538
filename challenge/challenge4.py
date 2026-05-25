from library4students import *

G_RECORDS = None

def bottom_up_merge_sort(arr):
    n = len(arr)
    if n <= 1:
        return arr

    temp = [None] * n
    src = arr
    dst = temp

    width = 1

    while width < n:
        left = 0

        while left < n:
            mid = left + width
            right = left + width + width

            if mid > n:
                mid = n

            if right > n:
                right = n

            i = left
            j = mid
            k = left

            while i < mid and j < right:
                a = src[i]
                b = src[j]

                if a <= b:
                    dst[k] = a
                    i += 1
                else:
                    dst[k] = b
                    j += 1

                k += 1

            while i < mid:
                dst[k] = src[i]
                i += 1
                k += 1

            while j < right:
                dst[k] = src[j]
                j += 1
                k += 1

            left = right

        src, dst = dst, src
        width *= 2

    return src

def merge_two(left, right):
    n = len(left)
    m = len(right)

    result = [None] * (n + m)

    i = 0
    j = 0
    k = 0

    while i < n and j < m:
        a = left[i]
        b = right[j]

        if a <= b:
            result[k] = a
            i += 1
        else:
            result[k] = b
            j += 1

        k += 1

    while i < n:
        result[k] = left[i]
        i += 1
        k += 1

    while j < m:
        result[k] = right[j]
        j += 1
        k += 1

    return result

def sort_range(rng):
    global G_RECORDS
    l, r = rng
    part = G_RECORDS[l:r]

    return bottom_up_merge_sort(part)

def merge_chunks(chunks):
    while len(chunks) > 1:
        next_chunks = []
        i = 0

        while i < len(chunks):
            if i + 1 < len(chunks):
                next_chunks.append(merge_two(chunks[i], chunks[i + 1]))
            else:
                next_chunks.append(chunks[i])

            i += 2

        chunks = next_chunks

    return chunks[0]

def parallel_sort(records):
    global G_RECORDS
    n = len(records)
    if n <= 1:
        return records

    G_RECORDS = records

    cpu = multiprocessing.cpu_count()
    workers = min(cpu, 8)

    if n < 80000:
        workers = 1

    if workers == 1:
        return bottom_up_merge_sort(records)

    chunk_size = (n + workers - 1) // workers
    ranges = []
    start = 0

    while start < n:
        end = start + chunk_size

        if end > n:
            end = n

        ranges.append((start, end))
        start = end

    try:
        ctx = multiprocessing.get_context("fork")
    except ValueError:
        return bottom_up_merge_sort(records)

    with ctx.Pool(workers) as pool:
        chunks = pool.map(sort_range, ranges)

    return merge_chunks(chunks)

def MAIN(input_file_path):
    with open(input_file_path, "rb") as f:
        data = f.read().split()

    if len(data) == 0:
        return []

    N = int(data[0])

    records = [(-int(data[i]), data[i + 1]) for i in range(1, 2 * N, 2)]
    sorted_records = parallel_sort(records)

    return [(-item[0], item[1].decode()) for item in sorted_records]