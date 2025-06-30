import numpy
import pandas
import math
import os
import shutil
from pyproj import Geod

CONFIG_PREFIX = './config/'
TEMP_PREFIX = './temp/'
SRC_PREFIX = './src/'
OUTPUT_PREFIX = './output/'

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
        
    return dir


def observation_array_on_fault(receiving_fault_array, target_depth, observation_distance):
    # Generate points along the fault plane at a specified depth with a given horizontal spacing.
    
    observation_points = []

    O_lon = float(receiving_fault_array[1])
    O_lat = float(receiving_fault_array[2])
    O_depth = float(receiving_fault_array[3])
    length = float(receiving_fault_array[4])
    width = float(receiving_fault_array[5])
    strike = float(receiving_fault_array[6])
    dip_angle = float(receiving_fault_array[7])

    geod = Geod(ellps="WGS84")

    depth_diff = target_depth - O_depth
    horizontal_offset = depth_diff / math.tan(math.radians(dip_angle))
    width_offset = depth_diff / math.sin(math.radians(dip_angle))
    
    if (depth_diff < 0) or (width_offset > width):
        return observation_points

    # Determine the starting point's projection at the target depth
    dip_direction = (strike + 90) % 360
    proj_lon, proj_lat, _ = geod.fwd(O_lon, O_lat, dip_direction, horizontal_offset * 1000)

    # Generate points along the fault's strike direction
    num_points = int(length / observation_distance) + 1

    for i in range(num_points):
        distance_along_strike = i * observation_distance
        point_lon, point_lat, _ = geod.fwd(proj_lon, proj_lat, strike, distance_along_strike * 1000)
        observation_points.append((point_lon, point_lat))

    return observation_points


def config():
    # read config.dat file and return a list with info
    configs = []

    with open(CONFIG_PREFIX + 'config.dat', 'r') as calculation_setting:
        for line in calculation_setting:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            configs.append(values)

    return configs

def build_cmp_input(depth, observation_distance, configs):
    # build up pscmp input file

    dir = TEMP_PREFIX + 'cmp/' + str(depth)

    os.makedirs(dir, exist_ok=True)

    # override option will override any possible exist former file in temp/cmp/
    # or the function will skip writing if there is any file in target folder
    if (len(os.listdir(dir)) != 0):
        print(f'INFO: cmp file for depth {depth} already exists, skipping...')
        return 0
    
    # calculate observation array
    observation_array = []
    with open(CONFIG_PREFIX + 'receiving_fault.dat', 'r') as receiving_fault:
        for line in receiving_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            split_line = stripped_line.split()
            observation_points = observation_array_on_fault(split_line, depth, observation_distance)
            for point in observation_points:
                observation_array.append(observation_points)

    with open(TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp', 'a') as cmp_input, \
        open(CONFIG_PREFIX + 'source_fault.dat', 'r') as source_fault:
        cmp_input.write('0\n')
        cmp_input.write(f'{len(observation_array)}\n')

        newline_count = 0
        for point in observation_array:
            newline_count += 1
            cmp_input.write(f'({point[0]}, {point[1]}) ')
            if (newline_count == 6): cmp_input.write('\n')
        
        cmp_input.write(f'{configs[0][0]}\n')
        if (configs[0][0] == 1): cmp_input.write(f'{configs[0][0]} {configs[0][1]} {configs[0][2]} {configs[0][3]}\n')
        cmp_input.write(f'{configs[1][0]}\n')
        if (configs[1][0] == 1): 
            cmp_input.write(f'{configs[1][0]} {configs[1][1]} {configs[1][2]} ')
            cmp_input.write(f'{configs[1][3]} {configs[1][4]} {configs[1][5]} ')
            cmp_input.write(f'{configs[1][6]} {configs[1][7]} {configs[1][8]}\n')
        
        cmp_input.write(f"'{TEMP_PREFIX}cmp/{depth}/'\n")
        cmp_input.write('0 0 0\n')
        cmp_input.write("'ux.dat' 'uy.dat' 'uz.dat'\n")
        cmp_input.write('0 0 0 0 0 0\n')
        cmp_input.write("'sxx.dat' 'syy.dat' 'szz.dat' 'sxy.dat' 'syz.dat' 'szx.dat'\n")
        cmp_input.write('0 0 0 0 0\n')
        cmp_input.write("'tx.dat' 'ty.dat' 'rot.dat' 'gd.dat' 'gr.dat'\n")
        cmp_input.write(f'{configs[2][0]}\n')

        snapshot_count = 0
        while (snapshot_count < int(configs[2][0])):
            cmp_input.write(f'{configs[3 + snapshot_count][0]} {configs[3 + snapshot_count][1]}\n')
            snapshot_count += 1
        
        cmp_input.write(f"'{TEMP_PREFIX}grn/{depth}/'\n")
        cmp_input.write("'uz' 'ur' 'ut'\n")
        cmp_input.write("'szz' 'srr' 'stt' 'szr' 'srt' 'stz'\n")
        cmp_input.write("'tr' 'tt' 'rot' 'gd' 'gr'\n")

        for line in source_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            cleaned_line = ' '.join(stripped_line.split())
            cmp_input.write(cleaned_line + '\n')


if __name__ == '__main__':
    print('INFO: setup all files in config folder before running this script.')
    print('INFO: calculate.py running...')
    ifgrn = input('INFO: Do you want to calculate green function set? (y/no-override/n): ')

    if ifgrn !='n' and ifgrn != 'no-override' and ifgrn != 'y':
        print('ERROR: Bad input')
        os._exit(0)

    ifcmp = input('INFO: Do you want to calculate deltacfs? (y/no-override/n): ')

    if ifcmp != 'y' and ifcmp != 'no-override' and ifcmp != 'n':
        print('ERROR: Bad input')
        os._exit(1)

    depth_range = depth_minmax()
    depth_step, calculation_settings = calculation_setting()
    configs = config()
    observation_distance = depth_step

    depth_array = []
    depth = depth_range[0]
    while depth <= depth_range[1]:
        depth_array.append(depth)
        depth += depth_step

    if ifgrn != 'n':
        print('INFO: grn_input.py running...')

        if ifgrn == 'y':
            print('INFO: Overriding existing green function set...')
            shutil.rmtree(TEMP_PREFIX + 'grn/', ignore_errors=True)
            shutil.rmtree(TEMP_PREFIX + 'grn_input/', ignore_errors=True)
        
        os.makedirs(TEMP_PREFIX + 'grn_input/', exist_ok=True)
        for depth in depth_array:
            build_grn_input(depth, calculation_settings)
            state = os.system('sh ./src/psgrn.sh ' + TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn')
            if state != 0:
                print(f'ERROR: psgrn.sh failed for depth {depth}.')
                os._exit(1)
            print(f'INFO: psgrn.sh finished for depth {depth}.')
            

    if ifcmp != 'n':
        print('INFO: cmp_input.py running...')

        if ifcmp == 'y':
            print('INFO: Overriding existing deltacfs...')
            shutil.rmtree(TEMP_PREFIX + 'cmp/', ignore_errors=True)
            shutil.rmtree(TEMP_PREFIX + 'cmp_input/', ignore_errors=True)
        
        os.makedirs(TEMP_PREFIX + 'cmp_input/', exist_ok=True)
        for depth in depth_array:
            build_cmp_input(depth, observation_distance, configs)
            state = os.system('sh ./src/pscmp.sh ' + TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp')
            if state != 0:
                print(f'ERROR: pscmp.sh failed for depth {depth}.')
                os._exit(1)
            print(f'INFO: pscmp.sh finished for depth {depth}.')
    
    print('INFO: calculate.py finished.')