"""
Section 5 — Et mon médicament ? (version grand public)

On choisit un médicament et une maladie, et l'app répond en langage simple à deux questions :
1. Le médicament laisse-t-il une empreinte plus forte que la maladie ?
2. Ses effets lui sont-ils propres, ou s'expliquent-ils par autre chose
   (autres médicaments, pays, profil du patient, mode de vie) ?
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import Context, caveat, class_name, header, next_button, table_view
from utils import viz
from utils.analysis import compare_with_disease, disease_groups, drug_list, explain_origin
from utils.constants import GROUP_LABELS
from utils.i18n import fmt_dec, fmt_int, fmt_pct, label, t
from utils.io import load_associations

KEY = "my_drug"
VERDICT_ICON = {"stronger": "🟠", "similar": "🟡", "weaker": "🔵", "unknown": "⚪"}
GROUP_COLORS = {"other_drugs": viz.KIND_COLORS["drug"], "disease": viz.KIND_COLORS["disease"],
                "environment": "#6250D6", "patient": "#898781", "lifestyle": viz.KIND_COLORS["other"]}


def render(ctx: Context) -> None:
    header(KEY)
    st.markdown(t("my_drug.intro"))

    assoc = load_associations()
    fdr, classes = ctx.filters.fdr, ctx.filters.classes
    drugs = drug_list(assoc, fdr)
    groups = disease_groups(assoc)
    if drugs.empty or not groups:
        st.info(t("common.no_data"))
        next_button(KEY)
        return

    # --- Choix du médicament et de la maladie (sur une ligne) ------------------
    c1, c2 = st.columns(2)
    drug = c1.selectbox(t("my_drug.pick_drug"), drugs.index, key="md_drug",
                        format_func=lambda d: f"{d} ({fmt_int(drugs[d])})")
    default = groups.index("3") if "3" in groups else 0          # diabète de type 2 par défaut
    group = c2.selectbox(t("my_drug.pick_disease"), groups, index=default, key="md_group",
                         format_func=lambda g: label(GROUP_LABELS.get(g, {"en": g, "fr": g})))
    disease = label(GROUP_LABELS.get(group, {"en": group, "fr": group}))

    # =========================================================================
    # Question 1 : plus fort que la maladie ?
    # =========================================================================
    st.subheader(t("my_drug.q1", drug=drug, disease=disease))
    cmp = compare_with_disease(assoc, drug, group, fdr, classes)
    v = cmp["verdict"]
    st.markdown(f"#### {VERDICT_ICON[v]} {t(f'my_drug.v1_{v}', drug=drug, disease=disease)}")

    m1, m2, m3 = st.columns(3)
    m1.metric(t("my_drug.m_drug", drug=drug), fmt_pct(cmp["drug_rate"]),
              help=t("my_drug.m_help", n=fmt_int(cmp["drug_n"]), tested=fmt_int(cmp["drug_tested"])))
    m2.metric(t("my_drug.m_disease", disease=disease), fmt_pct(cmp["disease_rate"]),
              help=t("my_drug.m_help", n=fmt_int(cmp["disease_n"]), tested=fmt_int(cmp["disease_tested"])))
    m3.metric(t("my_drug.m_shared"), fmt_int(cmp["shared"]))

    bars = pd.DataFrame({"who": [drug, disease],
                         "rate": [cmp["drug_rate"], cmp["disease_rate"]],
                         "color": [viz.KIND_COLORS["drug"], viz.KIND_COLORS["disease"]]})
    st.plotly_chart(viz.ranked_bars(bars, "who", "rate", "", t("my_drug.chart1_title"),
                                    t("my_drug.chart1_sub"), value_name="%", color_col="color",
                                    value_format=".1f"), width="stretch")

    st.markdown(t("my_drug.strength", drug=drug, d=fmt_dec(cmp["drug_median_effect"], 2),
                  disease=disease, m=fmt_dec(cmp["disease_median_effect"], 2)))
    if cmp["shared"]:
        st.markdown(t("my_drug.shared_text", n=fmt_int(cmp["shared"]), same=fmt_int(cmp["same_direction"]),
                      opp=fmt_int(cmp["opposite_direction"]), drug=drug, disease=disease))
        shared = cmp["shared_table"]
        table_view(pd.DataFrame({
            t("network.col_feature"): shared["feature_drug"],
            t("network.col_class"): [class_name(str(c)) for c in shared["feature_class_drug"]],
            t("my_drug.col_effect_drug"): shared["effect_size_drug"].round(3),
            t("my_drug.col_effect_disease"): shared["effect_size_disease"].round(3),
        }), "drug_vs_disease")

    # =========================================================================
    # Question 2 : le médicament ou autre chose ?
    # =========================================================================
    st.subheader(t("my_drug.q2", drug=drug))
    origin = explain_origin(assoc, drug, fdr, classes)
    if origin["total"] == 0:
        st.info(t("common.no_data"))
    else:
        v2 = origin["verdict"]
        st.markdown(f"#### {t(f'my_drug.v2_{v2}', drug=drug, pct=fmt_pct(origin['own_pct']))}")

        split = pd.DataFrame({
            "row": [drug] * 3,
            "part": ["own", "lax", "confounded"],
            "n": [origin["own"], origin["lax"], origin["confounded"]],
        })
        st.plotly_chart(viz.share_bars(
            split, "row", "part", "n",
            colors={"own": viz.KIND_COLORS["drug"], "lax": "#C3C2B7", "confounded": "#E34948"},
            labels={p: t(f"my_drug.part_{p}") for p in ["own", "lax", "confounded"]},
            title=t("my_drug.chart2_title"), subtitle=t("my_drug.chart2_sub", n=fmt_int(origin["total"]))),
            width="stretch")

        by = origin["by_group"]
        if len(by):
            by = by.assign(label=by["group"].map(lambda g: t(f"my_drug.g_{g}")),
                           color=by["group"].map(GROUP_COLORS))
            st.plotly_chart(viz.ranked_bars(by, "label", "pct", "", t("my_drug.chart3_title"),
                                            t("my_drug.chart3_sub"), value_name="%",
                                            color_col="color", value_format=".1f"), width="stretch")
            st.caption(t("my_drug.overlap_note"))

    with st.expander(t("my_drug.how_title")):
        st.markdown(t("my_drug.how"))
    caveat(t("my_drug.medical"))
    next_button(KEY)
