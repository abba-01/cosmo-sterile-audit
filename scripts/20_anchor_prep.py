#!/usr/bin/env python3
"""
Prepare anchor data: crossmatch Gaia+SH0ES, apply extinction, ZP corrections.
"""

import sys


def prepare_anchors():
    """Prepare anchor Cepheids for Period-Luminosity fit."""
    print("Preparing Cepheid anchor data...")
    print("TODO: Crossmatch Gaia parallaxes with SH0ES Cepheids")
    print("TODO: Apply Milky Way extinction corrections")
    print("TODO: Apply zero-point calibration offsets")
    print("TODO: Propagate uncertainty correlations")
    print("TODO: Save to data/processed/anchors.csv")
    return 0


if __name__ == "__main__":
    sys.exit(prepare_anchors())
