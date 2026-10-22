"""
Affiche la structure des fichiers téléchargés (colonnes, types, valeurs manquantes).
Usage : python scripts/inspect_data.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_colwidth", 60)

# --- 1. Fichier principal de résultats -----------------------------------
tsv = RAW / "output_all_formatted_noc_uncollapsed_complete.tsv"
df = pd.read_csv(tsv, sep="\t", low_memory=False)

print("=" * 80)
print(f"FICHIER : {tsv.name}")
print(f"Dimensions : {df.shape[0]:,} lignes x {df.shape[1]} colonnes")
print("=" * 80)

summary = pd.DataFrame({
    "type": df.dtypes.astype(str),
    "nb_uniques": df.nunique(),
    "%_manquant": (df.isna().mean() * 100).round(1),
    "exemple": df.iloc[0],
})
print(summary)

print("\n--- 3 premières lignes (transposées) ---")
print(df.head(3).T)

print(f"\nLignes dupliquées : {df.duplicated().sum():,}")

# --- 2. Fichiers de noms et de métadonnées --------------------------------
for folder in ["feature_names", "metadata"]:
    print("\n" + "=" * 80)
    print(f"DOSSIER : data/raw/{folder}/")
    print("=" * 80)
    for f in sorted((RAW / folder).rglob("*")):
        if f.is_file():
            print(f"\n> {f.relative_to(RAW)}  ({f.stat().st_size / 1e3:.1f} ko)")
            with f.open(encoding="utf-8", errors="replace") as fh:
                for _ in range(3):
                    line = fh.readline().rstrip()
                    if not line:
                        break
                    print("   ", line[:150])