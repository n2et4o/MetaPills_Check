"""Section 6 — Conclusions : ce qu'il faut retenir, implications, limites, suite."""
from __future__ import annotations

import streamlit as st

from sections.common import Context, header, variable_name
from utils.i18n import fmt_int, fmt_pct, t
from utils.io import SOURCE

KEY = "conclusions"


def render(ctx: Context) -> None:
    header(KEY)
    dist = ctx.report["distributions"]["robustness"]
    total = sum(dist.values())
    pct_conf = dist.get("confounded", 0) / total * 100 if total else 0

    named = ctx.report.get("top_confounders_named", [])
    first = variable_name(named[0]["code"], named[0]["name"]) if named else "—"

    drugs = ctx.sig[ctx.sig["effector_kind"] == "drug"]
    top_drug = drugs["effector"].value_counts().index[0] if len(drugs) else "—"

    # --- 3 messages clés, calculés à partir des données (pas écrits en dur) ------
    st.subheader(t("conclusions.key_title"))
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric(t("conclusions.k1_label"), fmt_pct(pct_conf))
        st.markdown(t("conclusions.k1_text"))
    with k2:
        st.metric(t("conclusions.k2_label"), first)
        st.markdown(t("conclusions.k2_text"))
    with k3:
        st.metric(t("conclusions.k3_label"), str(top_drug))
        st.markdown(t("conclusions.k3_text", n=fmt_int(int((drugs["effector"] == top_drug).sum()))))

    st.subheader(t("conclusions.implications_title"))
    st.markdown(t("conclusions.implications"))

    st.subheader(t("conclusions.limits_title"))
    st.markdown(t("conclusions.limits"))

    st.subheader(t("conclusions.next_title"))
    st.markdown(t("conclusions.next"))

    st.subheader(t("conclusions.credits_title"))
    st.markdown(t("conclusions.credits", **SOURCE))
