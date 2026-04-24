"""PSCMP input-file generator.

Builds .cmp input files for the fomosto_pscmp2008a Fortran binary.
Each file encodes observation points, output options, and source fault
parameters so that PSCMP can compute Coulomb stress changes (ΔCFS).
"""

from src import constant, error, logger_all
from pyproj import Geod
from os import makedirs, listdir
import math

cmp_log = logger_all.setlogger('cmp_input')


def observation_array_on_fault(
    receiving_fault_array, target_depth, observation_max_interval
):
    """Generate equally spaced observation points along the receiving fault.

    Projects the fault reference point down-dip to the target depth, then
    walks points along strike at the given horizontal interval using WGS-84
    geodesic forward computations.  Output tuples are ordered (lat, lon) so
    that the Fortran PSCMP reader interprets them correctly when parsing the
    Python tuple syntax as a complex number literal ``(real, imag)`` →
    ``(lat, lon)``.

    Args:
        receiving_fault_array: List of strings parsed from one non-comment,
            non-blank line of receiving_fault.dat.  Expected indices:
            [1]=O_lat, [2]=O_lon, [3]=O_depth, [4]=length_km,
            [5]=width_km, [6]=strike_deg, [7]=dip_deg.
        target_depth: Depth in km at which to place the observation points.
        observation_max_interval: Maximum spacing in km between consecutive
            observation points along strike.

    Returns:
        list of (float, float): Observation points as (lat, lon) tuples,
        rounded to 4 decimal places.

    Raises:
        error.FunctionRunningError: If geodesic computation produces NaN
            (e.g. degenerate geometry).
        AssertionError: If the target depth lies above the fault origin or
            the down-dip projection walks off the bottom of the fault.
    """
    observation_points = []

    O_lon = float(receiving_fault_array[2])
    O_lat = float(receiving_fault_array[1])
    O_depth = float(receiving_fault_array[3])
    length = float(receiving_fault_array[4])
    width = float(receiving_fault_array[5])
    strike = float(receiving_fault_array[6])
    dip_angle = float(receiving_fault_array[7])

    cmp_log.debug(
        f'O_lon: {O_lon}, O_lat: {O_lat}, O_depth: {O_depth}, '
        f'length: {length}, width: {width}, strike: {strike}, '
        f'dip_angle: {dip_angle}'
    )

    geod = Geod(ellps="WGS84")

    depth_diff = target_depth - O_depth
    horizontal_offset = depth_diff / math.tan(math.radians(dip_angle))
    width_offset = depth_diff / math.sin(math.radians(dip_angle))

    if math.isnan(horizontal_offset):
        raise error.FunctionRunningError('observation_array_on_fault')
    if math.isnan(width_offset):
        raise error.FunctionRunningError('observation_array_on_fault')

    cmp_log.debug(
        f'depth_diff: {depth_diff}, horizontal_offset: {horizontal_offset}, '
        f'width_offset: {width_offset}'
    )

    assert depth_diff >= 0, 'depth_diff overwhelm'
    assert width_offset <= width, 'width_offset overwhelm'

    # Project the reference point down-dip to the target depth plane.
    proj_lon, proj_lat, _ = geod.fwd(
        O_lon, O_lat, (strike + 90) % 360, horizontal_offset * 1000
    )
    proj_lon, proj_lat = (round(proj_lon, 4), round(proj_lat, 4))

    if math.isnan(proj_lon) or math.isnan(proj_lat):
        raise error.FunctionRunningError('observation_array_on_fault')

    cmp_log.debug(f'proj_lon, proj_lat: {proj_lon}, {proj_lat}')

    # Walk equally spaced observation points along strike.
    num_points = int(length / observation_max_interval) + 1

    assert num_points > 2

    cmp_log.debug(f'num_points: {num_points}')

    for i in range(num_points):
        distance_along_strike = i * observation_max_interval
        point_lon, point_lat, _ = geod.fwd(
            proj_lon, proj_lat, strike, distance_along_strike * 1000
        )
        if math.isnan(point_lon) or math.isnan(point_lat):
            raise error.FunctionRunningError('observation_array_on_fault')
        point_lon, point_lat = (round(point_lon, 4), round(point_lat, 4))

        cmp_log.debug(
            f'distance_along_strike: {distance_along_strike}, '
            f'point_lon, point_lat: {point_lon} {point_lat}'
        )

        observation_points.append((point_lat, point_lon))

    cmp_log.debug(
        f'observation_points: {observation_points}'
    )

    return observation_points


def build_cmp_input(depth, observation_max_interval, configs):
    """Generate a PSCMP input (.cmp) file for a single observation depth.

    Reads receiving_fault.dat and source_fault.dat, computes observation
    points, and writes the complete PSCMP input deck.

    Args:
        depth: Observation depth in km.
        observation_max_interval: Spacing between observation points in km
            (passed from main.py as depth_step × 2).
        configs: List-of-lists from config.dat, parsed by settings.config().
            configs[0]: insar flag + optional LOS cosines.
            configs[1]: icmb flag + optional Coulomb parameters.
            configs[2]: snapshot count.
            configs[3:3+nsc]: per-snapshot time + filename.

    Raises:
        error.FunctionRunningError: If writing the .cmp file fails.
    """
    cmp_log.debug(
        f'input parameters: depth {depth}, '
        f'observation_max_interval: {observation_max_interval}, '
        f'configs: {configs}'
    )

    out_dir = constant.TEMP_PREFIX + 'cmp/' + str(depth)

    makedirs(out_dir, exist_ok=True)

    # Skip if PSCMP results already exist (no-override mode).
    if len(listdir(out_dir)) != 0:
        cmp_log.warning(
            f'cmp file for depth {depth} already exists, skipping...'
        )
        return 0

    # Build observation array from receiving fault geometry.
    observation_array = []
    with open(
        constant.CONFIG_PREFIX + 'receiving_fault.dat', 'r'
    ) as receiving_fault:
        for line in receiving_fault:
            stripped_line = line.strip()

            if not stripped_line or stripped_line.startswith('#'):
                continue
            split_line = stripped_line.split()

            try:
                observation_points = observation_array_on_fault(
                    split_line, depth, observation_max_interval
                )
                observation_array.extend(observation_points)

            except AssertionError as e:
                cmp_log.warning(
                    f'observation array walking out of receiving fault, '
                    f'reason: {e}, skip this point'
                )

    assert len(observation_array) > 0, 'observation_array empty'

    cmp_log.debug(
        f'observation_array: {observation_array}'
    )

    with open(
        constant.TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp', 'a'
    ) as cmp_input, open(
        constant.CONFIG_PREFIX + 'source_fault.dat', 'r'
    ) as source_fault:
        try:
            # Header: observation mode (2-D areal; ilonrec=0) and count.
            cmp_input.write('0\n')
            cmp_input.write(f'{len(observation_array)}\n')

            # Observation coordinates: 6 complex-number (lat, lon) tuples per
            # line, the Fortran list-directed read format.
            newline_count = 0
            for point in observation_array:
                newline_count += 1
                cmp_input.write(f'{point}')
                if newline_count == 6:
                    cmp_input.write('\n')
                else:
                    cmp_input.write(' ')

            # Output switches: InSAR and Coulomb.
            cmp_input.write(f'\n{configs[0][0]}\n')
            if configs[0][0] == '1':
                cmp_input.write(
                    f'{configs[0][0]} {configs[0][1]} '
                    f'{configs[0][2]} {configs[0][3]}\n'
                )
            cmp_input.write(f'{configs[1][0]}\n')
            if configs[1][0] == '1':
                cmp_input.write(
                    f'{configs[1][0]} {configs[1][1]} {configs[1][2]} '
                    f'{configs[1][3]} {configs[1][4]} {configs[1][5]} '
                    f'{configs[1][6]} {configs[1][7]} {configs[1][8]}\n'
                )

            # Output directory and file lists.
            cmp_input.write(f"'{constant.TEMP_PREFIX}cmp/{depth}/'\n")
            cmp_input.write('0 0 0\n')
            cmp_input.write("'ux.dat' 'uy.dat' 'uz.dat'\n")
            cmp_input.write('0 0 0 0 0 0\n')
            cmp_input.write(
                "'sxx.dat' 'syy.dat' 'szz.dat' "
                "'sxy.dat' 'syz.dat' 'szx.dat'\n"
            )
            cmp_input.write('0 0 0 0 0\n')
            cmp_input.write(
                "'tx.dat' 'ty.dat' 'rot.dat' 'gd.dat' 'gr.dat'\n"
            )

            # Snapshot time and filename.
            cmp_input.write(f'{configs[2][0]}\n')
            snapshot_count = 0
            nsc = int(configs[2][0])
            while snapshot_count < nsc:
                cmp_input.write(
                    f'{configs[3 + snapshot_count][0]} '
                    f'{configs[3 + snapshot_count][1]}\n'
                )
                snapshot_count += 1

            # Green's function directory and output file list.
            cmp_input.write(f"'{constant.TEMP_PREFIX}grn/{depth}/'\n")
            cmp_input.write(constant.GRN_OUTPUT_FILENAMES)

            # Append source fault parameters (skip comments).
            for line in source_fault:
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                cleaned_line = ' '.join(stripped_line.split())
                cmp_input.write(cleaned_line + '\n')

        except Exception:
            raise error.FunctionRunningError('build_cmp_input(write)')

    logger_all.logged_print(
        f'build pscmp input file for depth {depth}...', cmp_log
    )
