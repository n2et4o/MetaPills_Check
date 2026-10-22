"""Section 2 — Vue d'ensemble : les médicaments pèsent-ils plus que la maladie ?"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import (Context, class_name, header, insight, kind_name, legend,
                             next_button, table_view)
from utils import viz
from utils.i18n import fmt_int, fmt_pct, t

KEY = "overview"
KINDS = ["drug", "disease", "other"]


def render(ctx: Context) -> None:
    header(KEY)
    if ctx.sig.empty:
        st.info(t("common.no_data"))
        next_button(KEY)
        return

    # --- 1. Comparaison équitable : taux d'associations retenues par type de facteur ---
    summary = _summary(ctx)
    cols = st.columns(len(summary))
    for col, row in zip(cols, summary.itertuples()):
        col.metric(kind_name(row.kind), fmt_int(row.significant),
                   help=t("overview.kpi_help", tested=fmt_int(row.tested)))
        col.caption(t("overview.kpi_rate", rate=fmt_pct(row.rate)))

    rate_df = summary.assign(label=summary["kind"].map(kind_name),
                             color=summary["kind"].map(viz.KIND_COLORS))
    st.plotly_chart(viz.ranked_bars(
        rate_df, "label", "rate", "", t("overview.rate_title"), t("overview.rate_sub"),
        value_name=t("overview.rate_axis"), color_col="color", value_format=".1f"),
        width="stretch")
    table_view(summary, "rates_by_factor")

    by_kind = summary.set_index("kind")
    if {"drug", "disease"} <= set(by_kind.index):
        d, m = by_kind.loc["drug"], by_kind.loc["disease"]
        insight(t("overview.insight_count", drug=fmt_int(d.significant),
                  disease=fmt_int(m.significant), drug_rate=fmt_pct(d.rate),
                  disease_rate=fmt_pct(m.rate)))
        st.caption(t("overview.fair_note"))

    # --- 2. Quels facteurs ont le plus d'effets ? --------------------------------
    n_top = st.slider(t("sidebar.top_n"), 5, 25, 12, key="ov_top")
    top = (ctx.sig.groupby(["effector", "effector_kind"], observed=True).size()
           .rename("n").reset_index().nlargest(n_top, "n"))
    top["color"] = top["effector_kind"].map(viz.KIND_COLORS)
    st.plotly_chart(viz.ranked_bars(
        top, "effector", "n", "", t("overview.top_title"), t("overview.top_sub"),
        value_name=t("overview.n_assoc"), color_col="color"), width="stretch")
    legend(KINDS)
    table_view(top.drop(columns="color"), "top_factors")

    # --- 3. Que touchent-ils ? (microbiote ou métabolome) -----------------------
    comp = (ctx.sig.groupby(["effector_kind", "feature_class"], observed=True).size()
            .rename("n").reset_index())
    comp["effector_kind"] = comp["effector_kind"].map(kind_name)
    st.plotly_chart(viz.share_bars(
        comp, "effector_kind", "feature_class", "n", colors=viz.CLASS_COLORS,
        labels={c: class_name(c) for c in viz.CLASS_COLORS},
        title=t("overview.comp_title"), subtitle=t("overview.comp_sub")), width="stretch")

    # Part du microbiote parmi les effets des médicaments
    drug_comp = ctx.sig[ctx.sig["effector_kind"] == "drug"]["feature_class"].value_counts(normalize=True)
    micro = sum(drug_comp.get(c, 0) for c in ["Microbiome taxonomy", "Microbiome function"]) * 100
    insight(t("overview.insight_micro", pct=fmt_pct(micro)))
    next_button(KEY)


def _summary(ctx: Context) -> pd.DataFrame:
    """Par type de facteur : associations évaluées, retenues, et taux."""
    sig = ctx.sig.groupby("effector_kind", observed=True).size().rename("significant")
    df = ctx.tested.set_index("effector_kind").join(sig, how="left").fillna(0).reset_index()
    df = df.rename(columns={"effector_kind": "kind"})
    df["significant"] = df["significant"].astype(int)
    df["rate"] = (df["significant"] / df["tested"].clip(lower=1) * 100).round(2)
    df["kind"] = [str(k) for k in df["kind"]]
    return df.set_index("kind").reindex([k for k in KINDS if k in set(df["kind"])]).reset_index()
