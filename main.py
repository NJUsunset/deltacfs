"""deltacfs — Coulomb stress change (ΔCFS) calculation pipeline.

Orchestrates a config-driven workflow that generates input files for the
PSGRN/PSCMP Fortran binaries, runs them across multiple observation depths,
and consolidates the per-depth results into human- and machine-readable
output formats.

Phases (each can be toggled via interactive prompt):
  1. Green's function computation (PSGRN)
  2. Coulomb stress computation (PSCMP)
  3. After-process: merge per-depth output + write GMT-compatible files

Usage:
    python3 main.py          # interactive (y / no-override / n)
    python3 main.py --help   # not yet supported

For a non-interactive wrapper, use:  ./src/run.sh
"""

from src import (
    constant, grn_input, cmp_input, logger_all, error, settings, consolidate,
)
from shutil import rmtree
import os

TEST = True


def _build_depth_array(depth_range, depth_step):
    """Return a list of observation depths from min to max inclusive.

    Depth values are integer multiples of depth_step.  The upper bound is
    ceil'd by the receiving fault's down-dip extent (see
    settings.depth_minmax).
    """
    depth_array = []
    depth = depth_range[0]
    while depth <= depth_range[1]:
        depth_array.append(depth)
        depth += depth_step
    return depth_array


# ---------------------------------------------------------------------------
# Initialise logging
# ---------------------------------------------------------------------------
try:
    log = logger_all.initlogger(
        logger_all.Log_level.DEBUG if TEST else logger_all.Log_level.INFO
    )
    fortran_log = logger_all.setlogger('fortran_run')

except error.InputValueError as e:
    print(
        'Bad input for initialising log system, please check code, '
        'program exiting'
    )
    exit()


# ---------------------------------------------------------------------------
# Interactive mode prompts
# ---------------------------------------------------------------------------
try:
    logger_all.logged_print(
        'setup all files in config folder before running this script.', log
    )
    logger_all.logged_print('calculate.py running...', log)
    ifgrn = logger_all.logged_input(
        'Do you want to calculate green function set? '
        '(y/no-override/n): \n',
        log,
    )
    ifcmp = logger_all.logged_input(
        'Do you want to calculate deltacfs? (y/no-override/n): \n', log
    )
    ifap = logger_all.logged_input(
        'Do you want to make after process?(y/no-override/n)\n', log
    )

except KeyboardInterrupt as e:
    log.warning(e)
    logger_all.logged_print(
        'User keyboard interupt, program exiting...', log
    )
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(
        f'unforeseen error when processing log initialise, error info: {e}\n'
        'program exiting...',
        log,
    )
    exit()


# ---------------------------------------------------------------------------
# Read config and build depth array
# ---------------------------------------------------------------------------
try:
    depth_range = settings.depth_minmax()
    depth_step, calculation_settings = settings.calculation_setting()
    configs = settings.config()

    # Observation point spacing along strike (km).
    # Uses 2× depth_step so that the horizontal sample spacing is
    # roughly double the vertical one for a reasonably balanced grid.
    observation_distance = depth_step * 2.0

    depth_array = _build_depth_array(depth_range, depth_step)

except AssertionError as e:
    log.error(e)
    logger_all.logged_print(
        f'config.dat file value error with {e}, please check\n'
        'program exiting...',
        log,
    )
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(
        f'unforeseen error occur when processing depth list calculation, '
        f'error info: {e}\nprogram exiting...',
        log,
    )
    exit()


# ---------------------------------------------------------------------------
# Phase 1 — Green's function (PSGRN)
# ---------------------------------------------------------------------------
try:
    if ifgrn != 'n':
        logger_all.logged_print(
            'green function construct running...', log
        )

        if ifgrn == 'y':
            log.info('Overriding existing green function set...')
            rmtree(constant.TEMP_PREFIX + 'grn/', ignore_errors=True)
            rmtree(constant.TEMP_PREFIX + 'grn_input/', ignore_errors=True)

        os.makedirs(constant.TEMP_PREFIX + 'grn_input/', exist_ok=True)
        for depth in depth_array:
            grn_input.build_grn_input(depth, calculation_settings)
            logger_all.logged_run(
                [
                    'bash',
                    './src/psgrn.sh',
                    constant.TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn',
                ],
                fortran_log,
            )
            log.info(f'psgrn.sh finished for depth {depth}.')

except error.CommandRunningError as e:
    log.error(e)
    logger_all.logged_print(
        f'{e}, please check\nprogram exiting...', log
    )
    exit()

except error.FunctionRunningError as e:
    log.error(e)
    logger_all.logged_print(
        f'{e}, please check\npropgram exiting...', log
    )
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(
        f'unforeseen error when processing green function calculation, '
        f'error info: {e}\nprogram exiting...',
        log,
    )
    exit()


# ---------------------------------------------------------------------------
# Phase 2 — Coulomb stress change (PSCMP)
# ---------------------------------------------------------------------------
try:
    if ifcmp != 'n':
        logger_all.logged_print('stress calculation running...', log)

        if ifcmp == 'y':
            log.info('Overriding existing deltacfs...')
            rmtree(constant.TEMP_PREFIX + 'cmp/', ignore_errors=True)
            rmtree(constant.TEMP_PREFIX + 'cmp_input/', ignore_errors=True)

        os.makedirs(constant.TEMP_PREFIX + 'cmp_input/', exist_ok=True)
        for depth in depth_array:
            try:
                cmp_input.build_cmp_input(
                    depth, observation_distance, configs
                )
                logger_all.logged_run(
                    [
                        'bash',
                        './src/pscmp.sh',
                        constant.TEMP_PREFIX
                        + 'cmp_input/'
                        + str(depth)
                        + '.cmp',
                    ],
                    fortran_log,
                )
                log.info(f'pscmp.sh finished for depth {depth}.')

            except AssertionError as e:
                log.warning(e)
                pass

except error.CommandRunningError as e:
    log.error(e)
    logger_all.logged_print(
        f'{e}, please check\nprogram exiting...', log
    )
    exit()

except error.FunctionRunningError as e:
    log.error(e)
    logger_all.logged_print(
        f'{e}, please check\npropgram exiting...', log
    )
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(
        f'unforeseen error when processing stress calculation, '
        f'error infomation: {e}\nprogram exiting...',
        log,
    )
    exit()


# ---------------------------------------------------------------------------
# Phase 3 — After-process (combine + consolidate)
# ---------------------------------------------------------------------------
try:
    if ifap != 'n':
        logger_all.logged_print('afterprocess running...', log)

        first_cmp_dir = (
            constant.TEMP_PREFIX + 'cmp/' + str(depth_array[0])
        )
        if not os.path.isdir(first_cmp_dir):
            log.error(
                f'No PSCMP output directory at {first_cmp_dir} — '
                'run phase 2 first.'
            )
        else:
            filelist = os.listdir(first_cmp_dir)
            log.debug(f'readed file list: {filelist}')

            if ifap == 'y':
                log.info('Overriding existing outputfile...')
                rmtree(constant.OUTPUT_PREFIX, ignore_errors=True)

            os.makedirs(constant.OUTPUT_PREFIX, exist_ok=True)

            for filename in filelist:
                for depth in depth_array:
                    try:
                        settings.combine_file(filename, depth)
                    except AssertionError as e:
                        log.warning(e)
                        continue

                log.info(f'{filename} write finished')

            logger_all.logged_print(
                f'afterprocess for filelist {filelist} finished.', log
            )

            consolidate.consolidate_cmp_results()
            logger_all.logged_print(
                'consolidate all depth results finished.', log
            )

except Exception as e:
    log.error(e)
    logger_all.logged_print(
        f'unforeseen error at afterprocess, error information: {e}\n'
        'program exiting',
        log,
    )
    exit()


logger_all.logged_print('main.py finished.', log)
