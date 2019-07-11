import time
import glob
import os
from typing import Any, Optional, Tuple, Dict

from gtmcore.logging import LMLogger
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.configuration import Configuration
from gtmcore.configuration.utils import call_subprocess

DISK_WARNING_THRESHOLD_GB = 2.5
logger = LMLogger.get_logger()


def check_projects(config: Configuration, username: str) -> Dict[str, Any]:
    """ Crawl through all projects to check for errors on loading or accessing imporant fields.
    Warning: This method may take a while.

    Args:
        config: Configuration to include root gigantum directory
        username: Active username - if none provided crawl for all users.

    Returns:
        Dictionary mapping a project path to errors

    Schema:
    {
        'errors': {
            'username/owner/labbooks/project-name': 'This is the error msg'
        },
        '_collectionTimeSec': 2.0
    }
    """
    gigantum_root = config.app_workdir
    project_paths = glob.glob(f'{gigantum_root}/{username}/*/labbooks/*')
    inventory = InventoryManager(config.config_file)
    t0 = time.time()
    errors: Dict[str, Any] = {'errors': {}}
    for project_path in project_paths:
        try:
            # Try to load the labbook, and it's important fields.
            labbook = inventory.load_labbook_from_directory(project_path)
            _ = labbook.creation_date, labbook.modified_on, labbook.data
        except Exception as e:
            logger.error(e)
            errors['errors'][project_path.replace(gigantum_root, '')] = str(e)
    tfin = time.time()
    errors['_collectionTimeSec'] = float(f'{tfin - t0:.2f}')
    return errors


def service_telemetry():
    # TODO: Use a dataclass to represent this
    t0 = time.time()
    mem_total, mem_avail = _calc_mem_free()
    disk_total, disk_avail = _calc_disk_free()
    nvidia_driver = os.environ.get('NVIDIA_DRIVER_VERSION')
    try:
        rq_total, rq_free = _calc_rq_free()
    except:
        rq_total, rq_free = 0, 0
        
    compute_time = time.time() - t0
    return {
        'memory': {
            'total': mem_total,
            'available': mem_avail
        },
        'disk': {
            'total': disk_total,
            'available': disk_avail,
            'lowDiskWarning': disk_avail < DISK_WARNING_THRESHOLD_GB
        },
        'rq': {
            # Total workers, and workers idle/available
            'total': rq_total,
            'available': rq_free
        },
        # How long it took to collect stats - round to two decimal places
        'collectionTimeSec': float(f'{compute_time:.2f}'),
        'gpu': {
            'isAvailable': bool(nvidia_driver),
            # If None, becomes 'None'
            'nvidiaVersion': str(nvidia_driver)
        }
    }


def _calc_mem_free() -> Tuple[int, int]:
    mem_results = call_subprocess(['free'], cwd='/')
    hdr, vals, _, _ = mem_results.split('\n')
    mem_total, mem_available = int(vals.split()[1]), int(vals.split()[-1])
    return mem_total, mem_available


def _calc_disk_free() -> Tuple[float, float]:
    disk_results = call_subprocess("df -h /".split(), cwd='/').split('\n')
    _, disk_size, disk_used, disk_avail, use_pct, _ = disk_results[1].split()

    disk_size_num, disk_size_unit = float(disk_used[:-1]), disk_used[-1]
    if disk_size_unit == 'M':
        disk_size_num /= 1000.0

    disk_avail_num, disk_avail_unit = float(disk_avail[:-1]), disk_avail[-1]
    if disk_avail_unit == 'M':
        disk_avail_num /= 1000.0

    return disk_size_num, disk_avail_num


def _calc_rq_free() -> Tuple[int, int]:
    """Parses the output of `rq info` to return total number
    of workers and the count of workers currently idle."""
    rq_out = call_subprocess("rq info".split(), cwd='/')
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
    return total_cnt, idle_cnt
