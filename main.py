from src import constant, errors, grn_input, cmp_input, logger_all, settings
from shutil import rmtree
import logging
from os import makedirs, listdir

TEST = True
def main() -> None:
    # initialise log
    log = logger_all.initlogger(logging.DEBUG if TEST else logging.INFO)
    fortran_log = logger_all.setlogger('fortran_run')


    # ask user to save data and make clean
    logger_all.logged_print('setup all files in config folder before running this script.', log)
    logger_all.logged_print('calculate.py running...', log)
    run = logger_all.logged_input('The program will erase all file in output adn temp folder\n \
                                    all privious data will be loss, please save them before further action\n \
                                    type Confirm below to make further run, \
                                    ALL option will additionally clean log file: (Confirm/ALL/exit)\n', log, ['Confirm', 'ALL', 'exit'])
    if run == 'exit':
        logger_all.logged_print('accept input to exit program, program stopping...', log)
        exit()
    elif run == 'Confirm':
        logger_all.logged_print('accept confirmation, program cleaning...', log)
        log.info('cleaning existing green function set...')
        rmtree(constant.TEMP_PREFIX + 'grn/', ignore_errors=True)
        rmtree(constant.TEMP_PREFIX + 'grn_input/', ignore_errors=True)
        log.info('cleaning existing deltacfs...')
        rmtree(constant.TEMP_PREFIX + 'cmp/', ignore_errors=True)
        rmtree(constant.TEMP_PREFIX + 'cmp_input/', ignore_errors=True)
        log.info('cleaning existing output file...')
        rmtree(constant.OUTPUT_PREFIX, ignore_errors=True)
        log.info('clean process finished')
    elif run == 'ALL':
        logger_all.logged_print('accept all clean confirmation, program cleaning...', log)
        log.info('cleaning existing green function set...')
        rmtree(constant.TEMP_PREFIX + 'grn/', ignore_errors=True)
        rmtree(constant.TEMP_PREFIX + 'grn_input/', ignore_errors=True)
        log.info('cleaning existing deltacfs...')
        rmtree(constant.TEMP_PREFIX + 'cmp/', ignore_errors=True)
        rmtree(constant.TEMP_PREFIX + 'cmp_input/', ignore_errors=True)
        log.info('cleaning existing output file...')
        rmtree(constant.OUTPUT_PREFIX, ignore_errors=True)
        log.info('cleaning existing log file...')
        rmtree(constant.LOG_PREFIX, ignore_errors=True)
        log.info('clean process finished')
    else:
        raise ValueError


    try:
        # calculate depth list
        depth_range = settings.depth_minmax()
        depth_step, calculation_settings = settings.calculation_setting()
        configs = settings.config()
        observation_max_interval = depth_step

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
            logger_all.logged_print('green function construct running...', log)

            if ifgrn == 'y':
                
            
            makedirs(constant.TEMP_PREFIX + 'grn_input/', exist_ok=True)
            for depth in depth_array:
                grn_input.build_grn_input(depth, calculation_settings)
                logger_all.logged_run(['bash', './src/psgrn.sh', constant.TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn'], fortran_log)
                log.info(f'psgrn.sh finished for depth {depth}.')


    except errors.CommandRunningError as e:
        log.error(e)
        logger_all.logged_print(f'{e}, please check\nprogram exiting...', log)
        exit()

    except errors.FunctionRunningError as e:
        log.error(e)
        logger_all.logged_print(f'{e}, please check\npropgram exiting...', log)
        exit()

    except Exception as e:
        log.error(e)
        logger_all.logged_print(f'unforeseen error when processing green function calculation, error info: {e}\nprogram exiting...', log)
        exit()


    try:
        if ifcmp != 'n':
            logger_all.logged_print('stress calculation running...', log)

            if ifcmp == 'y':
                log.info('Overriding existing deltacfs...')

            
            makedirs(constant.TEMP_PREFIX + 'cmp_input/', exist_ok=True)
            for depth in depth_array:
                try:
                    cmp_input.build_cmp_input(depth, observation_max_interval, configs)
                    state = logger_all.logged_run(['bash', './src/pscmp.sh', constant.TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp'], fortran_log)
                    log.info(f'pscmp.sh finished for depth {depth}.')
                
                except AssertionError as e:
                    log.warning(e)
                    pass

    except errors.CommandRunningError as e:
        log.error(e)
        logger_all.logged_print(f'{e}, please check\nprogram exiting...', log)
        exit()

    except errors.FunctionRunningError as e:
        log.error(e)
        logger_all.logged_print(f'{e}, please check\npropgram exiting...', log)
        exit()

    except Exception as e:
        log.error(e)
        logger_all.logged_print(f'unforeseen error when processing stress calculation, error infomation: {e}\nprogram exiting...', log)
        exit()


    try:
        if ifap != 'n':
            logger_all.logged_print('afterprocess running...', log)
            filelist = listdir(constant.TEMP_PREFIX + 'cmp/' + str(depth_array[0]))
            log.debug(f'readed file list: {filelist}')

            if ifap == 'y':


            makedirs(constant.OUTPUT_PREFIX, exist_ok=True)

            for filename in filelist:
                for depth in depth_array:
                    try:
                        settings.combine_file(filename, depth)
                    except AssertionError as e:
                        log.warning(e)
                        continue
            
                log.info(f'{filename} write finished')
            logger_all(f'afterprocess for filelist {filelist} finished.')

    except Exception as e:
        log.error(e)
        logger_all.logged_print(f'unforeseen error at afterprocess, error information: {e}\nprogram exiting', log)
        exit()


    logger_all.logged_print('main.py finished.', log)
