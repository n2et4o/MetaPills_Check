"""Section 1 — Pourquoi c'est important : accroche, public, questions, cohorte."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import Context, caveat, header, insight, next_button, table_view, variable_name
from utils import viz
from utils.constants import COUNTRY_LABELS, GROUP_LABELS
from utils.i18n import fmt_dec, fmt_int, label, t

KEY = "intro"


def render(ctx: Context) -> None:
    header(KEY)

    # --- Accroche + public + questions -----------------------------------------
    st.markdown(f"### {t('intro.hook')}")
    st.markdown(t("intro.context"))
    a, b = st.columns(2)
    with a:
        st.markdown(f"**{t('intro.audience_title')}**")
        st.markdown(t("intro.audience"))
    with b:
        st.markdown(f"**{t('intro.questions_title')}**")
        st.markdown(t("intro.questions"))

    # --- Vulgarisation : les mots clés expliqués simplement ---------------------
    with st.expander(t("intro.glossary_title")):
        st.markdown(t("intro.glossary"))

    # --- Chiffres clés de la cohorte -------------------------------------------
    cohort_log = ctx.report["cohort"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("intro.kpi_patients"), fmt_int(cohort_log["patients"]))
    k2.metric(t("intro.kpi_countries"), fmt_int(len(cohort_log["countries"])))
    k3.metric(t("intro.kpi_tested"), fmt_int(ctx.report["associations"]["clean_rows"]))
    poly = _weighted(ctx.cohort, "drugs_mean")
    k4.metric(t("intro.kpi_drugs"), fmt_dec(poly))

    # --- Carte + nombre moyen de médicaments par groupe -------------------------
    left, right = st.columns(2)
    with left:
        # Totaux par pays (agrégats du rapport qualité : aucune donnée individuelle)
        by_country = pd.DataFrame(list(cohort_log["countries"].items()),
                                  columns=["country", "n_patients"])
        st.plotly_chart(viz.country_map(
            by_country, "country", "n_patients", t("intro.map_title"), t("intro.map_sub"),
            t("intro.patients"), names={k: label(v) for k, v in COUNTRY_LABELS.items()}),
            width="stretch")
    with right:
        per_group = _per_group(ctx.cohort)
        st.plotly_chart(viz.ranked_bars(
            per_group, "group", "drugs_mean", viz.KIND_COLORS["drug"],
            t("intro.drugs_title"), t("intro.drugs_sub"), value_name=t("intro.drugs_axis"),
            highlight={per_group.loc[per_group["drugs_mean"].idxmax(), "group"]},
            value_format=".1f"), width="stretch")
        table_view(per_group, "drugs_per_group")

    top = per_group.loc[per_group["drugs_mean"].idxmax()]
    ctrl = per_group[per_group["code"] == "8"]
    if len(ctrl):
        insight(t("intro.insight_drugs", group=top["group"], n=fmt_dec(top["drugs_mean"]),
                  ctrl=fmt_dec(ctrl["drugs_mean"].iloc[0])))

    # --- Quels médicaments, dans quels groupes ? --------------------------------
    usage = ctx.usage.copy()
    if "name" not in usage:                       # fichier généré par une ancienne version
        usage["name"] = usage["drug_class"].str.capitalize()
    usage["name"] = [variable_name(f"{c}_C", n) for c, n in zip(usage["drug_class"], usage["name"])]
    usage["group"] = usage["group_code"].map(lambda g: label(GROUP_LABELS.get(g, {"en": g, "fr": g})))
    top_classes = (usage.groupby("name")["pct_patients"].max().nlargest(12).index)
    matrix = (usage[usage["name"].isin(top_classes)]
              .pivot_table(index="name", columns="group", values="pct_patients"))
    order = [label(GROUP_LABELS[g]) for g in GROUP_LABELS if label(GROUP_LABELS[g]) in matrix.columns]
    matrix = matrix[order].loc[matrix.max(axis=1).sort_values(ascending=False).index]
    st.plotly_chart(viz.heatmap(matrix, t("intro.usage_title"), t("intro.usage_sub"),
                                value_name="%", value_format=".0f"), width="stretch")
    table_view(matrix.round(1).reset_index(), "drug_usage")

    caveat(t("intro.caveat_denmark"))
    next_button(KEY)


def _weighted(cohort: pd.DataFrame, col: str) -> float:
    """Moyenne pondérée par le nombre de patients (cellules sans valeur ignorées)."""
    d = cohort.dropna(subset=[col])
    return float((d[col] * d["n_patients"]).sum() / d["n_patients"].sum()) if len(d) else 0.0


def _per_group(cohort: pd.DataFrame) -> pd.DataFrame:
    """Nombre moyen de médicaments par groupe de patients (tous pays confondus)."""
    rows = []
    for code, g in cohort.groupby("group_code"):
        rows.append({"code": code,
                     "group": label(GROUP_LABELS.get(code, {"en": code, "fr": code})),
                     "n_patients": int(g["n_patients"].sum()),
                     "drugs_mean": round(_weighted(g, "drugs_mean"), 2)})
    return pd.DataFrame(rows)
