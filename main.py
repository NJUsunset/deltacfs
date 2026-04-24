"""deltacfs — Coulomb stress change (ΔCFS) calculation pipeline.

Orchestrates a config-driven workflow that generates input files for the
PSGRN/PSCMP Fortran binaries, runs them across multiple observation depths,
and consolidates the per-depth results into human- and machine-readable
output formats.

Phases (each can be toggled via interactive prompt):
  1. Green's function computation (PSGRN)
  2. Coulomb stress computation (PSCMP)
  3. After-process: merge per-depth output + write GMT-compatible files
  4. Plot Coulomb stress cross-section (GMT)
  5. Clean generated files

Usage:
    python3 main.py          # interactive (y / no-override / n)
    ./src/run.sh             # convenience wrapper
"""

from src import (
    constant, grn_input, cmp_input, logger_all, error, settings, consolidate,
)
from src.plot_coulomb import plot_coulomb_section
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
# Interactive prompts — ask the user which phases to run
# ---------------------------------------------------------------------------
try:
    logger_all.logged_print(
        'Setup all files in config/ before running.', log
    )
    logger_all.logged_print(
        'Phases available:\n'
        '  1. Green\'s function computation   (PSGRN)\n'
        '  2. Coulomb stress computation      (PSCMP)\n'
        '  3. After-process                   (merge outputs)\n'
        '  4. Plot Coulomb cross-section      (GMT)\n'
        '  5. Clean generated files           (temp/ logs/ output/)\n',
        log,
    )

    ifgrn = logger_all.logged_input(
        'Run phase 1 — Green\'s function set? (y/no-override/n): \n',
        log,
    )
    ifcmp = logger_all.logged_input(
        'Run phase 2 — Coulomb stress ΔCFS? (y/no-override/n): \n',
        log,
    )
    ifap = logger_all.logged_input(
        'Run phase 3 — after-process? (y/no-override/n): \n',
        log,
    )
    ifplot = logger_all.logged_input(
        'Run phase 4 — plot Coulomb cross-section? (y/n): \n',
        log,
    )
    ifclean = logger_all.logged_input(
        'Run phase 5 — clean generated files? (y/n): \n',
        log,
    )

except KeyboardInterrupt as e:
    log.warning(e)
    logger_all.logged_print(
        'User keyboard interrupt, program exiting...', log
    )
    exit()

except Exception as e:
    log.error(e)
    logger_all.logged_print(
        f'Unforeseen error when processing log initialise, '
        f'error info: {e}\nprogram exiting...',
        log,
    )
    exit()


# ---------------------------------------------------------------------------
# Phase 5 — Clean (runs early if requested, skips later phases)
# ---------------------------------------------------------------------------
if ifclean == 'y':
    logger_all.logged_print('Cleaning generated files...', log)
    for d in (constant.TEMP_PREFIX, constant.LOG_PREFIX, constant.OUTPUT_PREFIX):
        rmtree(d, ignore_errors=True)
    logger_all.logged_print('Done.', log)
    # Don't exit — other phases may regenerate what they need.


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
        f'Unforeseen error when processing depth list calculation, '
        f'error info: {e}\nprogram exiting...',
        log,
    )
    exit()


# ---------------------------------------------------------------------------
# Phase 1 — Green's function (PSGRN)
# ---------------------------------------------------------------------------
if ifgrn != 'n':
    try:
        logger_all.logged_print(
            'Phase 1 — Green\'s function construct running...', log
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
                    constant.SRC_PREFIX + 'psgrn.sh',
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
            f'{e}, please check\nprogram exiting...', log
        )
        exit()

    except Exception as e:
        log.error(e)
        logger_all.logged_print(
            f'Unforeseen error in phase 1, '
            f'error info: {e}\nprogram exiting...',
            log,
        )
        exit()


# ---------------------------------------------------------------------------
# Phase 2 — Coulomb stress change (PSCMP)
# ---------------------------------------------------------------------------
if ifcmp != 'n':
    try:
        logger_all.logged_print(
            'Phase 2 — Coulomb stress calculation running...', log
        )

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
                        constant.SRC_PREFIX + 'pscmp.sh',
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

    except error.CommandRunningError as e:
        log.error(e)
        logger_all.logged_print(
            f'{e}, please check\nprogram exiting...', log
        )
        exit()

    except error.FunctionRunningError as e:
        log.error(e)
        logger_all.logged_print(
            f'{e}, please check\nprogram exiting...', log
        )
        exit()

    except Exception as e:
        log.error(e)
        logger_all.logged_print(
            f'Unforeseen error in phase 2, '
            f'error info: {e}\nprogram exiting...',
            log,
        )
        exit()


# ---------------------------------------------------------------------------
# Phase 3 — After-process (combine + consolidate)
# ---------------------------------------------------------------------------
if ifap != 'n':
    try:
        logger_all.logged_print('Phase 3 — afterprocess running...', log)

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
            log.debug(f'Read file list: {filelist}')

            if ifap == 'y':
                log.info('Overriding existing output files...')
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
                f'After-process for {filelist} finished.', log
            )

            consolidate.consolidate_cmp_results()
            logger_all.logged_print(
                'Consolidate all depth results finished.', log
            )

    except Exception as e:
        log.error(e)
        logger_all.logged_print(
            f'Unforeseen error in phase 3, error info: {e}\n'
            'program exiting',
            log,
        )
        exit()


# ---------------------------------------------------------------------------
# Phase 4 — Plot Coulomb cross-section (GMT)
# ---------------------------------------------------------------------------
if ifplot == 'y':
    try:
        logger_all.logged_print(
            'Phase 4 — Plotting Coulomb cross-section...', log
        )
        plot_coulomb_section()
        logger_all.logged_print('Plot finished.', log)

    except FileNotFoundError as e:
        log.error(e)
        logger_all.logged_print(
            f'{e} — run phases 2 and 3 first.\n'
            'Skipping plot.',
            log,
        )

    except Exception as e:
        log.error(e)
        logger_all.logged_print(
            f'Unforeseen error in phase 4, error info: {e}\n'
            'Skipping plot.',
            log,
        )


logger_all.logged_print('main.py finished.', log)
