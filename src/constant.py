"""Path constants and validation helpers shared across the deltacfs pipeline."""

from src import logger_all

# Directory prefixes — relative to the project root.  All code assumes it is
# invoked from the project root; see README.md for the expected layout.
CONFIG_PREFIX = './config/'
TEMP_PREFIX = './temp/'
SRC_PREFIX = './src/'
OUTPUT_PREFIX = './output/'
LOG_PREFIX = './logs/'

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
