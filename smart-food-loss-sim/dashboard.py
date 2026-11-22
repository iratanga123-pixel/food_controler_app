"""Web dashboard for storage managers and the cooperative.

Usage:
    streamlit run dashboard.py
The simulator is started and controlled from the Simulation control page (left menu).
"""
import altair as alt
import pandas as pd
import streamlit as st

import registry
from ai_view import ai_panel
from alerts import check_and_alert
from config import APP_NAME, CROPS, ICON_PNG
from i18n import crop_name, header, lang, t
from notify import show_alerts
from predictor import load_readings, predict_all, risk_score

st.set_page_config(page_title=APP_NAME, page_icon=ICON_PNG, layout="wide")
COLORS = {"Good": "#2c7f4a", "Watch": "#c98a14", "Act now": "#c0392b"}

header("app_title")


@st.fragment(run_every=5)   # refresh the live view every 5 seconds
def live_view():
    preds = predict_all()
    if not preds:
        st.warning(t("no_readings"))
        return
    show_alerts(check_and_alert(preds))   # toast + desktop notification for each new alert

    # Crop limits set on the Admin page
    limits = registry.get_limits()
    stock = registry.stock_by_store()
    breaches = {p["store"]["id"]: registry.limit_breaches(
        limits[p["store"]["crop"]], p["features"]["grain_temp"], p["features"]["humidity"],
        p["features"]["grain_moisture"], lang()) if p["store"]["crop"] in limits else [] for p in preds}

    # Summary
    act = [p for p in preds if p["level"] > 0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("m_stores"), len(preds))
    c2.metric(t("m_action"), len(act))
    c3.metric(t("m_outside"), sum(1 for b in breaches.values() if b))
    c4.metric(t("m_risk"), f"{sum(p['store']['tonnes'] for p in act)} t")
    c5.metric(t("m_last"), pd.to_datetime(preds[0]["last_ts"]).strftime("%d/%m, %H:%M"))

    # One card per store
    cols = st.columns(len(preds))
    for col, p in zip(cols, preds):
        f = p["features"]
        with col:
            st.markdown(f"**{p['store']['name']}**  \n{crop_name(p['store']['crop'])} · {p['store']['tonnes']} t")
            st.markdown(f"<span style='background:{COLORS[p['level_name']]};color:white;padding:2px 10px;"
                        f"border-radius:10px;font-weight:600'>{t(p['level_name'])}</span>", unsafe_allow_html=True)
            st.write(t("card_values", m=f["grain_moisture"], rh=f["humidity"], t=f["grain_temp"]))
            st.progress(risk_score(p["proba"]), text=t("ai_risk"))
            if breaches[p["store"]["id"]]:
                st.error(t("outside") + "; ".join(breaches[p["store"]["id"]]), icon="⚠️")
            else:
                st.caption(t("within"))
            if p["store"]["id"] in stock:
                st.caption(t("reg_stock", t=stock[p["store"]["id"]]))

    # Detail of one store
    st.divider()
    names = {p["store"]["name"]: p for p in preds}
    choice = st.selectbox(t("store_detail"), list(names), key="store_choice")
    p = names[choice]
    s, c = p["store"], CROPS[p["store"]["crop"]]
    df = load_readings(s["id"], hours=96)
    df["time"] = pd.to_datetime(df["ts"])

    lim = limits.get(s["crop"])
    left, right = st.columns([2, 1])
    with left:
        st.caption(t("limits_caption"))
        for col_name, title, lines in [
                ("grain_moisture", t("ch_moisture"),
                 [lim["moisture_min"], lim["moisture_max"]] if lim else [c["m_safe"]]),
                ("humidity", t("ch_rh"), [lim["rh_min"], lim["rh_max"]] if lim else [70]),
                ("grain_temp", t("ch_temp"), [lim["temp_min"], lim["temp_max"]] if lim else [])]:
            line = alt.Chart(df).mark_line(color="#1d6b52").encode(
                x=alt.X("time:T", title=None), y=alt.Y(f"{col_name}:Q", title=title, scale=alt.Scale(zero=False)))
            layers = [line]
            if lines:
                layers.append(alt.Chart(pd.DataFrame({"y": lines})).mark_rule(color="#c0392b", strokeDash=[5, 4]).encode(y="y:Q"))
            st.altair_chart(alt.layer(*layers).properties(height=170), use_container_width=True)
    with right:
        st.subheader(t(p["level_name"]))
        st.write(t("safe_days", d=p["safe_days_now"]))
        st.write(t("ai_proba"))
        st.dataframe(pd.DataFrame({t("col_risk"): [t(k) for k in p["proba"]],
                                   t("col_proba"): [f"{v:.0%}" for v in p["proba"].values()]}),
                     hide_index=True, use_container_width=True)
        st.write(t("trend", v=p["features"]["moisture_slope_24h"] * 24))
        st.write(t("drivers"))
        st.dataframe(pd.DataFrame({t("col_factor"): [t("f_moisture"), t("f_humidity"), t("f_temp")],
                                   t("col_halvings"): [round(max(0, p["drivers"][k]), 2)
                                                       for k in ("moisture", "humidity", "temperature")]}),
                     hide_index=True, use_container_width=True)

    # AI prediction for the selected store
    with st.container(border=True):
        st.markdown(f"**{t('sec_ai')}**")
        ai_panel(s)


live_view()
