# deltacfs

A Python shell that orchestrates the **PSGRN/PSCMP** Fortran codes to compute Coulomb stress changes (ΔCFS) from earthquake source models.

## Overview

`deltacfs` automates a multi-depth, multi-phase pipeline:

1. **Green's function phase** — generates PSGRN input files (`temp/grn_input/`) and runs `fomosto_psgrn2008a` to compute elastic Green's functions for a layered earth model at each observation depth.
2. **Coulomb stress phase** — generates PSCMP input files (`temp/cmp_input/`) and runs `fomosto_pscmp2008a` to compute stress and Coulomb stress changes on the receiving fault plane at each depth.
3. **After-process phase** — merges per-depth snapshot outputs into `output/` and writes GMT-compatible XYZ data for visualisation.

Each phase can be toggled independently at runtime (`y` / `no-override` / `n`).

## Requirements

- **Python 3.12+** with `pyproj==3.7.0` (see `requirements.txt`)
- **Fortran binaries**: `/usr/local/bin/fomosto_psgrn2008a` and `/usr/local/bin/fomosto_pscmp2008a`
- **GMT 6** (optional, for `src/plot_coulomb.sh`)
- **Ghostscript** (optional, for PS → PDF conversion)
- A conda environment named `deltacfs` (or update the Python path in run scripts)

## Quick Start

```bash
# Run the full pipeline (interactive prompts)
python3 main.py

# Or use the shell wrapper (same behaviour)
./src/run.sh

# Clean all generated files
./src/clean.sh

# Plot Coulomb stress cross-section (after a full run)
./src/plot_coulomb.sh
```

## Project Structure

```
deltacfs/
├── main.py              # Top-level pipeline orchestrator
├── src/
│   ├── constant.py      # Paths, constants, validators
│   ├── settings.py      # Config file readers
│   ├── error.py         # Custom exception hierarchy
│   ├── logger_all.py    # Logging + subprocess + prompt helpers
│   ├── grn_input.py     # PSGRN input generator
│   ├── cmp_input.py     # PSCMP input generator (obs. points, prestress)
│   ├── consolidate.py   # Per-depth → merged output + GMT XYZ
│   ├── run.sh           # Conda wrapper for main.py
│   ├── psgrn.sh         # PSGRN Fortran launcher
│   ├── pscmp.sh         # PSCMP Fortran launcher
│   ├── clean.sh         # Remove temp/ logs/ output/
│   └── plot_coulomb.sh  # GMT fault-plane cross-section
├── config/              # User-editable parameter files
│   ├── receiving_fault.dat
│   ├── source_fault.dat
│   ├── calculation_setting.dat
│   ├── config.dat
│   └── model.dat
├── output/              # Generated results (created at runtime)
│   ├── consolidated.dat
│   ├── gmt_coulomb.xyz
│   └── coulomb_fault_plane.pdf
├── temp/                # Intermediate files (created at runtime)
│   ├── grn_input/       # .grn files
│   ├── grn/{depth}/     # Green's function output
│   ├── cmp_input/       # .cmp files
│   └── cmp/{depth}/     # PSCMP output per depth
└── logs/                # Timestamped log files
```

## Config Files

### `receiving_fault.dat`
Defines the receiving (target) fault geometry: origin lat/lon, depth, length, width, strike, dip.  Multiple sub-faults are supported.  The depth range for observation is computed from the shallowest origin and deepest down-dip extent.

### `source_fault.dat`
Lists the source fault sub-faults (up to 432 currently) with their positions, dimensions, and slip distributions (*pos_s*, *pos_d*, *slip_strike*, *slip_downdip*, *opening*).

### `calculation_setting.dat`
Controls:
- **Depth step** (1st row, 1st value) — also determines the horizontal observation spacing as `depth_step × 2` km (see `main.py`).
- Observation distance settings (2nd row).
- Source depth settings (3rd row).
- Time sampling and wavenumber integration parameters.

### `config.dat`
Output switches:
- `insar` (0/1) — enable InSAR LOS displacement output.
- `icmb` (0/1) — enable Coulomb stress output.  When enabled, also provides: friction coefficient, Skempton ratio, master fault strike/dip/rake, and three principal stresses (sigma1, sigma2, sigma3).
- Snapshot count and snapshot time + filenames.

### `model.dat`
Layered viscoelastic earth model: depth, Vp, Vs, density, transient viscosity η1, steady-state viscosity η2, and relaxation ratio α (all layers elastic when η1 = η2 = 0).

## Output Files

| File | Description |
|------|-------------|
| `output/consolidated.dat` | All depths merged; fixed-width Fortran format with added `Depth[km]` column |
| `output/gmt_coulomb.xyz` | Space-separated: `lon lat depth CMB_Fix CMB_Op1 CMB_Op2` |
| `output/coulomb_fault_plane.pdf` | Fault-plane cross-section plot (via GMT) |

## Coulomb Stress Columns

When `icmb = 1`, each snapshot file contains:

```
CMB_Fix    — Coulomb stress on the fixed (master) fault
Sig_Fix    — Normal stress on the fixed fault
CMB_Op1    — Coulomb stress on optimal fault orientation 1
CMB_Op2    — Coulomb stress on optimal fault orientation 2
(plus Sig, Str, Dip, Slp for each optimal orientation)
```

**CMB_Fix** is the primary diagnostic: it is the ΔCFS resolved on the user-specified receiving fault geometry.  If all three principal stresses (sigma1, sigma2, sigma3) are set to 0 in `config.dat`, the output contains only the coseismic stress change with no background prestress contribution.

## Plotting

```bash
# Use default symmetrical colour range
./src/plot_coulomb.sh

# Narrow the range to highlight shallow detail
CMB_MIN=-6000 CMB_MAX=6000 ./src/plot_coulomb.sh
```

The plot shows a cross-section of the receiving fault plane: distance along strike (x-axis, km) vs depth (y-axis, km, reversed so 0 is at the top).  The colour scale is a diverging polar CPT centred at 0.

## Notes

- All paths are relative to the project root.  Always run from the project root directory.
- The horizontal observation point spacing is `depth_step × 2` km by design, matching the `observation_max_interval` argument to `cmp_input.build_cmp_input`.
- At depth 8 km the earth model has a significant layer boundary (Vp/Vs/ρ change), which produces a visible discontinuity in CMB_Fix values at that depth.
