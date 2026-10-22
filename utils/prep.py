"""
Nettoyage, validation et feature engineering.

Ce module n'importe PAS streamlit : il est utilisé hors de l'app par
scripts/build_processed.py, qui produit les fichiers de data/processed/.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from utils.constants import MIN_CELL_SIZE, POLYPHARMACY_MIN

# Codes de statut (en majuscules) trouvés dans « Confounder status »
STRICT_CODES = {"SD", "OK_SD", "OK"}
NO_COVARIATE_CODES = {"NC", "OK_NC"}
LAX_CODES = {"LD"}
AMBIGUOUS_CODES = {"AD", "OK_D"}
NS_CODES = {"NS"}

# Colonnes d'origine -> noms courts en snake_case
RENAME = {
    "Effector": "effector",
    "Effector ID": "effector_id",
    "Test": "test",
    "Sample set": "sample_set",
    "Feature space": "feature_space",
    "Feature class": "feature_class",
    "Feature display name": "feature",
    "Feature ID": "feature_id",
    "FDR": "fdr",
    "Effect size": "effect_size",
    "Confounder status": "confounder_status",
}
KEY = ["test", "effector_id", "sample_set", "feature_space", "feature_id"]   # identifie une association
ATC_REGEX = r"^[A-Z]\d{2}[A-Z]{2}\d{2}$"                     # ex. A10BA02 (metformine)


# =============================================================================
# 1. Associations médicament / maladie -> variable (microbiome, métabolome...)
# =============================================================================
def load_raw_results(path: Path) -> pd.DataFrame:
    """Lit le fichier TSV brut de Zenodo."""
    return pd.read_csv(path, sep="\t", low_memory=False)


def clean_associations(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Nettoie le fichier de résultats et renvoie (table propre, journal des étapes)."""
    log: dict = {"raw_rows": int(len(raw)), "raw_columns": int(raw.shape[1])}

    # Valeurs manquantes AVANT nettoyage (pour la section qualité)
    log["missing_pct_raw"] = (raw.isna().mean() * 100).round(1).to_dict()

    # a) Colonnes requises présentes ?
    missing_cols = sorted(set(RENAME) - set(raw.columns))
    if missing_cols:
        raise ValueError(f"Colonnes attendues absentes : {missing_cols}")

    # b) Doublons exacts
    log["exact_duplicates"] = int(raw.duplicated().sum())
    df = raw.drop_duplicates()

    # c) On garde les colonnes utiles. Les colonnes « Comparison ... » sont vides
    #    à 63 % (elles ne concernent qu'un sous-ensemble de tests) : on les retire.
    log["dropped_columns"] = [c for c in raw.columns if c not in RENAME]
    df = df[list(RENAME)].rename(columns=RENAME)

    # d) Types et nettoyage des textes
    df["fdr"] = pd.to_numeric(df["fdr"], errors="coerce")
    df["effect_size"] = pd.to_numeric(df["effect_size"], errors="coerce")
    text_cols = [c for c in df.columns if c not in ("fdr", "effect_size")]
    for c in text_cols:
        df[c] = df[c].astype(str).str.strip()

    # e) Contrôles de validité : FDR dans [0, 1], effet fini.
    #    On compte chaque motif séparément pour pouvoir l'expliquer dans l'app.
    checks = {
        "fdr_missing": df["fdr"].isna(),
        "fdr_out_of_range": df["fdr"].notna() & ~df["fdr"].between(0, 1),
        "effect_missing": df["effect_size"].isna(),
        "effect_infinite": df["effect_size"].notna() & ~np.isfinite(df["effect_size"]),
    }
    log["invalid_reasons"] = {k: int(v.sum()) for k, v in checks.items()}
    invalid = pd.concat(checks, axis=1).any(axis=1)
    log["invalid_rows_removed"] = int(invalid.sum())
    df = df[~invalid]

    # f) Doublons sur la clé (même test, même effecteur, même variable) :
    #    on garde le résultat le plus significatif (FDR minimal).
    log["key_duplicates"] = int(df.duplicated(KEY).sum())
    df = df.sort_values("fdr").drop_duplicates(KEY, keep="first")

    df = add_features(df)
    log["clean_rows"] = int(len(df))
    return df.reset_index(drop=True), log


def _first_token(status: str) -> str:
    """Premier mot du statut, ex. 'CENTER_C, AGE' -> 'CENTER_C' ; 'LD' -> 'LD'."""
    tokens = re.split(r"[,;:\s]+", str(status).strip())
    return tokens[0] if tokens and tokens[0] else ""


def classify_status(status: str) -> str:
    """
    Traduit la colonne « Confounder status » en catégorie de robustesse.

    Le fichier contient soit un code de statut (SD, LD, OK, NC, AD, NS),
    soit la LISTE des variables qui expliquent l'association
    (ex. 'CENTER_C', 'METFORMIN_C, Status', 'A10BA02') -> « confondue ».
    """
    token = _first_token(status).upper()
    if token in STRICT_CODES:
        return "robust"        # résiste à tous les facteurs de confusion testés
    if token in NO_COVARIATE_CODES:
        return "no_covariate"  # aucun autre facteur à tester : robuste par défaut
    if token in LAX_CODES:
        return "lax"           # déconfondue de façon permissive
    if token in AMBIGUOUS_CODES:
        return "ambiguous"
    if token in NS_CODES:
        return "not_significant"
    return "confounded"        # le statut liste les variables responsables


def confounder_names(status: str) -> list[str]:
    """Pour une association confondue : liste des variables responsables."""
    if classify_status(status) != "confounded":
        return []
    return [t for t in re.split(r"[,;:\s]+", str(status).strip()) if t]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les variables dérivées utilisées par les graphiques."""
    df = df.copy()

    # Type d'effecteur, d'après les 7 valeurs réelles de « Test » :
    #   Group contrast -> maladie ; Drug combination / CMD drug dosage / CMD drug intake /
    #   Compound (ATC) / Antibiotic courses -> médicament ; Other effect -> autres facteurs
    test_lower = df["test"].str.lower()
    df["effector_kind"] = np.select(
        [test_lower.eq("group contrast"),
         test_lower.str.contains("drug|antibiot|dosage|combination|atc")],
        ["disease", "drug"],
        default="other",
    )

    # Statut de déconfusion -> 5 catégories lisibles (voir classify_status)
    df["status_prefix"] = df["confounder_status"].map(_first_token)
    df["robustness"] = df["confounder_status"].map(classify_status)

    # Groupe de patients : code entre parenthèses en fin de texte, ex. « Controls (8) vs MetS (1) » -> 1
    df["group_code"] = df["sample_set"].str.extract(r"\(([0-9][ab]?)\)\s*$", expand=False).fillna("all")

    # Classe ATC (1re lettre) quand l'identifiant est un code ATC valide
    is_atc = df["effector_id"].str.match(ATC_REGEX)
    df["atc_level1"] = np.where(is_atc, df["effector_id"].str[0], "")

    # Direction et intensité de l'effet
    df["direction"] = np.where(df["effect_size"] >= 0, "increase", "decrease")
    df["abs_effect"] = df["effect_size"].abs()
    df["neg_log10_fdr"] = -np.log10(df["fdr"].clip(lower=1e-300))

    # Types catégoriels : fichier parquet beaucoup plus léger, filtres plus rapides
    for c in ["effector", "effector_id", "test", "sample_set", "feature_space",
              "feature_class", "effector_kind", "status_prefix", "robustness",
              "group_code", "atc_level1", "direction"]:
        df[c] = df[c].astype("category")
    return df


# =============================================================================
# 2. Cohorte (métadonnées patients) -> UNIQUEMENT des agrégats
# =============================================================================
def _find(raw_dir: Path, pattern: str) -> Path:
    """Trouve un fichier dans data/raw/ (les archives créent des sous-dossiers)."""
    matches = sorted(raw_dir.rglob(pattern))
    if not matches:
        raise FileNotFoundError(f"Aucun fichier '{pattern}' dans {raw_dir}")
    return matches[0]


def _read_meta(path: Path) -> pd.DataFrame:
    """Lit un fichier de métadonnées (format R : tabulations, index de lignes)."""
    df = pd.read_csv(path, sep="\t", dtype={"PATGROUPFINAL_C": str})
    return df.reset_index(drop=True)


def load_patients(raw_dir: Path) -> pd.DataFrame:
    """Jointure démographie + médicaments par patient (SampleID). Reste en mémoire, jamais exportée."""
    demo = _read_meta(_find(raw_dir, "demographic_*.r"))
    atcs = _read_meta(_find(raw_dir, "cmd_atcs_*.r"))

    drug_cols = [c for c in atcs.columns if c != "SampleID"]
    atcs["n_drugs"] = atcs[drug_cols].apply(pd.to_numeric, errors="coerce").gt(0).sum(axis=1)

    patients = demo.merge(atcs[["SampleID", "n_drugs"]], on="SampleID", how="left", validate="1:1")
    patients = patients.rename(columns={"PATGROUPFINAL_C": "group_code", "CENTER_C": "country",
                                        "AGE": "age", "BMI_C": "bmi"})
    patients["group_code"] = patients["group_code"].astype(str).str.strip()
    patients["age"] = pd.to_numeric(patients["age"], errors="coerce")
    patients["bmi"] = pd.to_numeric(patients["bmi"], errors="coerce")
    return patients


def aggregate_cohort(patients: pd.DataFrame) -> pd.DataFrame:
    """Agrège par pays x groupe. Les cellules < MIN_CELL_SIZE patients sont supprimées."""
    agg = (patients.groupby(["country", "group_code"], observed=True)
           .agg(n_patients=("SampleID", "size"),
                age_mean=("age", "mean"),
                bmi_mean=("bmi", "mean"),
                drugs_mean=("n_drugs", "mean"),
                polypharmacy_pct=("n_drugs", lambda s: (s >= POLYPHARMACY_MIN).mean() * 100))
           .reset_index())
    agg = agg[agg["n_patients"] >= MIN_CELL_SIZE]
    return agg.round(2).reset_index(drop=True)


def aggregate_drug_usage(raw_dir: Path, patients: pd.DataFrame) -> pd.DataFrame:
    """% de patients prenant chaque classe de médicament, par groupe de patients."""
    drugs = _read_meta(_find(raw_dir, "cmd_drugs_*.r"))
    classes = [c for c in drugs.columns if c != "SampleID"]
    drugs[classes] = drugs[classes].apply(pd.to_numeric, errors="coerce")

    merged = patients[["SampleID", "group_code"]].merge(drugs, on="SampleID", how="inner")
    sizes = merged.groupby("group_code").size()
    valid_groups = sizes[sizes >= MIN_CELL_SIZE].index

    usage = (merged[merged["group_code"].isin(valid_groups)]
             .groupby("group_code")[classes].mean().mul(100)
             .reset_index()
             .melt(id_vars="group_code", var_name="drug_class", value_name="pct_patients"))
    usage["drug_class"] = usage["drug_class"].str.removesuffix("_C")
    # On ne garde que les classes prises par au moins 1 % d'un groupe
    keep = usage.groupby("drug_class")["pct_patients"].transform("max") >= 1
    return usage[keep].round(2).reset_index(drop=True)


def cohort_log(patients: pd.DataFrame) -> dict:
    """Indicateurs qualité sur les métadonnées (sans donnée individuelle)."""
    return {
        "patients": int(len(patients)),
        "duplicate_sample_ids": int(patients["SampleID"].duplicated().sum()),
        "countries": patients["country"].value_counts(dropna=False).to_dict(),
        # Valeurs manquantes par pays : montre si elles sont concentrées (ex. Danemark)
        "missing_pct_by_country": (patients.groupby("country")[["age", "bmi"]]
                                   .apply(lambda g: g.isna().mean().mul(100).round(1))
                                   .to_dict(orient="index")),
        "missing_pct": (patients[["age", "bmi", "group_code", "country", "n_drugs"]]
                        .isna().mean().mul(100).round(1).to_dict()),
    }


# =============================================================================
# 3. Noms lisibles des variables (pour les graphiques)
# =============================================================================
def load_variable_names(raw_dir: Path) -> dict[str, str]:
    """
    Code -> nom lisible (anglais), d'après les fichiers officiels du dépôt :
    feature_names/metadata_names (ex. CENTER_C -> Country of recruitment)
    et feature_names/atcs_names (ex. A10BA02 -> metformin).
    """
    names: dict[str, str] = {}
    for pattern in ["metadata_names", "atcs_names"]:
        try:
            path = _find(raw_dir, pattern)
        except FileNotFoundError:
            continue
        table = pd.read_csv(path, sep="\t", header=None, dtype=str, usecols=[0, 1],
                            names=["code", "name"], on_bad_lines="skip")
        table = table.dropna()
        table = table[table["code"] != "Variable ID"]          # ligne d'en-tête éventuelle
        names.update(dict(zip(table["code"].str.strip(), table["name"].str.strip())))
    return names


def pretty_variable(code: str, names: dict[str, str]) -> str:
    """
    Transforme un code en nom lisible :
    'METFORMIN_C' -> 'Metformin' ; 'DOSAGE_STATINE_C' -> 'Statins (dosage)' ;
    'COMB_METFORMIN_C_STATINE_C' -> 'Metformin + Statins'.
    """
    if code in names:
        return names[code]
    if code.startswith("DOSAGE_"):
        return f"{pretty_variable(code.removeprefix('DOSAGE_'), names)} (dosage)"
    if code.startswith("COMB_"):
        parts = [p for p in code.removeprefix("COMB_").split("_C_") if p]
        parts = [p if p.endswith("_C") else p + "_C" for p in parts]
        return " + ".join(pretty_variable(p, names) for p in parts)
    return code.removesuffix("_C").replace("_", " ").capitalize()
