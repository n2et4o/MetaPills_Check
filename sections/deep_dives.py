"""Section 4 — Analyses détaillées : un médicament à la loupe, carte de chaleur, facteurs de confusion."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import Context, caveat, header, insight, next_button, table_view, variable_name
from utils import viz
from utils.i18n import fmt_int, t

KEY = "deep_dives"


def render(ctx: Context) -> None:
    header(KEY)
    drugs_sig = ctx.sig[ctx.sig["effector_kind"] == "drug"]
    if drugs_sig.empty:
        st.info(t("common.no_data"))
        next_button(KEY)
        return

    tab1, tab2, tab3 = st.tabs([t("deep_dives.tab_drug"), t("deep_dives.tab_heatmap"),
                                t("deep_dives.tab_confounders")])

    # --- Onglet 1 : un médicament à la loupe -----------------------------------
    with tab1:
        counts = drugs_sig["effector"].value_counts()
        counts = counts[counts > 0]
        ranking = pd.Series(counts.to_numpy(), index=[str(i) for i in counts.index])
        drug = st.selectbox(t("deep_dives.pick_drug"), list(ranking.index),
                            format_func=lambda d: f"{d} ({fmt_int(ranking[d])})", key="dd_drug")
        d = drugs_sig[drugs_sig["effector"] == drug]

        st.plotly_chart(viz.volcano(d, ctx.filters.fdr, t("deep_dives.volcano_title", drug=drug),
                                    t("deep_dives.volcano_sub"), labels=_volcano_labels(ctx)),
                        width="stretch")

        # Les 10 plus fortes hausses et baisses
        strongest = pd.concat([d.nlargest(10, "effect_size"), d.nsmallest(10, "effect_size")])
        strongest = strongest.drop_duplicates(["feature_space", "feature_id"])
        # Deux variables de familles différentes peuvent avoir le même nom : on précise la famille
        name = pd.Series([str(x)[:40] for x in strongest["feature"]], index=strongest.index)
        space = pd.Series([str(x) for x in strongest["feature_space"]], index=strongest.index)
        dup = name.duplicated(keep=False)
        strongest = strongest.assign(label=name.where(~dup, name + " (" + space + ")"))
        st.plotly_chart(viz.diverging_bars(
            strongest, "label", "effect_size", t("deep_dives.top_title", drug=drug),
            t("deep_dives.top_sub"), labels={"effect": t("deep_dives.effect"),
                                             "x": t("deep_dives.effect")}), width="stretch")
        up, down = int((d["effect_size"] > 0).sum()), int((d["effect_size"] < 0).sum())
        insight(t("deep_dives.insight_drug", drug=drug, n=fmt_int(len(d)),
                  up=fmt_int(up), down=fmt_int(down)))
        table_view(d[["feature", "feature_space", "effect_size", "fdr", "robustness", "sample_set"]]
                   .sort_values("fdr"), "drug_detail")

    # --- Onglet 2 : carte de chaleur médicaments x familles de variables --------
    with tab2:
        top = drugs_sig["effector"].value_counts().head(15).index
        matrix = (drugs_sig[drugs_sig["effector"].isin(top)]
                  .pivot_table(index="effector", columns="feature_space", values="fdr",
                               aggfunc="size", fill_value=0, observed=True))
        matrix = matrix.loc[matrix.sum(axis=1).sort_values(ascending=False).index,
                            matrix.sum().sort_values(ascending=False).index]
        st.plotly_chart(viz.heatmap(matrix, t("deep_dives.heat_title"), t("deep_dives.heat_sub"),
                                    value_name=t("deep_dives.n_assoc")), width="stretch")
        col_max = matrix.sum().idxmax()
        insight(t("deep_dives.insight_heat", space=col_max))
        table_view(matrix.reset_index(), "drug_by_feature_space")

    # --- Onglet 3 : qui brouille le signal ? -------------------------------------
    with tab3:
        named = pd.DataFrame(ctx.report.get("top_confounders_named")
                             or [{"code": c, "name": c, "n": n}
                                 for c, n in ctx.report.get("top_confounders", {}).items()])
        if named.empty:
            st.info(t("common.no_data"))
        else:
            named["name"] = [variable_name(c, n) for c, n in zip(named["code"], named["name"])]
            named = named.head(12)
            drug_like = ~named["code"].isin(["CENTER_C", "AGE", "BMI_C", "GENDER", "Status",
                                             "SMOKE", "aHEI", "DASH", "DDS", "pa_work_2cl"])
            st.plotly_chart(viz.ranked_bars(
                named, "name", "n", viz.KIND_COLORS["drug"], t("deep_dives.conf_title"),
                t("deep_dives.conf_sub"), value_name=t("deep_dives.n_assoc"),
                highlight=set(named.loc[drug_like, "name"])), width="stretch")
            st.caption(t("deep_dives.conf_legend"))
            n_drug_top5 = int(drug_like.head(5).sum())
            insight(t("deep_dives.insight_conf", k=n_drug_top5, first=named["name"].iloc[0]))
            table_view(named, "top_confounders")
        caveat(t("deep_dives.caveat_conf"))
    next_button(KEY)


def _volcano_labels(ctx: Context) -> dict:
    return {"increase": t("common.increase"), "decrease": t("common.decrease"),
            "x": t("deep_dives.effect"), "y": "−log10(FDR)", "effect": t("deep_dives.effect"),
            "threshold": f"FDR = {ctx.filters.fdr}"}
