"""
Transforme les fichiers bruts (data/raw/) en fichiers légers pour l'app (data/processed/).
À lancer une seule fois, après scripts/download_data.py :
    python scripts/build_processed.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

# Permet d'importer utils/ quand on lance le script depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.constants import (ASSOCIATIONS_PARQUET, COHORT_PARQUET, DRUG_USAGE_PARQUET,
                             PROCESSED_DIR, QUALITY_JSON, RAW_DIR, RESULTS_FILE)
from utils.prep import (aggregate_cohort, aggregate_drug_usage, clean_associations,
                        cohort_log, confounder_names, load_patients, load_raw_results,
                        load_variable_names, pretty_variable)


def top_confounders(assoc, n: int = 20) -> dict:
    """Compte combien d'associations chaque variable confond."""
    confounded = assoc.loc[assoc["robustness"] == "confounded", "confounder_status"]
    names = confounded.map(confounder_names).explode().dropna()
    return names.value_counts().head(n).astype(int).to_dict()


def named_confounders(counts: dict, names: dict) -> list[dict]:
    """Ajoute un nom lisible à chaque code : [{'code', 'name', 'n'}, ...]."""
    return [{"code": c, "name": pretty_variable(c, names), "n": n} for c, n in counts.items()]


def main() -> int:
    if not RESULTS_FILE.exists():
        print("Fichier brut absent : lance d'abord  python scripts/download_data.py", file=sys.stderr)
        return 1
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Associations
    print("[1/3] Nettoyage des associations...")
    assoc, log = clean_associations(load_raw_results(RESULTS_FILE))
    assoc.to_parquet(ASSOCIATIONS_PARQUET, index=False)

    # 2. Cohorte (agrégats seulement)
    print("[2/3] Agrégation de la cohorte...")
    patients = load_patients(RAW_DIR)
    var_names = load_variable_names(RAW_DIR)
    aggregate_cohort(patients).to_parquet(COHORT_PARQUET, index=False)
    usage = aggregate_drug_usage(RAW_DIR, patients)
    usage["name"] = usage["drug_class"].map(lambda c: pretty_variable(f"{c}_C", var_names))
    usage.to_parquet(DRUG_USAGE_PARQUET, index=False)

    # 3. Rapport qualité (lu par la section « Data quality » de l'app)
    print("[3/3] Rapport qualité...")
    top_conf = top_confounders(assoc)
    report = {
        "built_on": date.today().isoformat(),
        "associations": log,
        "cohort": cohort_log(patients),
        "distributions": {
            col: assoc[col].value_counts().astype(int).to_dict()
            for col in ["test", "effector_kind", "feature_class", "feature_space",
                        "robustness", "status_prefix", "group_code"]
        },
        "effect_size_range": [float(assoc["effect_size"].min()), float(assoc["effect_size"].max())],
        # Variables qui « expliquent » le plus souvent une association (associations confondues)
        "top_confounders": top_conf,
        "top_confounders_named": named_confounders(top_conf, var_names),
        # Échantillon des statuts bruts les plus fréquents, pour vérifier la classification
        "raw_status_top25": assoc["confounder_status"].value_counts().head(25).astype(int).to_dict(),
    }
    QUALITY_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Résumé console
    print("\n" + json.dumps(report, indent=2, ensure_ascii=False))
    for f in [ASSOCIATIONS_PARQUET, COHORT_PARQUET, DRUG_USAGE_PARQUET, QUALITY_JSON]:
        print(f"-> {f.relative_to(PROCESSED_DIR.parent.parent)}  ({f.stat().st_size / 1e6:.2f} Mo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
