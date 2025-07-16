from src import logger_all

CONFIG_PREFIX = './config/'
TEMP_PREFIX = './temp/'
SRC_PREFIX = './src/'
OUTPUT_PREFIX = './output/'
LOG_PREFIX = './logs/'

class Range:
    def __init__(self, sub, up):
        self.sub = sub
        self.up = up
    def contains(self, number):
        return self.sub <= number <= self.up
    def abs_contains(self, number):
        return self.sub < number < self.up
    def __str__(self):
        return f'Range: from {self.sub} to {self.up}'

class BoolenNumber:
    def __init__(self):
        pass
    def contains(self, number):
        return number == 0 or number == 1
    def __str__(self):
        return 'int 0 or int 1'


TOF = BoolenNumber()
COS = Range(-1, 1)
ANGLE1 = Range(0, 360)
ANGLE2 = Range(-90, 90)
ANGLE3 = Range(0, 180)

constant_log = logger_all.setlogger('constant')

constant_log.debug('constant module loaded')