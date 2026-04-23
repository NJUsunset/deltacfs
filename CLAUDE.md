# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`deltacfs` is a Python shell that wraps **PSGRN/PSCMP** (Fortran-based geophysics software) to calculate Coulomb stress changes (ΔCFS) from earthquake source models. It automates the workflow of generating input files, running the Fortran binaries, and combining outputs across multiple depths.

### Workflow (main.py)

1. Read config files from `config/`
2. Calculate a depth array from `depth_min` to `depth_max` using `depth_step`
3. **Green's function phase**: For each depth, build PSGRN input → run `psgrn.sh` → compute elastic Green's functions
4. **Stress/ΔCFS phase**: For each depth, build PSCMP input → run `pscmp.sh` → compute stress and Coulomb stress changes
5. **After-process phase**: Combine outputs across depths into `output/`

Each phase can be toggled independently (y/no-override/n) at runtime.

## Code Architecture

### Entry Point
- **`main.py`** — Top-level orchestration with try/except blocks for each phase. The `TEST = True` flag controls log verbosity (DEBUG vs INFO).

### Source Modules (`src/`)

- **`constant.py`** — Path constants (`CONFIG_PREFIX`, `TEMP_PREFIX`, `SRC_PREFIX`, `OUTPUT_PREFIX`, `LOG_PREFIX`) and validation range classes (`Range`, `BoolenNumber` for validating config values)
- **`settings.py`** — Reads all config `.dat` files: `depth_minmax()`, `calculation_setting()`, `config()`, and `combine_file()` (after-process)
- **`grn_input.py`** — `build_grn_input(depth, calculation_settings)` — Generates PSGRN input files with layered earth model from `model.dat`
- **`cmp_input.py`** — `build_cmp_input(depth, observation_max_interval, configs)` — Generates PSCMP input files, including generating observation points along the receiving fault plane using pyproj geodesic calculations
- **`logger_all.py`** — Logging infrastructure: `initlogger()` (file + console), `setlogger()` (module-level child loggers), `logged_run()` (subprocess with streaming), `logged_input()` (validated prompts), `logged_print()`
- **`error.py`** — Custom exceptions: `InputValueError`, `FunctionRunningError`, `ConfigFileError`, `CommandRunningError`

### Shell Scripts (`src/`)

- **`run.sh`** — Invokes `python3 main.py` with the conda environment
- **`psgrn.sh`** — Validates `.grn` input, pipes it to `/usr/local/bin/fomosto_psgrn2008a`
- **`pscmp.sh`** — Validates `.cmp` input, pipes it to `/usr/local/bin/fomosto_pscmp2008a`
- **`clean.sh`** — Removes `temp/`, `logs/`, `output/` directories

### Config Files (`config/`)

- **`receiving_fault.dat`** — Receiving fault geometry (origin, strike, dip, dimensions)
- **`calculation_setting.dat`** — Depth step, observation intervals, time sampling, wavenumber integration params
- **`config.dat`** — Output options (InSAR LOS, Coulomb stress mode), snapshot parameters, fault mechanism
- **`model.dat`** — Layered viscoelastic earth model (layer thickness, density, seismic velocities, viscosity)
- **`source_fault.dat`** — Source fault rupture parameters (position, dimensions, slip, rake)

### Data Flow

```
config/*.dat → settings.py → depth_array
                            ↓
config/model.dat + depth → grn_input.py → .grn file → psgrn.sh → temp/grn/{depth}/
                                                                       ↓
config/receiving_fault.dat + depth → cmp_input.py → .cmp file → pscmp.sh → temp/cmp/{depth}/
                                                                                ↓
                                                                         settings.combine_file() → output/
```

## Dependencies

- Python 3.12+
- `pyproj==3.7.0` (geodesic calculations for fault plane point generation)
- Fortran binaries: `/usr/local/bin/fomosto_psgrn2008a` and `/usr/local/bin/fomosto_pscmp2008a`
- Conda environment: `deltacfs`

## Commands

```bash
# Run the full workflow (with interactive prompts)
python3 main.py

# Or use the shell script
./src/run.sh

# Clean generated temp/logs/output
./src/clean.sh
```

No test framework or test files are currently configured in this project.
