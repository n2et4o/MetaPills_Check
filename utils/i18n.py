"""
Traduction de l'interface (français / anglais).

Usage dans n'importe quel fichier :
    from utils.i18n import t, label
    st.title(t("intro.title"))
    st.write(t("intro.kpi_patients", n=fmt_int(2173)))
    st.write(label(GROUP_LABELS["3"]))      # dictionnaires {"fr": ..., "en": ...} de constants.py
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import streamlit as st

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
LANGS = {"fr": "🇫🇷 Français", "en": "🇬🇧 English"}
DEFAULT_LANG = "fr"


@lru_cache(maxsize=None)
def _catalog(lang: str) -> dict:
    """Charge locales/<lang>.json une seule fois (cache en mémoire)."""
    return json.loads((LOCALES_DIR / f"{lang}.json").read_text(encoding="utf-8"))


def _lookup(catalog: dict, key: str):
    """Cherche une clé à points, ex. 'sidebar.filters' -> catalog['sidebar']['filters']."""
    node = catalog
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def get_lang() -> str:
    """Langue active, stockée dans la session (par défaut : français)."""
    return st.session_state.get("lang", DEFAULT_LANG)


def t(key: str, **kwargs) -> str:
    """
    Renvoie le texte traduit. Si la clé manque dans la langue active,
    on essaie l'anglais, puis on affiche la clé elle-même (repérable à l'écran).
    Les {variables} du texte sont remplacées par kwargs.
    """
    text = _lookup(_catalog(get_lang()), key)
    if text is None:
        text = _lookup(_catalog("en"), key)
    if text is None:
        return f"⟦{key}⟧"
    return text.format(**kwargs) if kwargs else text


def label(mapping: dict) -> str:
    """Choisit la bonne langue dans un dictionnaire {'fr': ..., 'en': ...}."""
    return mapping.get(get_lang(), mapping.get("en", ""))


def language_selector() -> None:
    """
    Bouton de langue dans la barre latérale.
    La langue est aussi écrite dans l'URL (?lang=en) : un lien partagé garde la langue.
    """
    if "lang" not in st.session_state:
        from_url = st.query_params.get("lang", DEFAULT_LANG)
        st.session_state["lang"] = from_url if from_url in LANGS else DEFAULT_LANG

    # Un bouton radio a toujours une valeur (contrairement à un segmented_control
    # qu'on peut désélectionner) : pas de cas « aucune langue ».
    st.sidebar.radio(
        t("sidebar.language"),
        options=list(LANGS),
        format_func=LANGS.get,
        key="lang",
        horizontal=True,
    )
    st.query_params["lang"] = st.session_state["lang"]


# --- Formatage des nombres selon la langue -------------------------------------
def fmt_int(n: float) -> str:
    """2173 -> '2 173' (fr) ou '2,173' (en)."""
    s = f"{int(round(n)):,}"
    return s.replace(",", " ") if get_lang() == "fr" else s


def fmt_pct(x: float, decimals: int = 1) -> str:
    """56.64 -> '56,6 %' (fr) ou '56.6%' (en)."""
    s = f"{x:.{decimals}f}"
    return f"{s.replace('.', ',')} %" if get_lang() == "fr" else f"{s}%"


def fmt_dec(x: float, decimals: int = 1) -> str:
    """4.27 -> '4,3' (fr) ou '4.3' (en)."""
    s = f"{x:.{decimals}f}"
    return s.replace(".", ",") if get_lang() == "fr" else s
