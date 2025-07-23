CONFIG_PREFIX = './config/' # config file route
TEMP_PREFIX = './temp/' # temp file route
SRC_PREFIX = './src/'   # src file route
OUTPUT_PREFIX = './output/' # output file route
LOG_PREFIX = './logs/' # logfile route



class Range:
    def __init__(self, sub, up) -> None:
        self.sub = sub
        self.up = up
    def contains(self, number) -> bool:
        return self.sub <= number <= self.up
    def abs_contains(self, number) -> bool:
        return self.sub < number < self.up
    def __str__(self) -> str:
        return f'Range: from {self.sub} to {self.up}'



class BoolenNumber:
    def __init__(self) -> None:
        pass
    def contains(self, number) -> bool:
        return number in (0, 1)
    def __str__(self) -> str:
        return 'int 0 or int 1'



TOF = BoolenNumber()
COS = Range(-1, 1)
ANGLE1 = Range(0, 360)
ANGLE2 = Range(-90, 90)
ANGLE3 = Range(0, 180)

from src import logger_all
constant_log = logger_all.setlogger('constant')
constant_log.debug('constant module loaded')
