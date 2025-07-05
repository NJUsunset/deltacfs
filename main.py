import os
import shutil
from pyproj import Geod
import logging
import datetime
from src import constant, grn_input, cmp_input, logger_all

log = logger_all.setlogger()
log.info('setup all files in config folder before running this script.')
log.info('calculate.py running...')
ifgrn = logger_all.logged_input('Do you want to calculate green function set? (y/no-override/n): \n', log)
ifcmp = logger_all.logged_input('Do you want to calculate deltacfs? (y/no-override/n): \n', log)

depth_range = cmp_input.depth_minmax()
depth_step, calculation_settings = grn_input.calculation_setting()
configs = cmp_input.config()
observation_distance = depth_step / 5.0

depth_array = []
depth = depth_range[0]
while depth <= depth_range[1]:
    depth_array.append(depth)
    depth += depth_step

if ifgrn != 'n':
    log.info('grn_input.py running...')

    if ifgrn == 'y':
        log.info('Overriding existing green function set...')
        shutil.rmtree(constant.TEMP_PREFIX + 'grn/', ignore_errors=True)
        shutil.rmtree(constant.TEMP_PREFIX + 'grn_input/', ignore_errors=True)
    
    os.makedirs(constant.TEMP_PREFIX + 'grn_input/', exist_ok=True)
    for depth in depth_array:
        grn_input.build_grn_input(depth, calculation_settings)
        state = os.system('bash ./src/psgrn.sh ' + constant.TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn')
        if state != 0:
            log.error(f'psgrn.sh failed for depth {depth}.')
            os._exit(1)
        log.info(f'psgrn.sh finished for depth {depth}.')
        

if ifcmp != 'n':
    log.info('cmp_input.py running...')

    if ifcmp == 'y':
        log.info('Overriding existing deltacfs...')
        shutil.rmtree(constant.TEMP_PREFIX + 'cmp/', ignore_errors=True)
        shutil.rmtree(constant.TEMP_PREFIX + 'cmp_input/', ignore_errors=True)
    
    os.makedirs(constant.TEMP_PREFIX + 'cmp_input/', exist_ok=True)
    for depth in depth_array:
        grn_input.build_cmp_input(depth, observation_distance, configs)
        state = os.system('bash ./src/pscmp.sh ' + constant.TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp')
        if state != 0:
            log.error(f'pscmp.sh failed for depth {depth}.')
            os._exit(1)
        log.info(f'pscmp.sh finished for depth {depth}.')

log.info('main.py finished.')
