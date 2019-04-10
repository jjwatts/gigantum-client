import time
from typing import Tuple

from gtmcore.configuration.utils import call_subprocess
from gtmcore.logging import LMLogger


logger = LMLogger.get_logger()


def service_telemetry():
    t0 = time.time()
    mem_total, mem_avail = _calc_mem_free()
    disk_total, disk_avail = _calc_disk_free()
    rq_total, rq_free = _calc_rq_free()
    compute_time = time.time() - t0
    return {
        'memory': {
            'total': mem_total,
            'available': mem_avail
        },
        'disk': {
            'total': disk_total,
            'available': disk_avail
        },
        'rq': {
            # Total workers, and workers idle/available
            'total': rq_total,
            'available': rq_free
        },
        # How long it took to collect stats - round to two decimal places
        'collectionTimeSec': float(f'{compute_time:.2f}')
    }


def _calc_mem_free() -> Tuple[int, int]:
    mem_results = call_subprocess(['free'], cwd='/')
    hdr, vals, _, _ = mem_results.split('\n')
    mem_total, mem_available = int(vals.split()[1]), int(vals.split()[-1])
    return mem_total, mem_available


def _calc_disk_free() -> Tuple[int, int]:
    disk_results = call_subprocess("df -h /".split(), cwd='/').split('\n')
    _, disk_size, disk_used, disk_avail, use_pct, _ = disk_results[1].split()
    logger.info(disk_results)
    logger.info(f"Disk use: {disk_size}, {disk_used}, {disk_avail}, {use_pct}")
    return disk_size, disk_avail


def _calc_rq_free() -> Tuple[int, int]:
    """Parses the output of `rq info` to return total number
    of workers and the count of workers currently idle."""
    rq_out = call_subprocess("rq info".split(), cwd='/')
    logger.info(rq_out)
    total_cnt, idle_cnt = 0, 0
    for rq_line in rq_out.split('\n'):
        toks = rq_line.strip().split()
        if not toks:
            continue
        sp = toks[0].split('.')
        if len(sp) == 2 and sp[0].isalnum() and sp[1].isdigit():
            if 'idle' in toks[1]:
                idle_cnt += 1
            total_cnt += 1
        else:
            logger.info(rq_line)
    return total_cnt, idle_cnt
