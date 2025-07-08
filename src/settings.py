from src import constant, logger_all
from os.path import exists
import math

settings_log = logger_all.setlogger('settings')

def depth_minmax():
    # get min and max depth from file "receiving_fault.dat", return array (depth_min, depth_max)
    depth = []
    depth_stretch = []
    with open(constant.CONFIG_PREFIX + 'receiving_fault.dat', 'r') as receiving_fault:
        for line in receiving_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            split_line = stripped_line.split()
            depth.append(float(split_line[3]))
            depth_stretch.append(float(split_line[3]) + float(split_line[5]) * math.sin(math.radians(float(split_line[7]))))

    settings_log.debug(f'print depth_minmax reading result: O_depth {depth}, dip {depth_stretch}')

    depth_min = math.floor(min([min(depth), min(depth_stretch)]))
    depth_max = math.ceil(max([max(depth), max(depth_stretch)]))
    depth_range = [depth_min, depth_max]

    assert depth_min >= 0, 'depth_min'
    assert depth_max > depth_min, 'depth_range'

    settings_log.debug(f'print depth_minmax calculation result: depth_stretch {depth_stretch}, depth_range {depth_range}')

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

def combine_file(filename, depth):
    
    settings_log.debug(f'will operate file {constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename}')
    
    assert exists(constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename), f'empty output file in {depth}'

    with open(constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename, 'r') as read_file, \
        open(constant.OUTPUT_PREFIX + filename, 'a') as write_file:
        
        with open(constant.OUTPUT_PREFIX + filename, 'r') as temp_file:
            if (temp_file.read() == ''):
                settings_log.debug(f'{filename} is found empty when processing depth {depth}, preparing to write title in it')
                write_file.write('depth[km] ')
                write_file.write(read_file.readline())
            
        for i, line in enumerate(read_file):
            if i <= 2: continue

            stripped_line = line.strip()
            cleaned_line = ' '.join(stripped_line.split())
            write_file.write(str(depth) + ' ')
            write_file.write(cleaned_line + '\n')
    
    settings_log.debug(f'successfully rewrite file {filename} at depth {depth} to output file')