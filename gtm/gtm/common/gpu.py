import platform
import subprocess
import re


def get_nvidia_driver_version() -> str:
    driver_version = None
    if platform.system() == 'Linux':
        bash_command = "nvidia-smi --query-gpu=driver_version --format=csv,noheader"
        process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        if not error:
            m = re.match(r"([\d.]+)", output.decode())
            if m:
                driver_version = m.group(0)
    return driver_version
