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
    """Convert (lon, lat, depth, cmb) → (dist_along_strike, depth, cmb).

    Distance is assigned by point index within each depth level since the
    observation points were generated at equal spacing along strike via
    geod.fwd.  Geodesic distance is NOT recomputed because lon/lat in the
    output file have already been through a Fortran complex-number round-trip
    that can introduce coordinate-order inconsistencies.
    """
    with open(input_path) as f:
        raw = [l.split() for l in f if not l.startswith('#') and l.strip()]

    by_depth = defaultdict(list)
    for lon, lat, depth, cmb, *_ in raw:
        by_depth[float(depth)].append((float(lon), float(lat), float(cmb)))

    depths = sorted(by_depth.keys())
    all_cmb = [c for pts in by_depth.values() for (_, _, c) in pts]

    n_pts = len(by_depth[depths[0]])
    spacing = observation_interval

    with open(output_path, 'w') as out:
        out.write('# dist_along_strike_km  depth_km  CMB_Fix\n')
        for depth in depths:
            pts = by_depth[depth]
            for i, (lon, lat, cmb) in enumerate(pts):
                dist_km = i * spacing
                out.write(f'{dist_km:.4f}  {depth:.1f}  {cmb:.6e}\n')

    absmax = max(abs(min(all_cmb)), abs(max(all_cmb)))
    dist_max = (n_pts - 1) * spacing
    depth_max = max(depths)

    return dist_max, depth_max, absmax


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

    # Write the fault-plane XYZ intermediate file.
    tmp_xyz = os.path.join(constant.OUTPUT_PREFIX, 'fault_plane.xyz')
    dist_max, depth_max, absmax = _build_fault_plane_xyz(
        input_xyz, tmp_xyz, observation_interval
    )
    dist_inc = observation_interval
    depth_inc = depth_step

    if cmb_min is None:
        cmb_min = -absmax
    if cmb_max is None:
        cmb_max = absmax

    logger_all.logged_print(
        f'Grid: 0–{dist_max:.0f} km along strike '
        f'× 0–{depth_max:.0f} km depth',
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
            f'-T{cmb_min}/{cmb_max}/{(cmb_max-cmb_min)/10:.2e}',
            stdout=open(cpt_path, 'w'),
        )

        # Grid from regular data (gridline registration).
        _run_gmt(
            'xyz2grd', tmp_xyz,
            f'-R0/{dist_max:.1f}/0/{depth_max:.1f}',
            f'-I{dist_inc}/{depth_inc}',
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

        # Colour bar on the right side — annotation interval adapts to range.
        cb_interval = _nice_interval(cmb_max - cmb_min)
        _run_gmt(
            'psscale', f'-C{cpt_path}',
            '-Dx16c/3c+w8c/0.35c',
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
