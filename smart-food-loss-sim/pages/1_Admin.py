"""Admin page: login, food registration, stock list and crop storage limits.

Opens from the left menu of the dashboard (streamlit run dashboard.py).
Admin can do everything; the warehouse manager can register and dispatch food but
can only view the crop limits.
"""
import hmac
from datetime import date

import pandas as pd
import streamlit as st

import registry
import sim_control as sc
from config import APP_NAME, ICON_PNG, STORES, USERS
from i18n import crop_name, header, lang, t
from notify import alert_watch

st.set_page_config(page_title=f"Admin · {APP_NAME}", page_icon=ICON_PNG, layout="wide")

STORE_NAMES = {s["id"]: s["name"] for s in STORES}


# ---- Login -----------------------------------------------------------------

def login_form():
    header("login_title")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid, st.form("login"):
        username = st.text_input(t("username")).strip().lower()
        password = st.text_input(t("password"), type="password")
        if st.form_submit_button(t("login_btn"), type="primary"):
            user = USERS.get(username)
            if user and hmac.compare_digest(password.encode(), user["password"].encode()):
                st.session_state.user = {"username": username, "name": user["name"], "role": user["role"]}
                st.rerun()
            st.error(t("login_bad"))
    with mid:
        st.caption(t("login_hint"))


if "user" not in st.session_state:
    login_form()
    st.stop()

user = st.session_state.user
is_admin = user["role"] == "Admin"

with st.sidebar:
    st.write(t("logged_in", name=user["username"], role=t(user["role"])))
    if st.button(t("logout")):
        del st.session_state["user"]
        st.rerun()

header("admin_title")
alert_watch()   # desktop notifications keep coming while the Admin works here
limits = registry.get_limits()


def label(crop: str) -> str:
    return crop_name(crop, limits.get(crop, {}).get("label"))


tab_reg, tab_stock, tab_limits, tab_auto = st.tabs(
    [t("tab_reg"), t("tab_stock"), t("tab_limits"), t("tab_auto")])


# ---- 1. Food registration --------------------------------------------------

with tab_reg:
    st.subheader(t("reg_header"))
    c1, c2 = st.columns(2)
    store_id = c1.selectbox(t("facility"), list(STORE_NAMES), format_func=STORE_NAMES.get)
    store = next(s for s in STORES if s["id"] == store_id)
    crop_ids = list(limits)
    crop = c2.selectbox(t("crop_type"), crop_ids, format_func=label,
                        index=crop_ids.index(store["crop"]) if store["crop"] in crop_ids else 0)
    lim = limits[crop]

    st.info(t("limits_info", crop=label(crop), tmin=lim["temp_min"], tmax=lim["temp_max"],
              rmin=lim["rh_min"], rmax=lim["rh_max"], mmin=lim["moisture_min"], m=lim["moisture_max"]))
    if crop != store["crop"]:
        st.warning(t("crop_mismatch", store=store["name"], crop=crop_name(store["crop"])))

    with st.form("register", clear_on_submit=True):
        a, b, c = st.columns(3)
        quantity_kg = a.number_input(t("qty"), min_value=0.0, step=50.0)
        bags = b.number_input(t("bags"), min_value=0, step=1)
        date_in = c.date_input(t("date_in"), value=date.today(), max_value=date.today())
        a, b = st.columns(2)
        supplier = a.text_input(t("supplier"))
        supplier_phone = b.text_input(t("supplier_phone"), placeholder="+2507...")
        a, b, c = st.columns(3)
        intake_moisture = a.number_input(t("intake_m"), min_value=5.0, max_value=35.0,
                                         value=float(lim["moisture_max"]), step=0.1, format="%.1f")
        intake_temp = b.number_input(t("intake_t"), min_value=-5.0, max_value=50.0,
                                     value=20.0, step=0.5, format="%.1f")
        quality = c.selectbox(t("quality"), ["Grade 1", "Grade 2", "Grade 3", "Ungraded"], format_func=t)
        notes = st.text_area(t("notes"), placeholder=t("notes_ph"))
        submitted = st.form_submit_button(t("reg_btn"), type="primary")

    if submitted:
        errors = []
        if quantity_kg <= 0:
            errors.append(t("e_qty"))
        if not supplier.strip():
            errors.append(t("e_supplier"))
        if errors:
            for e in errors:
                st.error(e)
        else:
            # Saved in English so the records stay consistent; shown in the chosen language.
            saved_check = registry.limit_breaches(lim, intake_temp, None, intake_moisture, "en")
            shown_check = registry.limit_breaches(lim, intake_temp, None, intake_moisture, lang())
            batch_id = registry.register_batch({
                "store_id": store_id, "crop": crop, "quantity_kg": quantity_kg, "bags": int(bags) or None,
                "supplier": supplier.strip(), "supplier_phone": supplier_phone.strip() or None,
                "date_in": date_in.isoformat(), "intake_moisture": intake_moisture, "intake_temp": intake_temp,
                "quality": quality, "intake_check": "; ".join(saved_check) or "OK", "notes": notes.strip() or None,
            }, user["username"])
            st.success(t("reg_ok", id=batch_id, kg=quantity_kg, crop=label(crop), store=store["name"]))
            if shown_check:
                st.warning(t("reg_warn", b="; ".join(shown_check), m=lim["moisture_max"]))


# ---- 2. Food in storage ----------------------------------------------------

with tab_stock:
    df = registry.list_batches()
    if df.empty:
        st.write(t("no_batches"))
    else:
        df["store"] = df["store_id"].map(STORE_NAMES).fillna(df["store_id"])
        df["crop_label"] = df["crop"].map(label)
        in_store = df[df["status"] == "In storage"]

        m1, m2, m3 = st.columns(3)
        m1.metric(t("m_batches"), len(in_store))
        m2.metric(t("m_food"), f"{in_store['quantity_kg'].sum() / 1000:,.2f} t")
        m3.metric(t("m_problems"), int((in_store["intake_check"] != "OK").sum()))

        f1, f2 = st.columns(2)
        store_filter = f1.multiselect(t("filter_store"), sorted(df["store"].unique()))
        status_filter = f2.multiselect(t("filter_status"), ["In storage", "Dispatched"],
                                       default=["In storage"], format_func=t)
        view = df
        if store_filter:
            view = view[view["store"].isin(store_filter)]
        if status_filter:
            view = view[view["status"].isin(status_filter)]
        view = view.assign(status=view["status"].map(t), quality=view["quality"].map(lambda q: t(q) if q else q))

        cols = {"id": "c_batch", "store": "c_store", "crop_label": "c_crop", "quantity_kg": "c_qty",
                "bags": "c_bags", "supplier": "c_supplier", "supplier_phone": "c_phone", "date_in": "c_date_in",
                "intake_moisture": "c_moisture", "intake_temp": "c_temp", "quality": "c_grade",
                "intake_check": "c_check", "status": "c_status", "date_out": "c_date_out",
                "registered_by": "c_by", "notes": "c_notes"}
        table = view[list(cols)].rename(columns={k: t(v) for k, v in cols.items()})
        st.dataframe(table, hide_index=True)
        st.download_button(t("download"), table.to_csv(index=False).encode("utf-8"),
                           file_name="food_batches.csv", mime="text/csv")

        if not in_store.empty:
            st.subheader(t("dispatch_header"))
            options = {int(r.id): f"#{r.id} · {r.store} · {r.crop_label} · {r.quantity_kg:,.0f} kg · {r.supplier}"
                       for r in in_store.itertuples()}
            d1, d2, d3 = st.columns([3, 1, 1], vertical_alignment="bottom")
            batch = d1.selectbox(t("batch"), list(options), format_func=options.get)
            date_out = d2.date_input(t("date_out"), value=date.today(), max_value=date.today())
            if d3.button(t("dispatch_btn")):
                registry.dispatch_batch(batch, date_out.isoformat())
                st.toast(t("dispatched_toast", id=batch))
                st.rerun()


# ---- 3. Crop storage limits ------------------------------------------------

with tab_limits:
    st.subheader(t("limits_header"))
    st.write(t("limits_help"))
    table = pd.DataFrame([{t("l_crop"): label(crop),
                           t("l_temp"): t("l_range", lo=l["temp_min"], hi=l["temp_max"]),
                           t("l_rh"): t("l_range", lo=l["rh_min"], hi=l["rh_max"]),
                           t("l_m"): t("l_range", lo=l["moisture_min"], hi=l["moisture_max"]),
                           t("l_by"): l["updated_by"], t("l_at"): l["updated_at"]} for crop, l in limits.items()])
    st.dataframe(table, hide_index=True)

    if not is_admin:
        st.info(t("admin_only"))
    else:
        st.subheader(t("edit_header"))
        NEW = "__new__"
        choice = st.selectbox(t("l_crop"), [NEW] + list(limits),
                              format_func=lambda c: t("add_crop") if c == NEW else label(c))
        new = choice == NEW
        cur = limits.get(choice, {"label": "", "temp_min": 10.0, "temp_max": 25.0,
                                  "rh_min": 40.0, "rh_max": 70.0, "moisture_min": 11.0, "moisture_max": 14.0})
        with st.form(f"limits_{choice}"):
            name = st.text_input(t("crop_name"), value=cur["label"])
            a, b = st.columns(2)
            vals = {
                "temp_min": a.number_input(t("f_tmin"), value=float(cur["temp_min"]), step=0.5),
                "temp_max": b.number_input(t("f_tmax"), value=float(cur["temp_max"]), step=0.5),
                "rh_min": a.number_input(t("f_rmin"), value=float(cur["rh_min"]), step=1.0),
                "rh_max": b.number_input(t("f_rmax"), value=float(cur["rh_max"]), step=1.0),
                "moisture_min": a.number_input(t("f_mmin"), value=float(cur["moisture_min"]),
                                               step=0.1, format="%.1f"),
                "moisture_max": b.number_input(t("f_mmax"), value=float(cur["moisture_max"]),
                                               step=0.1, format="%.1f"),
            }
            save = st.form_submit_button(t("save_limits"), type="primary")
        if save:
            errors = [t(k) for k in registry.validate_limits(vals)]
            crop_id = "".join(ch for ch in name.strip().lower().replace(" ", "_") if ch.isalnum() or ch == "_")
            if not name.strip():
                errors.append(t("e_crop_name"))
            elif new and crop_id in limits:
                errors.append(t("e_crop_exists", name=name))
            if errors:
                for e in errors:
                    st.error(e)
            else:
                registry.save_limits(crop_id if new else choice, name.strip(), vals, user["username"])
                st.toast(t("limits_saved", name=name.strip()))
                st.rerun()
        if new:
            st.caption(t("new_crop_note"))


# ---- 4. Automatic warehouse control (no manual switching) -----------------

with tab_auto:
    st.subheader(t("auto_header"))
    st.write(t("auto_help"))
    for s in STORES:
        lim = limits.get(s["crop"])
        with st.container(border=True):
            st.markdown(f"**{s['name']}** · {label(s['crop'])}")
            if not lim:
                st.warning(t("auto_no_limits"))
                continue
            tg = sc.targets(lim)
            st.markdown(t("auto_rules_above", tmax=lim["temp_max"], rmax=lim["rh_max"], mmax=lim["moisture_max"],
                          dh=tg["dehumidifier_target"]))
            st.markdown(t("auto_rules_below", tmin=lim["temp_min"], rmin=lim["rh_min"], mmin=lim["moisture_min"],
                          ht=tg["heater_target"], hu=tg["humidifier_target"]))
    st.caption(t("auto_change_limits"))
