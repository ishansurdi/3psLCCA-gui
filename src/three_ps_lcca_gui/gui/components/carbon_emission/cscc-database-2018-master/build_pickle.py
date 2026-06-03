import pandas as pd
from pathlib import Path

CSV_PATH = Path(__file__).parent / "cscc_db_v2.csv"
PKL_PATH = Path(__file__).parent / "cscc_db.pkl"

# Key columns must stay as strings ("NA" is a valid value, not missing)
STR_COLS = ["ISO3", "run", "dmgfuncpar", "climate", "SSP", "RCP", "prtp", "eta", "dr"]

df = pd.read_csv(CSV_PATH, dtype={c: str for c in STR_COLS}, keep_default_na=False)
df.set_index(STR_COLS, inplace=True)
df.sort_index(inplace=True)
df.to_pickle(PKL_PATH)

print(f"Saved {len(df):,} rows to {PKL_PATH}")
