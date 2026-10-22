"""
Analyses pour la section « Et mon médicament ? » (sans Streamlit : testable seule).

Deux questions, pour un médicament choisi :
1. Son empreinte est-elle plus forte que celle de la maladie ?
   -> on compare le TAUX d'associations robustes (médicament vs maladie),
      puis on regarde les variables touchées par les deux : même sens ou sens opposé.
2. Ses effets viennent-ils du médicament lui-même ou d'autre chose ?
   -> on regarde, parmi ses associations significatives, celles qui résistent
      à l'ajustement (robustes) et, pour les autres, QUI les explique :
      autres médicaments, pays (milieu), profil du patient, mode de vie, maladie.
"""
from __future__ import annotations

import pandas as pd

from utils.prep import confounder_names

ROBUST = ("robust", "no_covariate")
DRUG_TESTS = ("CMD drug intake effect", "Compound (ATC) effect", "Antibiotic courses effect")
KEY = ["feature_space", "feature_id"]

# Catégories de facteurs de confusion (codes des métadonnées MetaCardis)
CONFOUNDER_GROUPS = {
    "disease": {"Status"},
    "environment": {"CENTER_C"},                                  # pays / centre de recrutement
    "patient": {"AGE", "BMI_C", "GENDER"},                        # profil du patient
    "lifestyle": {"SMOKE", "aHEI", "DASH", "DDS", "pa_work_2cl"},  # tabac, alimentation, activité
}                                                                  # tout le reste = autres médicaments


def confounder_group(code: str) -> str:
    for group, codes in CONFOUNDER_GROUPS.items():
        if code in codes:
            return group
    return "other_drugs"


def drug_list(assoc: pd.DataFrame, fdr: float) -> pd.Series:
    """Médicaments disponibles, triés par nombre d'associations significatives."""
    d = assoc[(assoc["effector_kind"] == "drug") & assoc["test"].isin(DRUG_TESTS)
              & (assoc["fdr"] <= fdr)]
    counts = d["effector"].value_counts()
    counts = counts[counts > 0]                       # une colonne « category » garde les absents à 0
    return pd.Series(counts.to_numpy(), index=[str(i) for i in counts.index])


def disease_groups(assoc: pd.DataFrame) -> list[str]:
    """Codes des groupes de patients pour lesquels une comparaison maladie/témoins existe."""
    d = assoc[(assoc["effector_kind"] == "disease") & (assoc["group_code"] != "all")]
    return sorted({str(g) for g in d["group_code"].unique()})


def _one_per_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par variable (on garde l'analyse la plus significative)."""
    return df.sort_values("fdr").drop_duplicates(KEY)


def compare_with_disease(assoc: pd.DataFrame, drug: str, group: str, fdr: float,
                         classes: tuple = ()) -> dict:
    """Empreinte du médicament vs empreinte de la maladie (groupe `group` vs témoins)."""
    base = assoc[assoc["feature_class"].isin(classes)] if classes else assoc
    drug_all = base[(base["effector"] == drug) & base["test"].isin(DRUG_TESTS)]
    dis_all = base[(base["effector_kind"] == "disease") & (base["group_code"] == group)]

    def footprint(rows: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        tested = rows.drop_duplicates(KEY).shape[0]
        kept = _one_per_feature(rows[(rows["fdr"] <= fdr) & rows["robustness"].isin(ROBUST)])
        return kept, tested

    drug_kept, drug_tested = footprint(drug_all)
    dis_kept, dis_tested = footprint(dis_all)
    drug_rate = len(drug_kept) / drug_tested * 100 if drug_tested else 0.0
    dis_rate = len(dis_kept) / dis_tested * 100 if dis_tested else 0.0

    # Variables touchées par les deux : le médicament va-t-il dans le sens de la maladie ?
    both = drug_kept.merge(dis_kept, on=KEY, suffixes=("_drug", "_disease"))
    same = int(((both["effect_size_drug"] > 0) == (both["effect_size_disease"] > 0)).sum())
    opposite = len(both) - same

    if drug_tested == 0 or dis_tested == 0:
        verdict = "unknown"
    elif drug_rate > dis_rate * 1.2:
        verdict = "stronger"
    elif drug_rate < dis_rate * 0.8:
        verdict = "weaker"
    else:
        verdict = "similar"

    return {
        "drug_n": len(drug_kept), "drug_tested": drug_tested, "drug_rate": drug_rate,
        "drug_median_effect": float(drug_kept["abs_effect"].median()) if len(drug_kept) else 0.0,
        "disease_n": len(dis_kept), "disease_tested": dis_tested, "disease_rate": dis_rate,
        "disease_median_effect": float(dis_kept["abs_effect"].median()) if len(dis_kept) else 0.0,
        "shared": len(both), "same_direction": same, "opposite_direction": opposite,
        "shared_table": both, "verdict": verdict,
    }


def explain_origin(assoc: pd.DataFrame, drug: str, fdr: float, classes: tuple = ()) -> dict:
    """
    Parmi les associations significatives du médicament (avant le filtre « robustes »),
    quelle part lui est propre, et qui explique les autres ?
    """
    base = assoc[assoc["feature_class"].isin(classes)] if classes else assoc
    rows = base[(base["effector"] == drug) & base["test"].isin(DRUG_TESTS)
                & (base["fdr"] <= fdr)]
    rows = _one_per_feature(rows)
    total = len(rows)
    if total == 0:
        return {"total": 0, "own": 0, "own_pct": 0.0, "lax": 0, "confounded": 0,
                "by_group": pd.DataFrame(columns=["group", "n", "pct"]), "verdict": "unknown",
                "main_group": None}

    own = int(rows["robustness"].isin(ROBUST).sum())
    lax = int((rows["robustness"] == "lax").sum())
    confounded = rows[rows["robustness"] == "confounded"]

    # Une association peut avoir plusieurs explications : on compte chaque catégorie une fois
    groups = confounded["confounder_status"].map(
        lambda s: sorted({confounder_group(c) for c in confounder_names(s)}))
    by_group = groups.explode().dropna().value_counts().rename_axis("group").reset_index(name="n")
    by_group["pct"] = by_group["n"] / total * 100
    main_group = by_group["group"].iloc[0] if len(by_group) else None

    own_pct = own / total * 100
    if own_pct >= 50:
        verdict = "mostly_drug"
    elif main_group:
        verdict = f"mostly_{main_group}"
    else:
        verdict = "mixed"
    return {"total": total, "own": own, "own_pct": own_pct, "lax": lax,
            "confounded": len(confounded), "by_group": by_group, "verdict": verdict,
            "main_group": main_group}
