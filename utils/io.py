"""
Chargement des données pré-traitées dans l'app (avec cache Streamlit).
Les fichiers de data/processed/ sont versionnés sur GitHub : l'app démarre
sans téléchargement, en local comme sur Streamlit Community Cloud.
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from utils.constants import (ASSOCIATIONS_PARQUET, COHORT_PARQUET,
                             DRUG_USAGE_PARQUET, QUALITY_JSON)

# --- Source et licence (affichées dans l'app et le README) ----------------------
SOURCE = {
    "title": "Data analysis pipeline for investigating drug-host-microbiome "
             "relationships in cardiometabolic disease (MetaCardis cohort)",
    "authors": "Forslund S.K., Chakaroun R., Zimmermann-Kogadeeva M., Markó L., "
               "Aron-Wisnewsky J., Nielsen T., Birkner T.",
    "version": "1.1.0",
    "doi": "10.5281/zenodo.6242715",
    "url": "https://doi.org/10.5281/zenodo.6242715",
    "license": "CC BY 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "paper": "Forslund et al. (2021), Combinatorial, additive and dose-dependent "
             "drug–microbiome associations, Nature 600, 500–505",
}


def _check(path) -> None:
    """Message clair si les fichiers pré-traités n'ont pas été générés."""
    if not path.exists():
        st.error(
            f"Fichier manquant / missing file : `{path.name}`.\n\n"
            "Lancez / run : `python scripts/download_data.py` puis/then "
            "`python scripts/build_processed.py`"
        )
        st.stop()


def data_version() -> float:
    """
    Date de dernière modification des données pré-traitées.
    Elle fait partie de la clé du cache : si on relance scripts/build_processed.py,
    l'app relit automatiquement les nouveaux fichiers (sinon elle garderait
    en mémoire l'ancienne version tant que le serveur tourne).
    """
    files = [ASSOCIATIONS_PARQUET, COHORT_PARQUET, DRUG_USAGE_PARQUET, QUALITY_JSON]
    return max((f.stat().st_mtime for f in files if f.exists()), default=0.0)


@st.cache_data(show_spinner=False)
def _read_parquet(path: str, version: float) -> pd.DataFrame:
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def _read_json(path: str, version: float) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_associations() -> pd.DataFrame:
    """Toutes les associations nettoyées (maladie/médicament -> variable)."""
    _check(ASSOCIATIONS_PARQUET)
    return _read_parquet(str(ASSOCIATIONS_PARQUET), data_version())


def load_cohort() -> pd.DataFrame:
    """Agrégats de la cohorte par pays x groupe de patients."""
    _check(COHORT_PARQUET)
    return _read_parquet(str(COHORT_PARQUET), data_version())


def load_drug_usage() -> pd.DataFrame:
    """% de patients prenant chaque classe de médicament, par groupe."""
    _check(DRUG_USAGE_PARQUET)
    return _read_parquet(str(DRUG_USAGE_PARQUET), data_version())


def load_quality_report() -> dict:
    """Rapport qualité généré par scripts/build_processed.py."""
    _check(QUALITY_JSON)
    return _read_json(str(QUALITY_JSON), data_version())
