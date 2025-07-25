from src import constant, errors, grn_input, cmp_input, logger_all, settings
import logging
from os import makedirs, listdir

TEST = True
def main() -> None:
    # initialise log
    log = logger_all.initlogger(logging.DEBUG if TEST else logging.INFO)
    fortran_log = logger_all.setlogger('fortran_run')

    logger_all.logged_print('setup all files in config folder before running this script.', log)
    logger_all.logged_print('calculate.py running...', log)

    settings.interact_and_clean(log)


    calculation_settings = settings.read_settings('calculation_setting', settings.calculation_setting_assertion)
    configs = settings.read_settings('config', settings.config_assertion)

    settings.prepare_observe_points()


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
