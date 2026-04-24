"""PSGRN input-file generator.

Builds .grn input files for the fomosto_psgrn2008a Fortran binary.
Each file encodes a layered earth model at a specific observation depth.
"""

from src import constant, error, logger_all
from os import makedirs, listdir

grn_log = logger_all.setlogger('grn_input')


def build_grn_input(depth, calculation_settings):
    """Generate a PSGRN input (.grn) file for a single observation depth.

    Args:
        depth: Observation depth in km below the surface.
        calculation_settings: List-of-lists read from
            calculation_setting.dat by settings.calculation_setting().

    Returns:
        str: Path to the output Green's-function subdirectory (temp/grn/<depth>/).

    Raises:
        error.FunctionRunningError: If writing the .grn file fails.
    """
    out_dir = constant.TEMP_PREFIX + 'grn/' + str(depth)

    makedirs(out_dir, exist_ok=True)

    # Skip if Green's-function results already exist for this depth
    # (no-override mode).  'y' mode clears the parent directory in main.py.
    if len(listdir(out_dir)) != 0:
        grn_log.warning(
            f'grn file for depth {depth} already exists, skipping...'
        )
        return out_dir

    with open(
        constant.TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn', 'a'
    ) as grn_input, open(constant.CONFIG_PREFIX + 'model.dat', 'r') as model:
        try:
            grn_input.write(f'{depth} {calculation_settings[0][1]}\n')
            grn_input.write(
                f'{calculation_settings[1][0]} {calculation_settings[1][1]} '
                f'{calculation_settings[1][2]} {calculation_settings[1][3]}\n'
            )
            grn_input.write(
                f'{calculation_settings[2][0]} {calculation_settings[2][1]} '
                f'{calculation_settings[2][2]}\n'
            )
            grn_input.write(
                f'{calculation_settings[3][0]} {calculation_settings[3][1]}\n'
            )
            grn_input.write(f'{calculation_settings[4][0]}\n')
            grn_input.write(f'{calculation_settings[5][0]}\n')
            grn_input.write(
                f"'{constant.TEMP_PREFIX}grn/{depth}/'\n"
            )
            grn_input.write(constant.GRN_OUTPUT_FILENAMES)

            for line in model:
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                cleaned_line = ' '.join(stripped_line.split())
                grn_input.write(cleaned_line + '\n')

        except Exception:
            raise error.FunctionRunningError('build_grn_input')

    logger_all.logged_print(
        f'build psgrn input file for depth {depth}...', grn_log
    )

    return out_dir
