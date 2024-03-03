import os
import sys

from collections import namedtuple
from pathlib import Path
from loguru import logger
#from thinkpi.operations.loader import Waveforms
#from thinkpi.operations.filters import Filter

from thinkpi.config import thinkpi_conf as cfg

DataVector = namedtuple('DataVector', 'x y x_unit y_unit wave_name file_name path proc_hist')
_thinkpi_path = Path(__file__).parent.parent

for var_name, var_val in cfg.ENVIRON_VARS.items():
    os.environ[var_name] = var_val

logger.remove()
logger.add(sys.stderr, format="<cyan>{message}</cyan>", level="DEBUG")

__version__ = 'v1.0.337'
