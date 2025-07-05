import os
import shutil
from pyproj import Geod

from src.constant import *
from src.grn_input import *
from src.cmp_input import *


if __name__ == '__main__':
    # os.makedirs(LOG_PREFIX, exist_ok=True)
    print('INFO: setup all files in config folder before running this script.')
    print('INFO: calculate.py running...')
    ifgrn = input('INFO: Do you want to calculate green function set? (y/no-override/n): \n')

    if ifgrn !='n' and ifgrn != 'no-override' and ifgrn != 'y':
        print('ERROR: Bad input')
        os._exit(0)

    ifcmp = input('INFO: Do you want to calculate deltacfs? (y/no-override/n): \n')

    if ifcmp != 'y' and ifcmp != 'no-override' and ifcmp != 'n':
        print('ERROR: Bad input')
        os._exit(1)

    depth_range = depth_minmax()
    depth_step, calculation_settings = calculation_setting()
    configs = config()
    observation_distance = depth_step / 5.0

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
            state = os.system('bash ./src/psgrn.sh ' + TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn')
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
            state = os.system('bash ./src/pscmp.sh ' + TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp')
            if state != 0:
                print(f'ERROR: pscmp.sh failed for depth {depth}.')
                os._exit(1)
            print(f'INFO: pscmp.sh finished for depth {depth}.')
    
    print('INFO: Calculate.py finished.')
