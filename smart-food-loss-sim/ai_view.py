"""AI prediction panel for one store: risk level, risk %, what drives it and what to do.
Shown in the store detail on the dashboard."""
import pandas as pd
import streamlit as st

import registry
import sim_control as sc
from config import CROPS
from i18n import lang, t
from predictor import assess_store

RISK = {0: ("risk_low", "#2c7f4a"), 1: ("risk_medium", "#c98a14"), 2: ("risk_high", "#c0392b")}


def fmt_ts(ts) -> str:
    return pd.to_datetime(ts).strftime("%d/%m %H:%M")


def is_offline(sid: str) -> bool:
    return sc.simulator_alive() and sc.store_control(sc.read_control(), sid)["scenario"] in sc.OFFLINE_SCENARIOS


def risk_factors(p: dict) -> list[str]:
    f, d = p["features"], p["drivers"]
    safe = CROPS[p["store"]["crop"]]["m_safe"]
    weighted = []
    for key, text in [("moisture", t("fx_moisture", v=f["grain_moisture"], safe=safe)),
                      ("humidity", t("fx_humidity", v=f["humidity"])),
                      ("temperature", t("fx_temp", v=f["grain_temp"]))]:
        if d[key] > 0.05:
            weighted.append((d[key], f"{text}: {t('fx_halves', x=2 ** d[key])}"))
    out = [text for _, text in sorted(weighted, key=lambda w: -w[0])]
    if f["moisture_slope_24h"] * 24 > 0.05:
        out.append(t("fx_m_trend", v=f["moisture_slope_24h"] * 24))
    if f["humidity_slope_24h"] * 24 > 3:
        out.append(t("fx_rh_trend", v=f["humidity_slope_24h"] * 24))
    if f["grain_minus_air_24h"] > 1.5:
        out.append(t("fx_heating", v=f["grain_minus_air_24h"]))
    return out


def recommendations(p: dict, scenario: str, offline: bool, breaches: list[str]) -> list[str]:
    """What staff should do. Switching equipment is not on the list: automatic control does that."""
    d, f = p["drivers"], p["features"]
    powered = scenario != "power_failure"
    recs = []
    if not powered:
        recs.append(t("rec_power"))
    elif offline:
        recs.append(t("rec_offline"))
    if powered and (breaches or any(v > 0.05 for v in d.values())):
        recs.append(t("rec_auto"))
    if d["moisture"] > 0.05:
        recs.append(t("rec_dry", m=CROPS[p["store"]["crop"]]["m_safe"]))
    if d["humidity"] > 0.05 or f["humidity_slope_24h"] * 24 > 3 or scenario == "poor_ventilation":
        recs.append(t("rec_bags"))
    if d["temperature"] > 0.05:
        recs.append(t("rec_shade"))
    if p["level"] >= 1 or offline or not powered:
        recs.append(t("rec_inspect"))
    return list(dict.fromkeys(recs)) or [t("rec_ok")]


def ai_panel(store: dict):
    try:
        p = assess_store(store)
    except Exception:
        p = None
    if p is None:
        st.info(t("ai_no_data"))
        return
    scenario = sc.store_control(sc.read_control(), store["id"])["scenario"]
    offline = is_offline(store["id"])
    lim = registry.get_limits().get(store["crop"])
    f = p["features"]
    breaches = registry.limit_breaches(lim, f["grain_temp"], f["humidity"], f["grain_moisture"],
                                       lang()) if lim else []

    # Compact: three short columns side by side
    name, color = RISK[p["level"]]
    c1, c2, c3 = st.columns([1, 2, 2])
    with c1:
        pct = f" · {p['risk_pct']:.0%}" if p["risk_pct"] is not None else ""
        st.markdown(f"<div style='background:{color};color:white;padding:6px 8px;border-radius:8px;"
                    f"text-align:center;font-weight:700'>{t(name)}{pct}</div>", unsafe_allow_html=True)
        st.caption(t("ai_based_on", ts=fmt_ts(p["last_ts"]), d=p["safe_days_now"]))
        if offline:
            st.caption("📡 " + t("ai_stale", ts=fmt_ts(p["last_ts"])))
    with c2:
        st.markdown(f"**{t('factors_header')}**")
        factors = risk_factors(p)[:3]
        st.markdown("\n".join(f"- {x}" for x in factors) if factors else t("no_factors"))
    with c3:
        st.markdown(f"**{t('recs_header')}**")
        st.markdown("\n".join(f"- {x}" for x in recommendations(p, scenario, offline, breaches)[:3]))
