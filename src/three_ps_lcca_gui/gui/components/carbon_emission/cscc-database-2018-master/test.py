"""
Verify that pickle lookups match the raw CSV for a representative set of cases.
Run: python test.py
"""
import csv
import math
import pandas as pd
from pathlib import Path

CSV_PATH = Path(__file__).parent / "cscc_db_v2.csv"
PKL_PATH = Path(__file__).parent / "cscc_db.pkl"

KEY_COLS = ["ISO3", "run", "dmgfuncpar", "climate", "SSP", "RCP", "prtp", "eta", "dr"]
PCT_COLS = ["16.7%", "50%", "83.3%"]


def load_csv_samples(n=200):
    """Return n evenly-spaced rows from the CSV as dicts."""
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    step = max(1, len(rows) // n)
    return rows[::step]


def main():
    print(f"Loading pickle from {PKL_PATH} ...")
    df = pd.read_pickle(PKL_PATH)

    samples = load_csv_samples()
    print(f"Checking {len(samples)} sample rows from CSV against pickle ...\n")

    passed = 0
    failed = 0

    for csv_row in samples:
        key = tuple(csv_row[c] for c in KEY_COLS)

        # Skip rows where percentile values are not numeric in CSV
        try:
            csv_vals = tuple(float(csv_row[c]) for c in PCT_COLS)
        except ValueError:
            continue

        try:
            pkl_row = df.loc[key]
            pkl_vals = tuple(float(pkl_row[c]) for c in PCT_COLS)
        except KeyError:
            print(f"FAIL  key not found in pickle: {key}")
            failed += 1
            continue

        if not all(math.isclose(a, b, rel_tol=1e-9) for a, b in zip(csv_vals, pkl_vals)):
            print(f"FAIL  value mismatch for {key}")
            print(f"      CSV : {csv_vals}")
            print(f"      PKL : {pkl_vals}")
            failed += 1
        else:
            passed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {passed + failed} checked.")
    if failed == 0:
        print("All checks passed.")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
