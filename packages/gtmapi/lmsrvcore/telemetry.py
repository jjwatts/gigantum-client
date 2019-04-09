import time
from typing import Tuple

from gtmcore.configuration.utils import call_subprocess
from gtmcore.logging import LMLogger


logger = LMLogger.get_logger()


def service_telemetry():

    # Collect telemetry every 10 seconds
    period_sec = 10

    while True:
        mem_total, mem_available= _calc_mem_free()
        _calc_disk_free()
        logger.info(f"Mem free: {(mem_available / mem_total) * 100:.2f}% ")

        time.sleep(period_sec)


def _calc_mem_free() -> Tuple[int, int]:
    mem_results = call_subprocess(['free'], cwd='/')
    hdr, vals, _, _ = mem_results.split('\n')
    mem_total, mem_available = int(vals.split()[1]), int(vals.split()[-1])
    return mem_total, mem_available


def _calc_disk_free() -> Tuple[int, int]:
    disk_results = call_subprocess("df -h /".split(), cwd='/').split('\n')
    disk_size, disk_used, disk_avail, use_pct, _, _ = disk_results[1].split()
    logger.info(f"Disk use: {disk_size}, {disk_used}, {disk_avail}, {use_pct}")
    return 0, 0


def _calc_cpu_free() -> float:
    pass
