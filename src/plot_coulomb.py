"""GMT-based Coulomb stress cross-section plotter.

Reads output/gmt_coulomb.xyz and renders a fault-plane cross-section showing
the CMB_Fix distribution (distance along strike × depth) with a diverging
colour scale centred at 0.

All GMT commands are invoked via subprocess so no external shell wrapper is
needed beyond a GMT 6 installation in PATH.
"""

import math
import os
import subprocess
import tempfile
from collections import defaultdict

from src import constant, logger_all

plot_log = logger_all.setlogger('plot_coulomb')


def _read_depth_step_and_interval():
    """Return (depth_step, observation_interval) in km.

    observation_interval = depth_step * 2.0 (matches main.py).
    """
    config_path = os.path.join(
        constant.CONFIG_PREFIX, 'calculation_setting.dat'
    )
    with open(config_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                depth_step = float(line.strip().split()[0])
                break
    return depth_step, depth_step * 2.0


def _build_fault_plane_xyz(input_path, output_path, observation_interval):
    """Convert (lon, lat, depth, cmb) → cell-centred (dist, depth, cmb).

    Builds a 2-D array of CMB values indexed by [depth_idx][strike_idx], then
    writes each rectangular cell as a pixel-registered point whose value is
    the mean of its four corner data points.  No smoothing or interpolation
    is applied — each cell's colour represents exactly the average of its
    four vertices.

    Returns:
        dist_max:  Along-strike extent (km) of the full data array.
        depth_max: Maximum depth (km) of the full data array.
        absmax:    Absolute maximum |CMB_Fix| across all data points.
        dist_inc:  Along-strike cell width (km).
        depth_inc: Depth cell height (km).
        cell_centers:  (n_cells_strike, n_cells_depth) — for grid info.
    """
    with open(input_path) as f:
        raw = [l.split() for l in f if not l.startswith('#') and l.strip()]

    # Group data by depth, preserving order within each depth.
    by_depth = defaultdict(list)
    depth_set = set()
    for lon, lat, depth_str, cmb, *_ in raw:
        d = float(depth_str)
        by_depth[d].append(float(cmb))
        depth_set.add(d)

    depths = sorted(by_depth.keys())
    n_pts = len(by_depth[depths[0]])
    n_depths = len(depths)

    # Build 2-D array: grid[depth_idx][strike_idx]
    grid_2d = []
    for d in depths:
        vals = by_depth[d]
        assert len(vals) == n_pts
        grid_2d.append(vals)

    all_cmb = [v for row in grid_2d for v in row]
    absmax = max(abs(min(all_cmb)), abs(max(all_cmb)))

    spacing = observation_interval
    depth_inc = depths[1] - depths[0] if n_depths > 1 else 1.0

    n_cells_strike = n_pts - 1
    n_cells_depth  = n_depths - 1

    dist_max  = n_cells_strike * spacing
    depth_max = n_cells_depth  * depth_inc

    with open(output_path, 'w') as out:
        out.write('# dist_along_strike_km  depth_km  CMB_Fix  (pixel registration)\n')
        for j in range(n_cells_depth):        # depth index
            for i in range(n_cells_strike):    # along-strike index
                # Mean of the four corner data points of this cell
                cell_val = (
                      grid_2d[j  ][i]
                    + grid_2d[j  ][i + 1]
                    + grid_2d[j + 1][i]
                    + grid_2d[j + 1][i + 1]
                ) / 4.0

                # Cell centre coordinates
                cell_x = (i + 0.5) * spacing
                cell_y = depths[j] + depth_inc / 2.0

                out.write(f'{cell_x:.4f}  {cell_y:.4f}  {cell_val:.6e}\n')

    cell_centers = (n_cells_strike, n_cells_depth)
    return dist_max, depth_max, absmax, spacing, depth_inc, cell_centers


def _nice_interval(data_range):
    """Return a round annotation interval for the colour bar.

    Snaps the rough interval (range / 5) to 1, 2, or 5 × 10^n so the
    colour bar shows 4–8 ticks regardless of the data range.
    """
    rough = data_range / 5
    exponent = math.floor(math.log10(rough))
    mantissa = rough / 10 ** exponent
    if mantissa < 1.5:
        nice = 1
    elif mantissa < 3.5:
        nice = 2
    else:
        nice = 5
    return int(nice * 10 ** exponent)


def _run_gmt(*args, check=True, **kwargs):
    """Thin wrapper around subprocess.run for GMT commands.

    Extra keyword arguments (e.g. stdout) are forwarded to subprocess.run.
    """
    cmd = ['gmt'] + list(args)
    plot_log.debug(f'Running: {cmd}')
    if 'capture_output' not in kwargs and 'stdout' not in kwargs:
        kwargs['capture_output'] = True
    result = subprocess.run(cmd, text=True, **kwargs)
    if check and result.returncode != 0:
        stderr = getattr(result, 'stderr', '')
        plot_log.error(f'GMT command failed: {cmd}\n{stderr}')
        raise RuntimeError(f'GMT {args[0]} failed: {stderr}')
    return result


def plot_coulomb_section(cmb_min=None, cmb_max=None):
    """Render a CMB_Fix fault-plane cross-section to PDF.

    Reads output/gmt_coulomb.xyz, grids the data at the natural observation
    spacing, and produces output/coulomb_fault_plane.pdf and .ps.

    Args:
        cmb_min: Lower bound of the colour scale (default: -absmax).
        cmb_max: Upper bound of the colour scale (default: +absmax).

    Returns:
        str: Path to the generated PDF file.
    """
    input_xyz = os.path.join(constant.OUTPUT_PREFIX, 'gmt_coulomb.xyz')
    if not os.path.isfile(input_xyz):
        raise FileNotFoundError(
            f'{input_xyz} not found — run the Coulomb phase first.'
        )

    depth_step, observation_interval = _read_depth_step_and_interval()

    # Write cell-centred (pixel-registered) fault-plane XYZ.
    tmp_xyz = os.path.join(constant.OUTPUT_PREFIX, 'fault_plane.xyz')
    dist_max, depth_max, absmax, dist_inc, depth_inc, cell_centers = (
        _build_fault_plane_xyz(input_xyz, tmp_xyz, observation_interval)
    )
    n_cells_strike, n_cells_depth = cell_centers

    if cmb_min is None:
        cmb_min = -absmax
    if cmb_max is None:
        cmb_max = absmax

    logger_all.logged_print(
        f'Grid: {n_cells_strike}×{n_cells_depth} cells, '
        f'{dist_max:.0f} km along strike × {depth_max:.0f} km depth',
        plot_log,
    )
    logger_all.logged_print(
        f'CMB_Fix range: [{cmb_min:.2e}, {cmb_max:.2e}]', plot_log
    )

    # GMT working files (use tempfile for process-safe naming).
    with tempfile.NamedTemporaryFile(suffix='.cpt', delete=False) as f:
        cpt_path = f.name
    with tempfile.NamedTemporaryFile(suffix='.grd', delete=False) as f:
        grd_path = f.name

    try:
        # Diverging CPT centred at 0, symmetrical range.
        _run_gmt(
            'makecpt', '-Cpolar',
            f'-T{cmb_min}/{cmb_max}/{(cmb_max-cmb_min)/50:.2e}',
            stdout=open(cpt_path, 'w'),
        )

        # Grid from cell-centred data (pixel registration).
        # Pixel registration: -R spans the extent of the pixel array,
        # xyz data are at pixel centres.
        _run_gmt(
            'xyz2grd', tmp_xyz,
            f'-R0/{dist_max:.1f}/0/{depth_max:.1f}',
            f'-I{dist_inc}/{depth_inc}',
            '-r',  # pixel registration
            f'-G{grd_path}',
        )

        ps_path = os.path.join(
            constant.OUTPUT_PREFIX, 'coulomb_fault_plane.ps'
        )

        # Fault-plane cross-section, depth 0 at top (negative J height).
        _run_gmt(
            'grdimage', grd_path,
            f'-R0/{dist_max:.1f}/0/{depth_max:.1f}',
            '-JX15c/-9c',
            f'-C{cpt_path}', '-K',
            '-Bxa2f1g2+l"Distance along strike (km)"',
            '-Bya1f0.5g1+l"Depth(km)"', '-BWSen',
            '--FONT_ANNOT_PRIMARY=9p', '--FONT_LABEL=11p',
            '--MAP_FRAME_PEN=0.5p',
            '--MAP_ANNOT_OFFSET_PRIMARY=2p', '--MAP_LABEL_OFFSET=6p',
            stdout=open(ps_path, 'w'),
        )

        # Colour bar vertically centred on the plot.
        # J=-9c → projected Y ranges from 0 (top) to -9c (bottom);
        # midpoint is -4.5c.
        cb_interval = _nice_interval(cmb_max - cmb_min)
        _run_gmt(
            'psscale', f'-C{cpt_path}',
            '-Dx16c/-4.5c+w8c/0.35c',
            f'-Bxa{cb_interval}+l"CMB_Fix (MPa)"',
            '-O',
            '--FONT_ANNOT_PRIMARY=8p', '--FONT_LABEL=10p',
            stdout=open(ps_path, 'a'),
        )

        logger_all.logged_print(f'Plot written to: {ps_path}', plot_log)

        # Convert to PDF.
        _run_gmt('psconvert', ps_path, '-Tf', '-P')
        pdf_path = os.path.join(
            constant.OUTPUT_PREFIX, 'coulomb_fault_plane.pdf'
        )
        logger_all.logged_print(f'PDF: {pdf_path}', plot_log)

        return pdf_path

    finally:
        # Clean up working files.
        for p in (cpt_path, grd_path, tmp_xyz):
            try:
                os.remove(p)
            except OSError:
                pass
