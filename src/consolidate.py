"""
Consolidate scattered CMP depth results into a single merged output file.

Reads snapshot_coseism.dat from each depth directory under temp/cmp/,
inserts a Depth[km] column between Lon[deg] and Ux, and writes
a single combined file to output/consolidated.dat.

The original PSCMP fixed-width column formatting is preserved.
"""

from src import constant, logger_all
from os import listdir, makedirs
from os.path import isdir, join, exists

consolidate_log = logger_all.setlogger('consolidate')


def consolidate_cmp_results():
    """
    Read all snapshot_coseism.dat files from temp/cmp/{depth}/,
    insert a Depth[km] column between Lon[deg] and Ux, and write
    a single combined file to output/consolidated.dat.
    """
    cmp_root = join(constant.TEMP_PREFIX, 'cmp')

    # discover depth directories (named as numeric strings)
    depth_dirs = []
    for entry in listdir(cmp_root):
        full_path = join(cmp_root, entry)
        if isdir(full_path):
            try:
                depth_val = float(entry)
                depth_dirs.append((depth_val, full_path))
            except ValueError:
                consolidate_log.warning(f'skipping non-numeric directory: {entry}')

    depth_dirs.sort(key=lambda x: x[0])

    if not depth_dirs:
        consolidate_log.warning('no depth directories found under temp/cmp/')
        return

    # Determine column structure from the first snapshot file
    first_depth = depth_dirs[0]
    first_snap = join(first_depth[1], 'snapshot_coseism.dat')
    if not exists(first_snap):
        consolidate_log.error(f'cannot determine column layout: {first_snap} not found')
        return

    with open(first_snap, 'r') as f:
        ref_header = f.readline().rstrip('\n')

    # Column geometry in the header:
    #   "      Lat[deg]      Lon[deg]          Ux          Uy ..."
    #    0               14              28   38
    lon_field_end = ref_header.index('Lon[deg]') + len('Lon[deg]')  # = 28
    ux_header_start = ref_header.index('Ux')                         # = 38

    consolidate_log.debug(
        f'column layout: lon_end={lon_field_end}, ux_start={ux_header_start}'
    )

    # Depth column: narrower than Lat/Lon (10 vs 14) to sit closer to Lon
    depth_col_width = 10
    # Extra header spacing (visual separators between column titles)
    header_gap_after_lon = '   '
    header_gap_before_ux = '      '

    # Depth column header: right-aligned
    depth_header = 'Depth[km]'.rjust(depth_col_width)
    # Depth data values: right-aligned, 4 decimal places
    depth_fmt = f'{{:{depth_col_width}.4f}}'

    header_written = False
    output_path = join(constant.OUTPUT_PREFIX, 'consolidated.dat')
    makedirs(constant.OUTPUT_PREFIX, exist_ok=True)

    with open(output_path, 'w') as out:
        for depth_val, depth_dir in depth_dirs:
            snapshot_path = join(depth_dir, 'snapshot_coseism.dat')

            if not exists(snapshot_path):
                consolidate_log.warning(
                    f'snapshot_coseism.dat not found in {depth_dir}, skipping depth {depth_val}'
                )
                continue

            with open(snapshot_path, 'r') as f:
                lines = f.readlines()

            if not lines:
                consolidate_log.warning(f'empty file at {snapshot_path}')
                continue

            header = lines[0].rstrip('\n')

            # Build merged header once
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

            # Data lines: insert depth value after the Lon field
            # Original data after Lon = 1 space + rest, so:
            #   keep first 28 chars (Lat + Lon), insert depth + gap, rest
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
