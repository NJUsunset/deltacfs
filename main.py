from src import constant, errors, input, logger_all, settings
import logging
from os import makedirs, listdir

TEST = False
def main() -> None:
    # initialise log
    log = logger_all.initlogger(logging.DEBUG if TEST else logging.INFO)
    fortran_log = logger_all.setlogger('fortran_run')

    logger_all.logged_print('setup all files in config folder before running this script.', log)
    logger_all.logged_print('calculate.py running...', log)

    settings.interact_and_clean(log)

    # read settings from config/
    calculation_settings = settings.read_settings('calculation_setting.dat', settings.calculation_setting_assertion)
    configs = settings.read_settings('config.dat', settings.config_assertion)
    receive_fault_list = settings.read_settings('receive_fault.dat')

    observe_max_interval = float(calculation_settings[0][0])

    # make temp dir
    makedirs(constant.TEMP_PREFIX + 'grn_input/', exist_ok=True)
    makedirs(constant.TEMP_PREFIX + 'cmp_input/', exist_ok=True)

    # calculate green func and stress for each depth
    depth_list_all: list[float] = []
    
    i = 0
    while i < len(receive_fault_list):
        depth_list, vertices, observe_points= settings.prepare_observe_points(receive_fault_list[i], observe_max_interval)
        depth_list_all += depth_list

        for depth in depth_list:
            input.build_grn_input(depth, calculation_settings)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
            input.build_cmp_input(depth, observe_points, configs)

        i = i + 1
    
    logger_all.logged_print(f'grn and cmp file build finish.', log)
    
    depth_list_set: list[float] = list(set(depth_list_all))
            
    for depth in depth_list_set:
        state = logger_all.logged_run(['bash', './src/psgrn.sh', constant.TEMP_PREFIX + 'grn_input/' + settings.depth_name(depth) + '.grn'],
                                        fortran_log)
        log.info(f'psgrn.sh finished for depth {depth}')
        state = logger_all.logged_run(['bash', './src/pscmp.sh', constant.TEMP_PREFIX + 'cmp_input/' + settings.depth_name(depth) + '.cmp'],
                                        fortran_log)
        log.info(f'pscmp.sh finished for depth {depth}.')
    
    logger_all.logged_print(f'psgrn/pscmp calculation finished.', log)

    # combine result into a single file
    logger_all.logged_print('afterprocess running...', log)
    filelist = listdir(constant.TEMP_PREFIX + 'cmp/' + settings.depth_name(depth_list_all[0]))
    log.debug(f'readed file list: {filelist}')

    makedirs(constant.OUTPUT_PREFIX, exist_ok=True)

    for filename in filelist:
        for depth in depth_list_all:
            try:
                settings.combine_file(filename, depth)
            except AssertionError as e:
                log.warning(e)
                continue
    
        log.info(f'{filename} write finished')
    logger_all.logged_print(f'afterprocess for filelist {filelist} finished.', log)


    logger_all.logged_print('main.py finished.', log)


main()