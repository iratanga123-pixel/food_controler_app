"""Simulation control: drive the virtual sensors, switch test scenarios and watch the warehouse
equipment, one store at a time (the AI prediction is on the dashboard). The equipment is never switched by hand:
it reacts automatically whenever a reading goes above or below the crop's storage limits.

Opens from the left menu of the dashboard (streamlit run dashboard.py). The simulator
(simulator.py --live) can be started from here, or from a terminal as before.
"""
import time

import pandas as pd
import streamlit as st

import registry
import sim_control as sc
from ai_view import fmt_ts, is_offline
from config import APP_NAME, ICON_PNG, STORES
from i18n import crop_name, header, t
from notify import alert_watch
from predictor import load_readings

st.set_page_config(page_title=f"Simulation control · {APP_NAME}", page_icon=ICON_PNG, layout="wide")
header("sim_title")
alert_watch()   # SMS alerts and desktop notifications while you run scenarios

STORES_BY_ID = {s["id"]: s for s in STORES}
EQUIPMENT = {"cooling_fan": ("eq_fan", "❄️"), "ventilation": ("eq_ventilation", "🌬️"),
             "dehumidifier": ("eq_dehum", "💧"), "heater": ("eq_heater", "🔥"), "humidifier": ("eq_humidifier", "💦")}
FINDINGS = ["in_ok", "in_insects", "in_mould", "in_smell", "in_hot", "in_wet_bags", "in_rodents"]
# Slider ranges: (min, max, step). Wide enough to push every reading above or below the crop limits.
RANGES = {"t": (5.0, 40.0, 0.5), "rh": (25.0, 92.0, 1.0), "m": (8.0, 25.0, 0.1)}

STATUS = sc.read_status()
ALIVE = sc.simulator_alive(STATUS)   # the controls only work while the simulator runs

store_id = st.selectbox(t("store"), list(STORES_BY_ID), key="sim_store",
                        format_func=lambda i: f"{STORES_BY_ID[i]['name']} · {crop_name(STORES_BY_ID[i]['crop'])}")
store = STORES_BY_ID[store_id]
ctl = sc.store_control(sc.read_control(), store_id)


def latest_readings(sid: str, n: int) -> pd.DataFrame:
    try:
        return load_readings(sid, hours=n)
    except Exception:            # no database or table yet
        return pd.DataFrame()


# ---- Callbacks (run before the page redraws) ---------------------------------

def start_sim():
    if sc.simulator_alive():
        sc.set_running(True)
    else:
        sc.start_simulator()
        st.session_state.sim_starting = time.time()


def stop_sim():
    sc.set_running(False)


def slider_keys(sid: str) -> dict:
    return {k: f"set_{k}_{sid}" for k in RANGES}


def apply_values(s: dict):
    k = slider_keys(s["id"])
    sc.send_command(s["id"], "set_values", temp=st.session_state[k["t"]],
                    humidity=st.session_state[k["rh"]], moisture=st.session_state[k["m"]])
    st.toast(t("values_sent", store=s["name"]))


def reset_values(s: dict):
    sc.send_command(s["id"], "reset_values")
    k = slider_keys(s["id"])
    st.session_state[k["t"]], st.session_state[k["rh"]], st.session_state[k["m"]] = (
        float(s["start_T"]), float(s["start_RH"]), float(s["start_m"]))
    st.toast(t("values_reset", store=s["name"]))


def set_scenario(s: dict):
    scenario = st.session_state[f"scen_{s['id']}"]
    sc.update_store(s["id"], scenario=scenario)
    st.toast(t("scenario_set", store=s["name"], sc=t("sc_" + scenario)))


def reset_connection(s: dict):
    scenario = sc.store_control(sc.read_control(), s["id"])["scenario"]
    if scenario == "sensor_disconnection":
        sc.update_store(s["id"], scenario="normal")
        st.toast(t("conn_reset_ok", store=s["name"]))
    elif scenario == "power_failure":
        st.toast(t("conn_no_power", store=s["name"]))
    else:
        st.toast(t("conn_already", store=s["name"]))


# ---- Live parts (redraw on their own) -----------------------------------------

@st.fragment(run_every=3)
def simulator_panel():
    status = sc.read_status()
    alive = sc.simulator_alive(status)
    if alive != ALIVE:
        st.rerun()               # simulator started or stopped: enable/disable the other controls
    if not alive:
        starting = time.time() - st.session_state.get("sim_starting", 0) < 20
        (st.info if starting else st.warning)(t("sim_starting" if starting else "sim_not_running"))
        st.button(t("sim_start"), type="primary", on_click=start_sim, disabled=starting)
    elif sc.read_control()["running"]:
        st.success(t("sim_running", ts=fmt_ts(status["sim_time"])))
        st.button(t("sim_stop"), on_click=stop_sim)
    else:
        st.info(t("sim_paused", ts=fmt_ts(status["sim_time"])))
        st.button(t("sim_start"), type="primary", on_click=start_sim)
    st.caption(t("sim_fresh_note"))

    st.markdown(f"**{t('now_readings')}**")
    df = latest_readings(store_id, 2)
    if df.empty:
        st.caption(t("no_store_readings"))
        return
    now, prev = df.iloc[-1], df.iloc[0]
    cols = st.columns(4)
    for col, (name, label, unit, digits) in zip(cols, [
            ("air_temp", "r_air", " °C", 1), ("humidity", "r_rh", "%", 0),
            ("grain_moisture", "r_moisture", "%", 1), ("grain_temp", "r_grain_t", " °C", 1)]):
        col.metric(t(label), f"{now[name]:.{digits}f}{unit}",
                   delta=f"{now[name] - prev[name]:+.{max(digits, 1)}f}" if len(df) > 1 else None,
                   delta_color="off")
    if is_offline(store_id):
        st.error(t("sensor_offline", ts=fmt_ts(now["ts"])), icon="📡")
    else:
        st.caption(fmt_ts(now["ts"]))


@st.fragment(run_every=3)
def equipment_panel():
    """Read-only view of the automatic controller: what is running and why."""
    st.info(t("auto_active", crop=crop_name(store["crop"])))
    lim = registry.get_limits().get(store["crop"])
    if lim:
        st.caption(t("auto_limits_line", tmin=lim["temp_min"], tmax=lim["temp_max"], rmin=lim["rh_min"],
                     rmax=lim["rh_max"], mmin=lim["moisture_min"], mmax=lim["moisture_max"]))
    else:
        st.warning(t("auto_no_limits"))
    if sc.store_control(sc.read_control(), store_id)["scenario"] == "power_failure":
        st.error(t("eq_power_off"), icon="⚡")

    store_status = (sc.read_status() or {}).get("stores", {}).get(store_id) if sc.simulator_alive() else None
    if not store_status:
        st.caption(t("eq_no_status"))
        return
    equipment = store_status.get("equipment", {})
    cols = st.columns(len(EQUIPMENT))
    for col, (name, (label_key, icon)) in zip(cols, EQUIPMENT.items()):
        on = bool(equipment.get(name))
        col.markdown(f"<div style='border:1px solid rgba(128,128,128,.35);border-radius:10px;padding:8px 4px;"
                     f"text-align:center;opacity:{1 if on else .55}'>{icon}<br><b>{t(label_key)}</b><br>"
                     f"{'🟢 ' + t('eq_state_on') if on else '⚪ ' + t('eq_state_off')}</div>",
                     unsafe_allow_html=True)
    st.caption(t("eq_help"))

    st.markdown(f"**{t('auto_log_header')}**")
    log = store_status.get("auto_log", [])
    if not log:
        st.caption(t("auto_log_none"))
    for e in log[:6]:
        why = t(e["why"]) if e["v"] is None else t(e["why"], v=e["v"], lim=e["lim"])
        st.caption(f"{fmt_ts(e['ts'])} · " + t("auto_log_on" if e["on"] else "auto_log_off",
                                               eq=t(EQUIPMENT[e["eq"]][0]), why=why))


# ---- Layout --------------------------------------------------------------------

top_left, top_right = st.columns(2)

with top_left.container(border=True):
    st.subheader("1. " + t("sec_sensors"))
    simulator_panel()
    st.divider()
    keys = slider_keys(store_id)
    if keys["t"] not in st.session_state:          # start the sliders at the store's current conditions
        cur = (STATUS or {}).get("stores", {}).get(store_id) or {
            "temp": store["start_T"], "humidity": store["start_RH"], "moisture": store["start_m"]}
        for k, v in [("t", cur["temp"]), ("rh", cur["humidity"]), ("m", cur["moisture"])]:
            lo, hi, step = RANGES[k]
            st.session_state[keys[k]] = float(min(hi, max(lo, round(v / step) * step)))
    a, b, c = st.columns(3)
    for col, k, label, fmt in [(a, "t", "set_temp", "%.1f"), (b, "rh", "set_rh", "%.0f"), (c, "m", "set_m", "%.1f")]:
        lo, hi, step = RANGES[k]
        col.slider(t(label), lo, hi, step=step, format=fmt, key=keys[k], disabled=not ALIVE)
    st.caption(t("set_help"))
    b1, b2 = st.columns(2)
    b1.button(t("apply_values"), type="primary", on_click=apply_values, args=(store,),
              disabled=not ALIVE, width="stretch")
    b2.button(t("reset_values"), on_click=reset_values, args=(store,), disabled=not ALIVE, width="stretch")
    if not ALIVE:
        st.caption(t("sim_start_first"))

with top_right.container(border=True):
    st.subheader("2. " + t("sec_scenarios"))
    key = f"scen_{store_id}"
    st.session_state[key] = ctl["scenario"]
    st.radio(t("scenario_label"), sc.SCENARIOS, key=key, format_func=lambda k: t("sc_" + k),
             on_change=set_scenario, args=(store,), disabled=not ALIVE)
    st.info(t("scd_" + ctl["scenario"]))
    if not ALIVE:
        st.caption(t("sim_start_first"))

with st.container(border=True):
    st.subheader("3. " + t("sec_warehouse"))
    equipment_panel()
    st.button(t("reset_conn"), icon="🔌", on_click=reset_connection, args=(store,), disabled=not ALIVE)
    if not ALIVE:
        st.caption(t("sim_start_first"))

    st.divider()
    st.markdown(f"**{t('insp_header')}**")
    with st.form(f"inspect_{store_id}", clear_on_submit=True):
        inspector = st.text_input(t("insp_inspector"), value=st.session_state.get("user", {}).get("name", ""))
        findings = st.multiselect(t("insp_findings"), FINDINGS, format_func=t)
        m_col, n_col = st.columns([1, 2])
        moisture = m_col.number_input(t("insp_moisture"), min_value=5.0, max_value=35.0, value=None,
                                      step=0.1, format="%.1f")
        notes = n_col.text_input(t("insp_notes"))
        saved = st.form_submit_button(t("insp_save"), type="primary")
    if saved:
        if not inspector.strip():
            st.error(t("insp_need_name"))
        else:
            new_id = registry.add_inspection(store_id, inspector.strip(), findings, moisture, notes.strip() or None)
            st.toast(t("insp_saved", id=new_id, store=store["name"]))

    st.markdown(f"**{t('insp_recent')}**")
    past = registry.list_inspections(store_id, limit=5)
    if past.empty:
        st.caption(t("insp_none"))
    else:
        past["findings"] = past["findings"].map(lambda s: ", ".join(t(k) for k in s.split(";") if k) if s else "")
        past["inspected_at"] = past["inspected_at"].map(fmt_ts)
        cols = {"inspected_at": "ic_when", "inspector": "ic_by", "findings": "ic_findings",
                "moisture": "ic_moisture", "notes": "ic_notes"}
        st.dataframe(past[list(cols)].rename(columns={k: t(v) for k, v in cols.items()}), hide_index=True)
