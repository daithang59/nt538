from library4students import *


_global_data = b''

def _process_indices(start, end):
    total = 0
    _float = float   
    _int = int

    for token in _global_data[start:end].split():
        try:
            val = _float(token)
            if val > 0 and val.is_integer():
                i_val = _int(val)
                if i_val % 3 == 0:
                    total += i_val
        except (ValueError, OverflowError):
            pass
    return total

def MAIN(input_file_path):
    global _global_data
    
    with open(input_file_path, 'rb') as f:
        _global_data = f.read()

    if not _global_data:
        return 0

    line_end = _global_data.find(b'\n')
    if line_end == -1:
        return 0

    data_start = line_end + 1
    total_len = len(_global_data)

    if data_start >= total_len:
        return 0

    try:
        n = int(_global_data[:line_end])
        if n <= 0:
            return 0
    except ValueError:
        return 0

    data_len = total_len - data_start
    cpu = multiprocessing.cpu_count()
    if data_len < 2_000_000:
        workers = 2       
    elif data_len < 10_000_000:
        workers = min(cpu, 8)
    else:
        workers = min(cpu, 16)

    chunk_size = data_len // workers
    ranges = []
    start = data_start

    for i in range(workers):
        if i == workers - 1:
            ranges.append((start, total_len))
            break
        
        end = start + chunk_size
        while end < total_len and _global_data[end] > 32:
            end += 1
            
        if end > start:
            ranges.append((start, end))
        start = end

    with multiprocessing.Pool(processes=workers) as pool:
        parts = pool.starmap(_process_indices, ranges)

    _global_data = b''
    return sum(parts)