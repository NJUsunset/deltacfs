#!/bin/bash
# Plot Coulomb stress change (CMB_Fix) distribution on the receiving fault plane.
#
# Thin wrapper around src/plot_coulomb.py — all logic is in the Python module.
# This script exists for convenience; prefer using `python3 main.py` (phase 4).
#
# Usage:
#   ./src/plot_coulomb.sh
#   CMB_MIN=-5000 CMB_MAX=5000 ./src/plot_coulomb.sh   # custom colour range
#
# Dependencies: GMT 6, Python 3 + pyproj

set -euo pipefail

cd "$(dirname "$0")/.."
python3 -c "
import os
from src.plot_coulomb import plot_coulomb_section

cmb_min = float(os.environ.get('CMB_MIN', 0) or 0) or None
cmb_max = float(os.environ.get('CMB_MAX', 0) or 0) or None

plot_coulomb_section(cmb_min=cmb_min, cmb_max=cmb_max)
"
