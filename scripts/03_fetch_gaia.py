#!/usr/bin/env python3
"""
Fetch Gaia EDR3 parallax data for Cepheid anchors and verify SHA-256 checksum.
"""

import sys


def fetch_gaia_data():
    """Download Gaia parallax subset and verify checksum."""
    print("Fetching Gaia EDR3 Cepheid parallax data...")
    print("TODO: Implement ADQL query to Gaia archive")
    print("TODO: Filter for parallax_over_error > 5")
    print("TODO: Verify SHA-256 against manifests/sources.yml")
    print("TODO: Save to data/raw/gaia/")
    return 0


if __name__ == "__main__":
    sys.exit(fetch_gaia_data())
