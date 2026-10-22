"""
Filtres globaux (barre latérale) appliqués à toutes les sections.

Le filtrage est mis en cache : Streamlit relance le script à chaque clic,
mais une combinaison de filtres déjà vue est servie instantanément.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils.constants import CLASS_LABELS, FDR_DEFAULT, GROUP_LABELS
from utils.i18n import get_lang, label, t
from utils.io import data_version, load_associations

FDR_OPTIONS = [0.001, 0.01, 0.05, 0.1]
ROBUST = ("robust", "no_covariate")
DEFAULTS = {"f_fdr": FDR_DEFAULT, "f_robust": True,
            "f_classes": list(CLASS_LABELS), "f_group": "any"}


@dataclass(frozen=True)
class Filters:
    fdr: float
    robust_only: bool
    classes: tuple
    group: str          # "any" = toutes les analyses, "all" = analyses poolées, sinon code du groupe


def lang_widget_key(base: str) -> str:
    """
    Clé de widget propre à la langue (ex. 'f_classes__en').
    Pourquoi : quand les libellés d'un menu changent de langue, Streamlit peut perdre
    la sélection. On garde donc la vraie valeur dans une clé stable (`base`)
    et on la recopie dans le widget de la langue active à chaque exécution.
    """
    return f"{base}__{get_lang()}"


def sync_widget(base: str) -> None:
    """Callback : recopie la valeur du widget dans la clé stable."""
    st.session_state[base] = st.session_state[lang_widget_key(base)]


def _reset() -> None:
    """Callback du bouton « Réinitialiser » : remet les valeurs par défaut."""
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def sidebar_filters() -> Filters:
    """Dessine les filtres dans la barre latérale et renvoie leurs valeurs."""
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)

    st.sidebar.header(t("sidebar.filters"))
    with st.sidebar.expander(t("sidebar.help_title")):
        st.markdown(t("sidebar.help"))
    fdr = st.sidebar.select_slider(t("sidebar.fdr"), options=FDR_OPTIONS, key="f_fdr",
                                   help=t("sidebar.fdr_help"))
    robust = st.sidebar.toggle(t("sidebar.robust_only"), key="f_robust",
                               help=t("sidebar.robust_only_help"))
    st.session_state[lang_widget_key("f_classes")] = st.session_state["f_classes"]
    st.sidebar.multiselect(t("sidebar.feature_class"), options=list(CLASS_LABELS),
                           format_func=lambda c: label(CLASS_LABELS[c]),
                           key=lang_widget_key("f_classes"), on_change=sync_widget, args=("f_classes",),
                           placeholder=t("sidebar.choose"))

    groups = ["any", "all"] + [g for g in GROUP_LABELS if g in _available_groups()]
    st.session_state[lang_widget_key("f_group")] = st.session_state["f_group"]
    st.sidebar.selectbox(t("sidebar.group"), options=groups, key=lang_widget_key("f_group"),
                         on_change=sync_widget, args=("f_group",), format_func=group_name,
                         help=t("sidebar.group_help"))
    classes, group = st.session_state["f_classes"], st.session_state["f_group"]
    st.sidebar.button(t("sidebar.reset"), on_click=_reset, width="stretch")
    return Filters(fdr, robust, tuple(classes), group)


def group_name(code: str) -> str:
    """Libellé traduit d'un code de groupe."""
    if code == "any":
        return t("sidebar.group_any")
    if code == "all":
        return t("sidebar.group_pooled")
    return label(GROUP_LABELS.get(code, {"en": code, "fr": code}))


def _available_groups() -> set:
    return _groups(data_version())


@st.cache_data(show_spinner=False)
def _groups(version: float) -> set:
    return {str(g) for g in load_associations()["group_code"].unique()}


def apply_filters(f: Filters) -> pd.DataFrame:
    """Associations significatives correspondant aux filtres."""
    return _apply(f, data_version())


@st.cache_data(show_spinner=False, max_entries=32)
def _apply(f: Filters, version: float) -> pd.DataFrame:
    df = load_associations()
    mask = df["fdr"] <= f.fdr
    if f.robust_only:
        mask &= df["robustness"].isin(ROBUST)
    if f.classes:
        mask &= df["feature_class"].isin(f.classes)
    if f.group != "any":
        mask &= df["group_code"] == f.group      # comparaison directe, sans conversion en texte
    return df[mask]


def tested_counts(f: Filters) -> pd.DataFrame:
    """Voir _tested (mis en cache avec la version des données)."""
    return _tested(f, data_version())


@st.cache_data(show_spinner=False, max_entries=32)
def _tested(f: Filters, version: float) -> pd.DataFrame:
    """
    Nombre d'associations TESTÉES par type de facteur (avant le seuil FDR),
    avec les mêmes filtres de variables et de groupe : sert de dénominateur
    pour comparer équitablement médicaments, maladie et autres facteurs.
    """
    df = load_associations()
    mask = pd.Series(True, index=df.index)
    if f.classes:
        mask &= df["feature_class"].isin(f.classes)
    if f.group != "any":
        mask &= df["group_code"] == f.group      # comparaison directe, sans conversion en texte
    return df[mask].groupby("effector_kind", observed=True).size().rename("tested").reset_index()
