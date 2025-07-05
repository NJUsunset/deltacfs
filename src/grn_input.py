TEST = False
import pandas
from src.constant import *
import math
import os
import numpy
if __name__ == '__main__':
    print('INFO: grn_input.py testing...')
    TEST = True # mark for test info and test code

def depth_minmax():
    # get min and max depth from file "receiving_fault.dat", return array (depth_min, depth_max)

    columns = ['n', 'O_lat', 'O_lon', 'O_depth', 'length', 'width', 'strike', 'dip']
    rf_data = pandas.read_csv(CONFIG_PREFIX + 'receiving_fault.dat', sep=r'\s+', names=columns, comment='#')

    O_depth = rf_data['O_depth']
    width = rf_data['width']
    dip = rf_data['dip']

    depth_stretch = O_depth + width * numpy.cos(numpy.deg2rad(dip))
    depth_min = math.floor(min([min(O_depth), min(depth_stretch)]))
    depth_max = math.ceil(max([max(O_depth), max(depth_stretch)]))
    depth_range = [depth_min, depth_max]

    if TEST: print('INFO: print depth_minmax output.'); print(depth_range)

    return depth_range


def calculation_setting():
    # read calculation settings from file "calculation_setting.dat", return a float depth_step and a list storing other info

    calculation_settings = []

    with open(CONFIG_PREFIX + 'calculation_setting.dat', 'r') as calculation_setting:
        for line in calculation_setting:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            calculation_settings.append(values)
    depth_step = float(calculation_settings[0][0])

    if TEST: print('INFO: print calculation_setting output.'); print(depth_step); print(calculation_settings)

    return depth_step, calculation_settings


def build_grn_input(depth, calculation_settings):
    # build up psgrn input file in specified depth

    dir = TEMP_PREFIX + 'grn/' + str(depth)

    os.makedirs(dir, exist_ok=True)

    # override option will override any possible exist former file in temp/grn/
    # or the function will skip writing if there is any file in target folder
    if (len(os.listdir(dir)) != 0):
        print(f'INFO: grn file for depth {depth} already exists, skipping...')
        return 0
    
    # compose grn input file
    with open(TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn', 'a') as grn_input, \
        open(CONFIG_PREFIX + 'model.dat', 'r') as model:
        grn_input.write(f'{depth} {calculation_settings[0][1]} \n')
        grn_input.write(f'{calculation_settings[1][0]} {calculation_settings[1][1]} {calculation_settings[1][2]} {calculation_settings[1][3]}\n')
        grn_input.write(f'{calculation_settings[2][0]} {calculation_settings[2][1]} {calculation_settings[2][2]}\n')
        grn_input.write(f'{calculation_settings[3][0]} {calculation_settings[3][1]}\n')
        grn_input.write(f'{calculation_settings[4][0]}\n')
        grn_input.write(f'{calculation_settings[5][0]}\n')
        grn_input.write(f"'{TEMP_PREFIX}grn/{depth}/'\n")
        grn_input.write("'uz' 'ur' 'ut'\n" \
                        "'szz' 'srr' 'stt' 'szr' 'srt' 'stz'\n" \
                        "'tr' 'tt' 'rot' 'gd' 'gr'\n")
        
        # append model info from model.dat
        for line in model:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            cleaned_line = ' '.join(stripped_line.split())
            grn_input.write(cleaned_line + '\n')

    if TEST: print(f'INFO: building psgrn input file for depth {depth}...')

    return dir


if TEST:
    depth_number = 1
    depth_step, calculation_settings = calculation_setting()
    depth_range = depth_minmax()
    depth_list = numpy.arange(depth_range[0], depth_range[1] + depth_step, depth_step)
    print(depth_list)
    build_grn_input(depth_number, calculation_settings, False)