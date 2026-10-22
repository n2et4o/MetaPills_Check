"""
Crée le zip de rendu, nommé comme le dossier du projet
(ex. StApp26_20220848_Joss_DOUNIAMA_OKANA_BIO.zip), à côté du dossier.

Contenu : code Python, README, DATA_SOURCE (lien du jeu de données), requirements,
config Streamlit, textes FR/EN, et les données pré-traitées (data/processed/).
Exclus : données brutes (data/raw/, ~83 Mo, retéléchargeables), environnement, caches.

Usage :
    python scripts/make_submission.py              # nom = nom du dossier du projet
    python scripts/make_submission.py MON_NOM      # nom personnalisé (sans .zip)
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INCLUDE = [
    "app.py", "README.md", "DATA_SOURCE.md", "requirements.txt", ".gitignore",
    ".streamlit/config.toml",
    "locales/*.json",
    "scripts/*.py",
    "utils/*.py",
    "sections/*.py",
    "data/processed/*",
    "data/raw/.gitkeep",
    "assets/*",
]
REQUIRED = ["app.py", "README.md", "DATA_SOURCE.md", "requirements.txt",
            "data/processed/associations.parquet", "data/processed/quality_report.json"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else ROOT.name
    missing = [f for f in REQUIRED if not (ROOT / f).exists()]
    if missing:
        print(f"[erreur] fichiers manquants : {missing}", file=sys.stderr)
        return 1

    files = sorted({p for pattern in INCLUDE for p in ROOT.glob(pattern) if p.is_file()})
    out = ROOT.parent / f"{name}.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            # Tout est rangé dans un dossier racine portant le nom du rendu
            zf.write(path, Path(name) / path.relative_to(ROOT))

    print(f"{len(files)} fichiers ajoutés :")
    for path in files:
        print(f"  {path.relative_to(ROOT)}  ({path.stat().st_size / 1e3:.0f} ko)")
    print(f"\n-> {out}  ({out.stat().st_size / 1e6:.1f} Mo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
