"""
Éléments partagés par toutes les sections : contexte de données, encadrés, navigation.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils.constants import CLASS_LABELS, EFFECTOR_KIND_LABELS, VARIABLE_FR
from utils.filters import Filters
from utils.i18n import get_lang, label, t

SECTIONS = ["intro", "overview", "network", "deep_dives", "my_drug", "data_quality", "conclusions"]


@dataclass
class Context:
    """Tout ce dont une section a besoin, préparé une seule fois dans app.py."""
    sig: pd.DataFrame          # associations significatives (filtres appliqués)
    tested: pd.DataFrame       # nombre d'associations évaluées par type de facteur
    cohort: pd.DataFrame       # agrégats patients (pays x groupe)
    usage: pd.DataFrame        # % de patients par classe de médicament et groupe
    report: dict               # rapport qualité (scripts/build_processed.py)
    filters: Filters


def header(key: str) -> None:
    """Titre + question à laquelle répond la section."""
    st.header(t(f"{key}.title"))
    st.markdown(f"*{t(f'{key}.question')}*")


def insight(text: str) -> None:
    """Encadré « à retenir » (la phrase clé de la section)."""
    st.info(text, icon="💡")


def caveat(text: str) -> None:
    """Encadré de prudence (limite, biais possible)."""
    st.warning(text, icon="⚠️")


def kind_name(kind: str) -> str:
    return label(EFFECTOR_KIND_LABELS.get(kind, {"en": kind, "fr": kind}))


def class_name(cls: str) -> str:
    return label(CLASS_LABELS.get(cls, {"en": cls, "fr": cls}))


def variable_name(code: str, english_name: str) -> str:
    """Nom d'une variable dans la langue active (traduction FR si disponible)."""
    if get_lang() == "fr" and code in VARIABLE_FR:
        return VARIABLE_FR[code]
    return english_name


def go_to(section: str) -> None:
    """Callback : change de section (utilisé par les boutons « Suivant »)."""
    st.session_state["section"] = section


def next_button(current: str) -> None:
    """Bouton vers la section suivante, en bas de page : guide la lecture du récit."""
    i = SECTIONS.index(current)
    if i + 1 < len(SECTIONS):
        nxt = SECTIONS[i + 1]
        st.divider()
        st.button(f"{t('common.next')} : {t(f'nav.{nxt}')} →", on_click=go_to, args=(nxt,),
                  type="primary")


def table_view(df: pd.DataFrame, key: str) -> None:
    """Version tableau d'un graphique (accessibilité) + téléchargement CSV."""
    with st.expander(t("common.table_view")):
        st.dataframe(df, hide_index=True, width="stretch")
        st.download_button(t("common.download_csv"), df.to_csv(index=False).encode("utf-8"),
                           file_name=f"{key}.csv", mime="text/csv", key=f"dl_{key}")


def legend(kinds: list[str]) -> None:
    """Légende HTML : pastille de couleur + nom (le texte reste en encre neutre)."""
    from utils.viz import KIND_COLORS
    items = [f"<span style='color:{KIND_COLORS[k]};font-size:1.1em'>■</span> {kind_name(k)}"
             for k in kinds]
    st.markdown("&nbsp;&nbsp;·&nbsp;&nbsp;".join(items), unsafe_allow_html=True)


def author_card() -> None:
    """Cadre « carte d'identité » en haut de l'app : logo + auteur + cours."""
    from utils.constants import AUTHOR as a, LOGO_FILE

    def link(text: str, url: str) -> str:
        return f"[{text}]({url})" if url else ""

    line1 = f"**{a['name']}**" + (f" · [{a['email']}](mailto:{a['email']})" if a["email"] else "")
    line2 = " · ".join(x for x in [
        f"**{t('author.program')}:** {a['program']}" if a["program"] else "",
        f"**{t('author.year')}:** {a['year']}" if a["year"] else "",
        f"**{t('author.student_id')}:** {a['student_id']}" if a["student_id"] else "",
        f"**{t('author.group')}:** {a['group']}" if a["group"] else "",
    ] if x)
    line3 = " · ".join(x for x in [link("LinkedIn", a["linkedin"]), link("GitHub", a["github"])] if x)
    line4 = f"**{t('author.course')}:** {a['course']}" if a["course"] else ""
    line5 = (f"**{t('author.professor')}:** {a['professor']}"
             + (f" · [{a['professor_email']}](mailto:{a['professor_email']})" if a["professor_email"] else "")
             if a["professor"] else "")

    with st.container(border=True):
        logo_col, info_col = st.columns([1, 4], vertical_alignment="center")
        with logo_col:
            if LOGO_FILE.exists():
                st.image(str(LOGO_FILE), width="stretch")
            else:   # pas de logo fourni : simple pastille texte
                st.markdown("<div style='font-size:2.2rem;font-weight:800;color:#1F4E79;"
                            "text-align:center'>EFREI</div>", unsafe_allow_html=True)
        with info_col:
            st.markdown("  \n".join(x for x in [line1, line2, line3, line4, line5] if x))
