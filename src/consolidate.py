"""Post-processing: merge per-depth PSCMP results into output files.

After the PSCMP phase completes, snapshot_coseism.dat files exist under
temp/cmp/{depth}/.  This module combines them into two output formats:
  - output/consolidated.dat  — human-readable, Depth[km] column inserted
  - output/gmt_coulomb.xyz   — machine-readable XYZ for GMT / plotting
"""

from src import constant, logger_all
from os import listdir, makedirs
from os.path import isdir, join, exists

consolidate_log = logger_all.setlogger('consolidate')


def consolidate_cmp_results():
    """Merge snapshot_coseism.dat across depths into consolidated.dat.

    Reads the header from the first depth's snapshot to determine column
    boundaries, then inserts a Depth[km] column between Lon[deg] and Ux
    for every data row.  The Fortran fixed-width formatting is preserved.

    After writing consolidated.dat, also writes the GMT-compatible XYZ
    output (see write_gmt_coulomb_output).
    """
    cmp_root = join(constant.TEMP_PREFIX, 'cmp')

    depth_dirs = []
    for entry in listdir(cmp_root):
        full_path = join(cmp_root, entry)
        if isdir(full_path):
            try:
                depth_val = float(entry)
                depth_dirs.append((depth_val, full_path))
            except ValueError:
                consolidate_log.warning(
                    f'skipping non-numeric directory: {entry}'
                )

    depth_dirs.sort(key=lambda x: x[0])

    if not depth_dirs:
        consolidate_log.warning(
            'no depth directories found under temp/cmp/'
        )
        return

    # Determine column structure from the first snapshot file.
    first_depth_dir = depth_dirs[0][1]
    first_snap = join(first_depth_dir, 'snapshot_coseism.dat')
    if not exists(first_snap):
        consolidate_log.error(
            f'cannot determine column layout: {first_snap} not found'
        )
        return

    with open(first_snap, 'r') as f:
        ref_header = f.readline().rstrip('\n')

    # Header layout: "      Lat[deg]      Lon[deg]          Ux ..."
    lon_field_end = ref_header.index('Lon[deg]') + len('Lon[deg]')
    ux_header_start = ref_header.index('Ux')

    consolidate_log.debug(
        f'column layout: lon_end={lon_field_end}, ux_start={ux_header_start}'
    )

    depth_col_width = 10
    depth_header = 'Depth[km]'.rjust(depth_col_width)
    depth_fmt = f'{{:{depth_col_width}.4f}}'

    header_gap_after_lon = '   '
    header_gap_before_ux = '      '

    header_written = False
    output_path = join(constant.OUTPUT_PREFIX, 'consolidated.dat')
    makedirs(constant.OUTPUT_PREFIX, exist_ok=True)

    with open(output_path, 'w') as out:
        for depth_val, depth_dir in depth_dirs:
            snapshot_path = join(depth_dir, 'snapshot_coseism.dat')

            if not exists(snapshot_path):
                consolidate_log.warning(
                    f'snapshot_coseism.dat not found in {depth_dir}, '
                    f'skipping depth {depth_val}'
                )
                continue

            with open(snapshot_path, 'r') as f:
                lines = f.readlines()

            if not lines:
                consolidate_log.warning(f'empty file at {snapshot_path}')
                continue

            header = lines[0].rstrip('\n')

            if not header_written:
                header_written = True
                new_header = (
                    header[:lon_field_end]
                    + header_gap_after_lon
                    + depth_header
                    + header_gap_before_ux
                    + header[ux_header_start:]
                )
                out.write(new_header + '\n')

            for line in lines[1:]:
                stripped = line.rstrip('\n')
                if not stripped:
                    continue
                depth_value = depth_fmt.format(depth_val)
                new_line = (
                    stripped[:lon_field_end]
                    + depth_value
                    + '   '
                    + stripped[lon_field_end + 1:]
                )
                out.write(new_line + '\n')

    consolidate_log.debug(f'consolidated file written to {output_path}')

    write_gmt_coulomb_output()


def write_gmt_coulomb_output():
    """Write a GMT-compatible XYZ file with Coulomb stress data.

    Reads snapshot_coseism.dat from each depth directory and outputs a
    space-separated file with columns:
        Lon[deg]  Lat[deg]  Depth[km]  CMB_Fix  CMB_Op1  CMB_Op2

    The Fortran header is parsed to locate the fixed-width columns for
    CMB_Fix, CMB_Op1, and CMB_Op2.  If the CMB_Fix column is absent
    (icmb != 1 in the PSCMP input), the file is skipped.

    Output path: output/gmt_coulomb.xyz
    """
    cmp_root = join(constant.TEMP_PREFIX, 'cmp')

    depth_dirs = []
    for entry in listdir(cmp_root):
        full_path = join(cmp_root, entry)
        if isdir(full_path):
            try:
                depth_val = float(entry)
                depth_dirs.append((depth_val, full_path))
            except ValueError:
                continue

    depth_dirs.sort(key=lambda x: x[0])

    if not depth_dirs:
        consolidate_log.warning(
            'no depth directories found for GMT output'
        )
        return

    first_snap = join(depth_dirs[0][1], 'snapshot_coseism.dat')
    if not exists(first_snap):
        return

    with open(first_snap, 'r') as f:
        ref_header = f.readline().rstrip('\n')

    if 'CMB_Fix' not in ref_header:
        consolidate_log.warning(
            'CMB_Fix not found, skipping GMT output'
        )
        return

    # Column boundaries: (a28) for Lat+Lon, then (27E12.4) for the rest.
    lon_field_end = ref_header.index('Lon[deg]') + len('Lon[deg]')
    lat_field_end = lon_field_end - 14

    coord_width = 28
    e12 = 12

    def data_pos(name):
        """Return the byte offset of a named field in the data lines."""
        return (
            coord_width
            + ((ref_header.index(name) - coord_width) // e12) * e12
        )

    cmb_fix_start = data_pos('CMB_Fix')
    cmb_op1_start = data_pos('CMB_Op1')
    cmb_op2_start = data_pos('CMB_Op2')

    output_path = join(constant.OUTPUT_PREFIX, 'gmt_coulomb.xyz')
    makedirs(constant.OUTPUT_PREFIX, exist_ok=True)

    with open(output_path, 'w') as out:
        out.write(
            '# GMT-format Coulomb stress data generated by deltacfs\n'
        )
        out.write(
            '# Lon[deg]  Lat[deg]  Depth[km]  CMB_Fix  CMB_Op1  CMB_Op2\n'
        )

        for depth_val, depth_dir in depth_dirs:
            snapshot_path = join(depth_dir, 'snapshot_coseism.dat')
            if not exists(snapshot_path):
                continue

            with open(snapshot_path, 'r') as f:
                lines = f.readlines()

            for line in lines[1:]:
                stripped = line.rstrip('\n')
                if not stripped:
                    continue

                lat = stripped[:lat_field_end].strip()
                lon = stripped[lat_field_end:lon_field_end].strip()
                cmb_fix = stripped[
                    cmb_fix_start:cmb_fix_start + e12
                ].strip()
                cmb_op1 = stripped[
                    cmb_op1_start:cmb_op1_start + e12
                ].strip()
                cmb_op2 = stripped[
                    cmb_op2_start:cmb_op2_start + e12
                ].strip()

                out.write(
                    f'{lon} {lat} {depth_val} '
                    f'{cmb_fix} {cmb_op1} {cmb_op2}\n'
                )

    consolidate_log.debug(f'GMT Coulomb output written to {output_path}')
