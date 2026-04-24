"""Path constants and validation helpers shared across the deltacfs pipeline."""

import os
from src import logger_all

# The project root is the parent directory of this src/ package.  All path
# constants are resolved once at import time so the code can be invoked from
# any working directory.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PREFIX = os.path.join(_PROJECT_ROOT, 'config') + os.sep
TEMP_PREFIX   = os.path.join(_PROJECT_ROOT, 'temp')   + os.sep
SRC_PREFIX    = os.path.join(_PROJECT_ROOT, 'src')     + os.sep
OUTPUT_PREFIX = os.path.join(_PROJECT_ROOT, 'output')  + os.sep
LOG_PREFIX    = os.path.join(_PROJECT_ROOT, 'logs')    + os.sep

# Shared PSCMP output filenames used by both grn_input and cmp_input modules.
GRN_OUTPUT_FILENAMES = (
    "'uz' 'ur' 'ut'\n"
    "'szz' 'srr' 'stt' 'szr' 'srt' 'stz'\n"
    "'tr' 'tt' 'rot' 'gd' 'gr'\n"
)


class Range:
    """Inclusive numeric range used for config validation."""

    def __init__(self, sub, up):
        self.sub = sub
        self.up = up

    def contains(self, number):
        return self.sub <= number <= self.up

    def __str__(self):
        return f'Range: from {self.sub} to {self.up}'


class BooleanNumber:
    """Validator for binary toggle values (0 or 1)."""

    def contains(self, number):
        return number == 0 or number == 1

    def __str__(self):
        return 'int 0 or int 1'


# Pre-constructed validators used by settings.config().
TOF = BooleanNumber()
COS = Range(-1, 1)
ANGLE1 = Range(0, 360)
ANGLE2 = Range(-90, 90)
ANGLE3 = Range(0, 180)

constant_log = logger_all.setlogger('constant')

constant_log.debug('constant module loaded')
