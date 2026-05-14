import subprocess
import sys

FROZEN = getattr(sys, "frozen", False)

def __install_package(name):
    if not FROZEN:
        subprocess.check_call([sys.executable, "-m", "pip", "install", name])