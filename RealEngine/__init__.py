from .game import FROZEN
from . import game, camera, engine, inputs, models, render
from .render import init
import subprocess
import sys

def __install_package(name):
    if not FROZEN:
        subprocess.check_call([sys.executable, "-m", "pip", "install", name])
