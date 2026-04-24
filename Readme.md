# deltacfs

A Python shell that orchestrates the **PSGRN/PSCMP** Fortran codes to compute Coulomb stress changes (ΔCFS) from earthquake source models.

## Overview

`deltacfs` automates a multi-depth, multi-phase pipeline.  All functionality is accessible through a single interactive entry point:

```bash
python3 main.py
```

The pipeline has five phases:

1. **Green's function** — generates PSGRN input files and runs `fomosto_psgrn2008a` to compute elastic Green's functions for a layered earth model at each observation depth.
2. **Coulomb stress** — generates PSCMP input files and runs `fomosto_pscmp2008a` to compute Coulomb stress changes (ΔCFS) on the receiving fault plane at each depth.
3. **After-process** — merges per-depth snapshot outputs into `output/` and writes GMT-compatible XYZ data.
4. **Plot** — renders a fault-plane cross-section of CMB_Fix via GMT.
5. **Clean** — removes generated `temp/`, `logs/`, and `output/` directories.

Each phase is toggled independently at runtime (`y` / `no-override` / `n` for computation phases; `y` / `n` for plot and clean).

## Requirements

- **Python 3.12+** with `pyproj==3.7.0` (see `requirements.txt`)
- **PSGRN/PSCMP** Fortran binaries (`fomosto_psgrn2008a` and `fomosto_pscmp2008a`) on `$PATH`
- **GMT 6** (required for the plot phase)
- **Ghostscript** (required for PS → PDF conversion in the plot phase)

The project auto-detects its own root directory and can be invoked from any working directory.

## Quick Start

```bash
# Interactive run — choose which phases to execute
python3 main.py

# Or use the shell wrapper (cd's to project root first)
./src/run.sh

# Clean generated files (also available as phase 5 in main.py)
./src/clean.sh
```

## Project Structure

```
deltacfs/
├── main.py              # Unified entry point — all five phases
├── src/
│   ├── constant.py      # Absolute-path constants, validators
│   ├── settings.py      # Config file readers
│   ├── error.py         # Custom exception hierarchy
│   ├── logger_all.py    # Logging, subprocess, prompt helpers
│   ├── grn_input.py     # PSGRN input generator
│   ├── cmp_input.py     # PSCMP input generator (obs. points, prestress)
│   ├── consolidate.py   # Per-depth merge + GMT XYZ writer
│   ├── plot_coulomb.py  # GMT fault-plane cross-section plotter
│   ├── run.sh           # Shell wrapper (cd + python3 main.py)
│   ├── psgrn.sh         # PSGRN Fortran launcher
│   ├── pscmp.sh         # PSCMP Fortran launcher
│   └── clean.sh         # Remove temp/ logs/ output/
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

## Interactive Dialogue

On startup, `main.py` prints the available phases and prompts:

```
Setup all files in config/ before running.
Phases available:
  1. Green's function computation   (PSGRN)
  2. Coulomb stress computation      (PSCMP)
  3. After-process                   (merge outputs)
  4. Plot Coulomb cross-section      (GMT)
  5. Clean generated files           (temp/ logs/ output/)

Run phase 1 — Green's function set? (y/no-override/n):
Run phase 2 — Coulomb stress ΔCFS? (y/no-override/n):
Run phase 3 — after-process? (y/no-override/n):
Run phase 4 — plot Coulomb cross-section? (y/n):
Run phase 5 — clean generated files? (y/n):
```

Valid responses:
- **`y`** — override existing data and run
- **`no-override`** — run only if output doesn't already exist
- **`n`** — skip this phase

## Config Files

### `receiving_fault.dat`
Defines the receiving (target) fault geometry: origin lat/lon, depth, length, width, strike, dip.  Multiple sub-fault segments are supported.  The depth range for observation is computed from the shallowest origin and deepest down-dip extent.

### `source_fault.dat`
Lists the source fault sub-faults (up to 432 currently) with their positions, dimensions, and slip distributions (*pos_s*, *pos_d*, *slip_strike*, *slip_downdip*, *opening*).

### `calculation_setting.dat`
Controls:
- **Depth step** (1st row, 1st value) — also determines the horizontal observation spacing as `depth_step × 2` km.
- Observation distance settings (2nd row).
- Source depth settings (3rd row).
- Time sampling and wavenumber integration parameters.

### `config.dat`
Output switches:
- `insar` (0/1) — enable InSAR LOS displacement output.
- `icmb` (0/1) — enable Coulomb stress output.  When enabled, also provides: friction coefficient, Skempton ratio, master fault strike/dip/rake, and three principal stresses (sigma1, sigma2, sigma3).
- Snapshot count and per-snapshot time + filenames.

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

The plot is a cross-section of the receiving fault plane: distance along strike (x-axis, km) vs depth (y-axis, km, reversed so 0 is at the top).  The colour scale is a diverging polar CPT centred at 0.  The plot phase can be run independently — as long as `output/gmt_coulomb.xyz` exists from a previous after-process phase.

## Portability

- All internal paths are resolved to absolute paths at import time via `src/constant.py`.  `main.py` can be invoked from any working directory.
- The Fortran binaries are expected on `$PATH` (the shell launchers use `fomosto_psgrn2008a` / `fomosto_pscmp2008a` without absolute paths).
- The only Python dependency beyond the standard library is `pyproj`.

## Notes

- The horizontal observation point spacing is `depth_step × 2` km by design, matching the `observation_max_interval` argument to `build_cmp_input`.
- At depth 8 km the earth model has a significant layer boundary (Vp/Vs/ρ change), which produces a visible discontinuity in CMB_Fix values at that depth.  Use `CMB_MIN` / `CMB_MAX` environment variables to narrow the colour range if shallow detail is obscured.
