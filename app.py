"""
Médicaments, microbiote et métabolisme - un récit de données sur la cohorte MetaCardis.

Lancer :  streamlit run app.py
Structure :
    utils/     chargement (io), nettoyage (prep), filtres, réseau, graphiques, traduction
    sections/  une étape du récit par fichier
"""
import streamlit as st

from sections import conclusions, data_quality, deep_dives, intro, my_drug, network, overview
from sections.common import SECTIONS, Context
from utils.filters import apply_filters, lang_widget_key, sidebar_filters, sync_widget, tested_counts
from utils.i18n import language_selector, t
from utils.io import SOURCE, load_cohort, load_drug_usage, load_quality_report

RENDERERS = {"intro": intro.render, "overview": overview.render, "network": network.render,
             "deep_dives": deep_dives.render, "my_drug": my_drug.render,
             "data_quality": data_quality.render,
             "conclusions": conclusions.render}

st.set_page_config(page_title="MetaCardis · Drugs & microbiome", page_icon="🧬", layout="wide")

# --- Barre latérale : langue, navigation, filtres ------------------------------
language_selector()
# La section active est gardée dans une clé stable (« section ») ; le menu utilise une clé
# propre à la langue pour rester correctement sélectionné quand on change de langue.
st.session_state.setdefault("section", SECTIONS[0])
st.session_state[lang_widget_key("section")] = st.session_state["section"]
st.sidebar.radio(t("nav.label"), SECTIONS, key=lang_widget_key("section"),
                 format_func=lambda s: t(f"nav.{s}"), on_change=sync_widget, args=("section",))
section = st.session_state["section"]
filters = sidebar_filters()

# --- En-tête commun -------------------------------------------------------------
st.title(t("app.title"))
st.caption(t("app.subtitle"))

# --- Données (en cache) puis section choisie -------------------------------------
with st.spinner(t("common.loading")):
    ctx = Context(sig=apply_filters(filters), tested=tested_counts(filters),
                  cohort=load_cohort(), usage=load_drug_usage(),
                  report=load_quality_report(), filters=filters)

RENDERERS[section](ctx)

# --- Pied de page : source, licence, avertissement --------------------------------
st.divider()
st.caption(t("footer.source", **SOURCE) + " " + t("footer.license", **SOURCE))
st.caption(t("footer.disclaimer"))
