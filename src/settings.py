from src import constant, logger_all
from pandas import read_csv
import math

settings_log = logger_all.setlogger('settings')

def depth_minmax():
    # get min and max depth from file "receiving_fault.dat", return array (depth_min, depth_max)

    columns = ['n', 'O_lat', 'O_lon', 'O_depth', 'length', 'width', 'strike', 'dip']
    rf_data = read_csv(constant.CONFIG_PREFIX + 'receiving_fault.dat', sep=r'\s+', names=columns, comment='#')

    O_depth = rf_data['O_depth']
    width = rf_data['width']
    dip = rf_data['dip']


    depth_stretch = O_depth + width * math.cos(math.radians(dip))
    depth_min = math.floor(min([min(O_depth), min(depth_stretch)]))
    depth_max = math.ceil(max([max(O_depth), max(depth_stretch)]))
    depth_range = [depth_min, depth_max]

    assert depth_min >= 0, 'depth_min'
    assert depth_max > depth_min, 'depth_range'

    settings_log.debug(f'print depth_minmax output: {depth_range}')

    return depth_range


def calculation_setting():
    # read calculation settings from file "calculation_setting.dat", return a float depth_step and a list storing other info

    calculation_settings = []

    with open(constant.CONFIG_PREFIX + 'calculation_setting.dat', 'r') as calculation_setting:
        for line in calculation_setting:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            calculation_settings.append(values)
    depth_step = float(calculation_settings[0][0])

    assert depth_step > 0, 'depth_step'

    settings_log.debug(f'print calculation_setting output: depth_step {depth_step}, calculation_settings {calculation_settings}')

    return depth_step, calculation_settings



def config():
    # read config.dat file and return a list with info
    configs = []

    with open(constant.CONFIG_PREFIX + 'config.dat', 'r') as calculation_setting:
        for line in calculation_setting:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            configs.append(values)
    
    settings_log.debug(f'config.dat read result: {configs}')


    assert constant.TOF.contains(int(configs[0][0])), 'insar(1/0)'
    if len(configs[0]) > 1:
        assert constant.COS.contains(float(configs[0][1])), 'insar cosine value'
        assert constant.COS.contains(float(configs[0][2])), 'insar cosine value'
        assert constant.COS.contains(float(configs[0][3])), 'insar cosine value'
    assert constant.TOF.contains(int(configs[1][0])), 'icmb'
    if len(configs[1]) > 1:
        assert float(configs[1][1]) > 0, 'friction factor'
        assert constant.ANGLE1.contains(float(configs[1][3])), 'strike'
        assert constant.ANGLE2.contains(float(configs[1][4])), 'dip'
        assert constant.ANGLE3.contains(float(configs[1][5])), 'slip'
    
    settings_log.debug(f'configs: {configs}')

    return configs