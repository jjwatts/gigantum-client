import platform
import subprocess
import re
from typing import Optional


def get_nvidia_driver_version() -> Optional[str]:
    driver_version = None
    if platform.system() == 'Linux':
        bash_command = "nvidia-smi --query-gpu=driver_version --format=csv,noheader"
        try:
            process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            if not error:
                m = re.match(r"([\d.]+)", output.decode())
                if m:
                    driver_version = m.group(0)
        except FileNotFoundError:
            print('nvidia-smi not found, no GPU configured.')
    return driver_version
