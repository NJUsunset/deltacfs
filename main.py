from src import constant, grn_input, cmp_input, logger_all, error, settings
from shutil import rmtree
import os

TEST = True

try:
    log = logger_all.initlogger(logger_all.Log_level.DEBUG if TEST else logger_all.Log_level.INFO)

except error.InputValueError as e:
    print('Bad input for initialising log system, please check code, program exiting')
    exit()


try:
    logger_all.logged_print('setup all files in config folder before running this script.', log)
    logger_all.logged_print('calculate.py running...', log)
    ifgrn = logger_all.logged_input('Do you want to calculate green function set? (y/no-override/n): \n', log)
    ifcmp = logger_all.logged_input('Do you want to calculate deltacfs? (y/no-override/n): \n', log)

except KeyboardInterrupt as e:
    log.warning(e)
    logger_all.logged_print('User keyboard interupt, program exiting...', log)
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(f'unforeseen error when processing log initialise, error info: {e}\nprogram exiting...', log)
    exit()


try:
    depth_range = settings.depth_minmax()
    depth_step, calculation_settings = settings.calculation_setting()
    configs = settings.config()
    observation_distance = depth_step / 5.0

    depth_array = []
    depth = depth_range[0]
    while depth <= depth_range[1]:
        depth_array.append(depth)
        depth += depth_step

except AssertionError as e:
    log.error(e)
    logger_all.logged_print(f'config.dat file value error with {e}, please check\nprogram exiting...', log)
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(f'unforeseen error occur when processing depth list calculation, error info: {e}\nprogram exiting...', log)
    exit()


try:
    if ifgrn != 'n':
        logger_all.logged_print('grn_input.py running...', log)

        if ifgrn == 'y':
            log.info('Overriding existing green function set...')
            rmtree(constant.TEMP_PREFIX + 'grn/', ignore_errors=True)
            rmtree(constant.TEMP_PREFIX + 'grn_input/', ignore_errors=True)
        
        os.makedirs(constant.TEMP_PREFIX + 'grn_input/', exist_ok=True)
        for depth in depth_array:
            grn_input.build_grn_input(depth, calculation_settings)
            logger_all.logged_run(['bash', './src/psgrn.sh', constant.TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn'], log)
            log.info(f'psgrn.sh finished for depth {depth}.')

except error.FunctionRunningError as e:
    log.error(e)
    logger_all.logged_print(e + ', please check\npropgram exiting...', log)
    exit()

except error.CommandRunningError as e:
    log.error(e)
    logger_all.logged_print(e + ', please check\nprogram exiting...', log)
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(f'unforeseen error when processing green function calculation, error info: {e}\nprogram exiting...', log)
    exit()


try:
    if ifcmp != 'n':
        logger_all.logged_print('cmp_input.py running...', log)

        if ifcmp == 'y':
            log.info('Overriding existing deltacfs...')
            rmtree(constant.TEMP_PREFIX + 'cmp/', ignore_errors=True)
            rmtree(constant.TEMP_PREFIX + 'cmp_input/', ignore_errors=True)
        
        os.makedirs(constant.TEMP_PREFIX + 'cmp_input/', exist_ok=True)
        for depth in depth_array:
            cmp_input.build_cmp_input(depth, observation_distance, configs)
            state = logger_all.logged_run(['bash', './src/pscmp.sh', constant.TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp'], log)
            log.info(f'pscmp.sh finished for depth {depth}.')

except AssertionError as e:
    log.warning(e)
    pass

except error.FunctionRunningError as e:
    log.error(e)
    logger_all.logged_print(e + ', please check\npropgram exiting...', log)
    exit()

except error.CommandRunningError as e:
    log.error(e)
    logger_all.logged_print(e + ', please check\nprogram exiting...', log)
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(f'unforeseen error when processing stress calculation, error infomation: {e}\nprogram exiting...', log)


logger_all.logged_print('main.py finished.', log)
