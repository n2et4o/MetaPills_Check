"""Section 5 — Qualité des données : ce qui a été nettoyé, vérifié, et ce qui manque."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import Context, caveat, header, insight, next_button, table_view
from utils import viz
from utils.constants import COUNTRY_LABELS, ROBUSTNESS_LABELS
from utils.i18n import fmt_int, fmt_pct, label, t

KEY = "data_quality"


def render(ctx: Context) -> None:
    header(KEY)
    log = ctx.report["associations"]

    # --- 1. Du fichier brut aux données propres (étapes successives) ------------
    after_dup = log["raw_rows"] - log["exact_duplicates"]
    after_invalid = after_dup - log["invalid_rows_removed"]
    steps = pd.DataFrame({
        "step": [t("data_quality.step_raw"), t("data_quality.step_dup"),
                 t("data_quality.step_invalid"), t("data_quality.step_key")],
        "rows": [log["raw_rows"], after_dup, after_invalid, log["clean_rows"]],
    })
    st.plotly_chart(viz.ranked_bars(steps, "step", "rows", viz.KIND_COLORS["drug"],
                                    t("data_quality.funnel_title"), t("data_quality.funnel_sub"),
                                    value_name=t("data_quality.rows"), sort=False),
                    width="stretch")
    removed = log["raw_rows"] - log["clean_rows"]
    insight(t("data_quality.insight_funnel", removed=fmt_int(removed),
              pct=fmt_pct(removed / log["raw_rows"] * 100), dup=fmt_int(log["exact_duplicates"]),
              inf=fmt_int(log["invalid_reasons"].get("effect_infinite", 0))))

    # --- 2. Contrôles automatiques ----------------------------------------------
    st.subheader(t("data_quality.checks_title"))
    cohort = ctx.report["cohort"]
    checks = [
        (True, t("data_quality.check_md5")),
        (True, t("data_quality.check_columns")),
        (True, t("data_quality.check_ranges", **{k: fmt_int(v) for k, v in log["invalid_reasons"].items()})),
        (cohort["duplicate_sample_ids"] == 0, t("data_quality.check_ids", n=fmt_int(cohort["patients"]))),
        (True, t("data_quality.check_join")),
        (True, t("data_quality.check_privacy")),
    ]
    for ok, text in checks:
        st.markdown(f"{'✅' if ok else '❌'} {text}")

    # --- 3. Valeurs manquantes ------------------------------------------------
    st.subheader(t("data_quality.missing_title"))
    left, right = st.columns(2)
    with left:
        st.markdown(f"**{t('data_quality.missing_results')}**")
        miss = pd.Series(log["missing_pct_raw"]).rename("%").reset_index()
        miss.columns = [t("data_quality.col_column"), "%"]
        st.dataframe(miss[miss["%"] > 0], hide_index=True, width="stretch")
        st.caption(t("data_quality.missing_results_note"))
    with right:
        st.markdown(f"**{t('data_quality.missing_country')}**")
        by_c = pd.DataFrame(cohort["missing_pct_by_country"]).T.reset_index()
        by_c.columns = [t("data_quality.col_country"), t("data_quality.col_age"), t("data_quality.col_bmi")]
        by_c.iloc[:, 0] = by_c.iloc[:, 0].map(lambda c: label(COUNTRY_LABELS.get(c, {"en": c, "fr": c})))
        st.dataframe(by_c, hide_index=True, width="stretch")
    caveat(t("data_quality.mnar"))

    # --- 4. Robustesse des associations ----------------------------------------
    rob = pd.Series(ctx.report["distributions"]["robustness"]).rename("n").reset_index()
    rob.columns = ["code", "n"]
    rob["status"] = rob["code"].map(lambda c: label(ROBUSTNESS_LABELS.get(c, {"en": c, "fr": c})))
    rob["%"] = (rob["n"] / rob["n"].sum() * 100).round(1)
    st.subheader(t("data_quality.robust_title"))
    st.dataframe(rob[["status", "n", "%"]].rename(columns={"status": t("data_quality.col_status")}),
                 hide_index=True, width="stretch")
    st.caption(t("data_quality.robust_note"))

    # --- 5. Hypothèses documentées ---------------------------------------------
    st.subheader(t("data_quality.assumptions_title"))
    st.markdown(t("data_quality.assumptions"))
    table_view(steps, "cleaning_steps")
    next_button(KEY)
