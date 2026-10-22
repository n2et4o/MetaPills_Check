"""Section 3 — Le réseau d'interactions médicaments -> microbiote / métabolome."""
from __future__ import annotations

import streamlit as st

from sections.common import Context, caveat, class_name, header, insight, next_button, table_view
from utils import viz
from utils.constants import CLASS_LABELS
from utils.i18n import fmt_int, label, t
from utils.network import build_graph, centrality_table, network_edges, shared_features

KEY = "network"


def render(ctx: Context) -> None:
    header(KEY)
    st.markdown(t("network.how_to_read"))

    # Réglages propres au réseau, sur une ligne au-dessus du graphique
    c1, c2 = st.columns(2)
    top_drugs = c1.slider(t("network.top_drugs"), 4, 15, 8, key="net_drugs")
    per_drug = c2.slider(t("network.per_drug"), 3, 20, 10, key="net_per_drug")

    edges = network_edges(ctx.sig, top_drugs=top_drugs, per_drug=per_drug)
    if edges.empty:
        st.info(t("common.no_data"))
        next_button(KEY)
        return
    G = build_graph(edges)

    st.plotly_chart(viz.network_figure(
        G, t("network.chart_title"), t("network.chart_sub"),
        class_labels={k: label(v) for k, v in CLASS_LABELS.items()},
        drug_label=t("network.drug"),
        hover_labels={"linked_drugs": t("network.linked_drugs"),
                      "linked_features": t("network.linked_features")}), width="stretch")

    # --- Indicateurs du réseau -------------------------------------------------
    shared = shared_features(G)
    cent = centrality_table(G)
    drugs = cent[cent["kind"] == "drug"]
    k1, k2, k3 = st.columns(3)
    k1.metric(t("network.kpi_drugs"), fmt_int(len(drugs)))
    k2.metric(t("network.kpi_features"), fmt_int(G.number_of_nodes() - len(drugs)))
    k3.metric(t("network.kpi_shared"), fmt_int(len(shared)))

    if len(shared):
        top = shared.iloc[0]
        insight(t("network.insight_shared", n=fmt_int(len(shared)), feature=top["feature"],
                  k=int(top["n_drugs"]), drugs=top["drugs"]))
    else:
        insight(t("network.insight_none"))

    left, right = st.columns(2)
    with left:
        st.markdown(f"**{t('network.table_shared')}**")
        shown = shared.assign(**{"class": shared["class"].map(class_name)}).rename(columns={
            "feature": t("network.col_feature"), "class": t("network.col_class"),
            "n_drugs": t("network.col_n_drugs"), "drugs": t("network.col_drugs")})
        st.dataframe(shown, hide_index=True, width="stretch", height=280)
    with right:
        st.markdown(f"**{t('network.table_central')}**")
        st.dataframe(drugs[["label", "degree", "betweenness"]].rename(columns={
            "label": t("network.drug"), "degree": t("network.col_degree"),
            "betweenness": t("network.col_betweenness")}),
            hide_index=True, width="stretch", height=280)
        st.caption(t("network.betweenness_help"))

    table_view(edges[["effector", "feature", "feature_class", "effect_size", "fdr", "robustness"]],
               "network_edges")
    caveat(t("network.caveat"))
    next_button(KEY)
