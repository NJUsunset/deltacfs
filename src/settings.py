"""Configuration file readers for the deltacfs pipeline.

Parses the four config/*.dat files and returns structured values consumed
by main.py, grn_input.py, and cmp_input.py.
"""

from src import constant, logger_all
from os.path import exists
import math

settings_log = logger_all.setlogger('settings')


def depth_minmax():
    """Compute the min and max observation depths from receiving fault geometry.

    The max depth accounts for the down-dip extent of each fault segment:
        bottom_depth = O_depth + width * sin(dip).

    Returns:
        list[int]: [depth_min, depth_max] in km, floor/ceil'd to integers.

    Raises:
        AssertionError: If depth_min < 0 or depth_max <= depth_min.
    """
    depth = []
    depth_stretch = []

    with open(
        constant.CONFIG_PREFIX + 'receiving_fault.dat', 'r'
    ) as receiving_fault:
        for line in receiving_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            split_line = stripped_line.split()
            depth.append(float(split_line[3]))
            depth_stretch.append(
                float(split_line[3])
                + float(split_line[5])
                * math.sin(math.radians(float(split_line[7])))
            )

    settings_log.debug(
        f'O_depth {depth}, dip {depth_stretch}'
    )

    depth_min = math.floor(min(min(depth), min(depth_stretch)))
    depth_max = math.ceil(max(max(depth), max(depth_stretch)))
    depth_range = [depth_min, depth_max]

    assert depth_min >= 0, 'depth_min'
    assert depth_max > depth_min, 'depth_range'

    settings_log.debug(
        f'depth_stretch {depth_stretch}, depth_range {depth_range}'
    )

    return depth_range


def calculation_setting():
    """Read calculation_setting.dat and return the depth step + raw rows.

    Returns:
        tuple[float, list[list[str]]]:
            depth_step (km) and the list of all non-comment data rows,
            each split into a list of strings.
    """
    calculation_settings = []

    with open(
        constant.CONFIG_PREFIX + 'calculation_setting.dat', 'r'
    ) as fh:
        for line in fh:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            calculation_settings.append(values)

    depth_step = float(calculation_settings[0][0])

    assert depth_step > 0, 'depth_step'

    settings_log.debug(
        f'depth_step {depth_step}, calculation_settings {calculation_settings}'
    )

    return depth_step, calculation_settings


def config():
    """Read config.dat and return a list of parameter rows.

    Performs validation on the InSAR flag, LOS cosines (if present), the
    Coulomb flag, friction coefficient, and prestress angles.

    Returns:
        list[list[str]]: All non-comment data rows from config.dat.

    Raises:
        AssertionError: If any validated value is out of its allowed range.
    """
    configs = []

    with open(constant.CONFIG_PREFIX + 'config.dat', 'r') as fh:
        for line in fh:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            configs.append(values)

    settings_log.debug(f'config.dat read result: {configs}')

    # Validate InSAR switch.
    assert constant.TOF.contains(int(configs[0][0])), 'insar(1/0)'
    if len(configs[0]) > 1:
        assert constant.COS.contains(float(configs[0][1])), (
            'insar cosine value'
        )
        assert constant.COS.contains(float(configs[0][2])), (
            'insar cosine value'
        )
        assert constant.COS.contains(float(configs[0][3])), (
            'insar cosine value'
        )

    # Validate Coulomb switch and prestress parameters.
    assert constant.TOF.contains(int(configs[1][0])), 'icmb'
    if len(configs[1]) > 1:
        assert float(configs[1][1]) > 0, 'friction factor'
        assert constant.ANGLE1.contains(float(configs[1][3])), 'strike'
        assert constant.ANGLE2.contains(float(configs[1][4])), 'dip'
        assert constant.ANGLE3.contains(float(configs[1][5])), 'slip'

    settings_log.debug(f'configs: {configs}')

    return configs


def combine_file(filename, depth):
    """Append depth-tagged data from one snapshot file into the output file.

    Reads temp/cmp/<depth>/<filename> and writes each data line prefixed
    with the depth value to output/<filename>.  The header line from the
    first depth level is also written (prefixed with 'depth[km] ').

    Args:
        filename: Snapshot output filename (e.g. 'snapshot_coseism.dat').
        depth: Depth in km for the current observation level.

    Raises:
        AssertionError: If the source snapshot file does not exist.
    """
    source_path = (
        constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename
    )
    settings_log.debug(f'will operate file {source_path}')

    assert exists(source_path), f'empty output file in {depth}'

    with open(source_path, 'r') as read_file, open(
        constant.OUTPUT_PREFIX + filename, 'a'
    ) as write_file:

        with open(constant.OUTPUT_PREFIX + filename, 'r') as temp_file:
            if temp_file.read() == '':
                settings_log.debug(
                    f'{filename} is found empty when processing depth '
                    f'{depth}, preparing to write title in it'
                )
                write_file.write('depth[km] ')
                write_file.write(read_file.readline())

        # Skip the first two data lines (Fortran table header rows), then
        # write each remaining line prefixed with the depth value.
        for i, line in enumerate(read_file):
            if i <= 2:
                continue

            stripped_line = line.strip()
            cleaned_line = ' '.join(stripped_line.split())
            write_file.write(str(depth) + ' ')
            write_file.write(cleaned_line + '\n')

    settings_log.debug(
        f'successfully rewrite file {filename} at depth {depth} to output file'
    )
