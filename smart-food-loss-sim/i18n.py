"""English / Kinyarwanda text for the dashboard and admin pages.

t("key", name=value)  -> text in the language picked at the top right of the page.
tr("key", "rw", ...)  -> text in a given language (usable outside Streamlit).
Kinyarwanda wording should be reviewed by a native speaker before real use.
"""
import streamlit as st

from config import CROPS

LANGS = {"en": "English", "rw": "Kinyarwanda"}

STRINGS = {
    # ---- shared ----
    "app_title": ("Hunika", "Hunika"),
    "Good": ("Good", "Ni byiza"),
    "Watch": ("Watch", "Witondere"),
    "Act now": ("Act now", "Fata ingamba nonaha"),
    "b_temp_low": ("temperature {v:.1f} °C is below {lim:g} °C", "ubushyuhe {v:.1f} °C buri munsi ya {lim:g} °C"),
    "b_temp_high": ("temperature {v:.1f} °C is above {lim:g} °C", "ubushyuhe {v:.1f} °C burenze {lim:g} °C"),
    "b_rh_low": ("humidity {v:.0f}% is below {lim:g}%", "ubuhehere bw'umwuka {v:.0f}% buri munsi ya {lim:g}%"),
    "b_rh_high": ("humidity {v:.0f}% is above {lim:g}%", "ubuhehere bw'umwuka {v:.0f}% burenze {lim:g}%"),
    "b_m_high": ("moisture {v:.1f}% is above {lim:g}%", "ubuhehere bw'imyaka {v:.1f}% burenze {lim:g}%"),
    "b_m_low": ("moisture {v:.1f}% is below {lim:g}% (over-dried)",
                "ubuhehere bw'imyaka {v:.1f}% buri munsi ya {lim:g}% (yumye cyane)"),
    "ar_ok": ("back within limits", "byasubiye mu mbibi"),

    # ---- dashboard ----
    "store": ("Store", "Ububiko"),
    "no_readings": ("No readings yet. Start the simulation on the **Simulation control** page (left menu).",
                    "Nta bipimo biraboneka. Tangiza igerageza ku rupapuro rw'**Igenzura ry'igerageza** (ibumoso)."),
    "sms_toast": ("SMS sent: ", "SMS yoherejwe: "),
    "settings": ("Settings: language and notifications", "Igenamiterere: ururimi n'imenyesha"),
    "ns_header": ("Notifications", "Imenyesha"),
    "ns_unsupported": ("Notifications are not available here. Open the app at http://localhost:8501.",
                       "Imenyesha ntirishoboka hano. Fungura porogaramu kuri http://localhost:8501."),
    "ns_on": ("Notifications are on for this browser.", "Imenyesha rirafunguye kuri iyi mushakisha."),
    "ns_off": ("Notifications are off. Allow them to get a pop-up when a store needs action.",
               "Imenyesha rirafunze. Ryemere kugira ngo umenyeshwe igihe ububiko bukeneye ingamba."),
    "ns_blocked": ("Notifications are blocked by the browser. Click the icon left of the address bar → "
                   "Notifications → Allow, then reload the page.",
                   "Mushakisha yabujije imenyesha. Kanda ku kamenyetso kari ibumoso bw'aho wandika aderesi → "
                   "Notifications → Allow, hanyuma wongere ufungure urupapuro."),
    "ns_allow": ("Allow notifications", "Emera imenyesha"),
    "ns_test": ("Send a test notification", "Ohereza imenyesha ry'igerageza"),
    "ns_test_title": ("Hunika", "Hunika"),
    "ns_test_body": ("Notifications are working. You will be told here when a store needs action.",
                     "Imenyesha rirakora. Uzajya umenyeshwa hano igihe ububiko bukeneye ingamba."),
    "nt_title": ("Allow notifications?", "Wemera kubona imenyesha?"),
    "nt_body": ("Get a pop-up on this computer as soon as a store's spoilage risk goes up, "
                "even when this tab is in the background.",
                "Ubone ubutumwa kuri iyi mudasobwa igihe cyose ibyago byo kwangirika mu bubiko byiyongereye, "
                "n'iyo uru rupapuro rutari imbere."),
    "nt_later": ("Not now", "Ubu oya"),
    "nt_allow": ("Allow", "Emera"),
    "nt_ok_title": ("Notifications are on", "Imenyesha ryafunguwe"),
    "nt_ok_body": ("You will be told here when a store needs action.",
                   "Uzajya umenyeshwa hano igihe ububiko bukeneye ingamba."),
    "m_stores": ("Stores monitored", "Ububiko bukurikiranwa"),
    "m_action": ("Need action", "Bukeneye ingamba"),
    "m_outside": ("Outside crop limits", "Birenze imbibi"),
    "m_risk": ("Grain at risk", "Umusaruro uri mu kaga"),
    "m_last": ("Last reading", "Igipimo cya nyuma"),
    "card_values": ("Moisture **{m:.1f}%** · RH **{rh:.0f}%** · Grain **{t:.1f} °C**",
                    "Ubuhehere **{m:.1f}%** · Umwuka **{rh:.0f}%** · Ubushyuhe **{t:.1f} °C**"),
    "ai_risk": ("AI risk, next 72 h", "Ibyago (AI), amasaha 72 ari imbere"),
    "outside": ("Outside limits: ", "Birenze imbibi: "),
    "within": ("✅ Within crop limits", "✅ Biri mu mbibi z'igihingwa"),
    "reg_stock": ("Registered stock: {t:,.2f} t", "Umusaruro wanditswe: {t:,.2f} t"),
    "store_detail": ("Store detail", "Ibisobanuro by'ububiko"),
    "limits_caption": ("Red dashed lines: crop limits set on the Admin page",
                       "Imirongo itukura: imbibi z'igihingwa zashyizweho ku rupapuro rw'Umuyobozi"),
    "ch_moisture": ("Grain moisture (%)", "Ubuhehere bw'imyaka (%)"),
    "ch_rh": ("Relative humidity (%)", "Ubuhehere bw'umwuka (%)"),
    "ch_temp": ("Grain temperature (°C)", "Ubushyuhe bw'imyaka (°C)"),
    "safe_days": ("Safe storage at current readings: **about {d:.0f} days**",
                  "Igihe cyo kubika nta kibazo ukurikije ibipimo by'ubu: **hafi iminsi {d:.0f}**"),
    "ai_proba": ("AI probabilities for the next 72 hours:", "Amahirwe (AI) mu masaha 72 ari imbere:"),
    "col_risk": ("Risk", "Ibyago"),
    "col_proba": ("Probability", "Ijanisha"),
    "trend": ("Moisture trend: **{v:+.2f}% per day**", "Uko ubuhehere buhinduka: **{v:+.2f}% ku munsi**"),
    "drivers": ("What is driving the risk (times the safe storage time is halved):",
                "Ibitera ibyago (inshuro igihe cyo kubika kigabanywamo kabiri):"),
    "col_factor": ("Factor", "Impamvu"),
    "col_halvings": ("Halvings", "Inshuro"),
    "f_moisture": ("Moisture", "Ubuhehere bw'imyaka"),
    "f_humidity": ("Humidity", "Ubuhehere bw'umwuka"),
    "f_temp": ("Temperature", "Ubushyuhe"),

    # ---- simulation control page ----
    "sim_title": ("Simulation control", "Igenzura ry'igerageza"),
    "sec_sensors": ("Sensor simulation", "Igerageza rya sensa"),
    "sec_scenarios": ("Simulation scenarios", "Ibihe by'igerageza"),
    "sec_ai": ("AI prediction", "Iteganya rya AI"),
    "sec_warehouse": ("Warehouse control", "Igenzura ry'ububiko"),
    "sim_not_running": ("The simulator is not running.", "Igerageza ntirikora."),
    "sim_starting": ("Starting the simulator…", "Igerageza riratangira…"),
    "sim_running": ("Running · simulated time {ts}", "Rirakora · igihe cy'igerageza {ts}"),
    "sim_paused": ("Paused · simulated time {ts}", "Ryahagaritswe · igihe cy'igerageza {ts}"),
    "sim_start": ("▶ Start simulation", "▶ Tangiza igerageza"),
    "sim_stop": ("⏸ Stop simulation", "⏸ Hagarika igerageza"),
    "sim_fresh_note": ("Starting opens the simulator in a new window and creates a fresh 96-hour history "
                       "for all stores. Stop pauses all stores; Start resumes them.",
                       "Gutangiza bifungura igerageza mu idirishya rishya kandi bigakora amateka mashya "
                       "y'amasaha 96 ku bubiko bwose. Guhagarika bihagarika ububiko bwose; gutangiza birabusubukura."),
    "sim_start_first": ("Start the simulation to use these controls.",
                        "Tangiza igerageza kugira ngo ukoreshe ibi bikoresho."),
    "now_readings": ("Latest sensor readings", "Ibipimo bya nyuma bya sensa"),
    "r_air": ("Air temperature", "Ubushyuhe bw'umwuka"),
    "r_rh": ("Humidity", "Ubuhehere bw'umwuka"),
    "r_moisture": ("Grain moisture", "Ubuhehere bw'imyaka"),
    "r_grain_t": ("Grain temperature", "Ubushyuhe bw'imyaka"),
    "no_store_readings": ("No readings for this store yet.", "Nta bipimo by'ubu bubiko biraboneka."),
    "sensor_offline": ("Sensor offline: no reading since {ts}.", "Sensa ntiyohereza: nta gipimo kuva {ts}."),
    "set_temp": ("Temperature (°C)", "Ubushyuhe (°C)"),
    "set_rh": ("Humidity (%)", "Ubuhehere bw'umwuka (%)"),
    "set_m": ("Grain moisture (%)", "Ubuhehere bw'imyaka (%)"),
    "set_help": ("These set the store's average conditions. Readings still swing by about ±3 °C and ±7% "
                 "humidity during the day, and then change with the scenario and equipment.",
                 "Ibi bishyiraho ibipimo by'ububiko bisanzwe. Ibipimo bihindagurika hafi ±3 °C na ±7% "
                 "by'ubuhehere ku munsi, hanyuma bigahinduka bitewe n'igihe n'ibikoresho."),
    "apply_values": ("Apply sensor values", "Shyiraho ibi bipimo"),
    "reset_values": ("Reset sensor values", "Subiza ibipimo by'ibanze"),
    "values_sent": ("Sensor values sent to {store}. They apply at the next simulated hour.",
                    "Ibipimo byoherejwe kuri {store}. Bizakurikizwa ku isaha ikurikira."),
    "values_reset": ("{store} reset to its starting values.", "{store} bwasubijwe ku bipimo by'ibanze."),
    "scenario_label": ("Scenario for this store", "Igihe cy'igerageza kuri ubu bubiko"),
    "scenario_set": ("Scenario for {store}: {sc}", "Igihe cy'igerageza kuri {store}: {sc}"),
    "sc_normal": ("Normal storage", "Kubika bisanzwe"),
    "sc_high_temperature": ("High temperature", "Ubushyuhe bwinshi"),
    "sc_high_humidity": ("High humidity", "Ubuhehere bwinshi bw'umwuka"),
    "sc_high_moisture": ("High grain moisture", "Ubuhehere bwinshi bw'imyaka"),
    "sc_poor_ventilation": ("Poor ventilation", "Umwuka udahagije"),
    "sc_sensor_disconnection": ("Sensor disconnection", "Sensa yacitse"),
    "sc_power_failure": ("Power failure", "Umuriro wabuze"),
    "scd_normal": ("The store follows its usual weather pattern.",
                   "Ububiko bukurikiza ikirere gisanzwe."),
    "scd_high_temperature": ("A heat wave: the store heats up toward 35 °C. The cooling fan slows it down.",
                             "Ubushyuhe bukabije: ububiko bushyuha bugana kuri 35 °C. Umuyaga ukonjesha urabigabanya."),
    "scd_high_humidity": ("Humid weather: air humidity climbs toward 90%. Ventilation and the dehumidifier fight it.",
                          "Ikirere gifite ubuhehere: ubuhehere bw'umwuka buzamuka bugana kuri 90%. "
                          "Kongera umwuka n'imashini ikurura ubuhehere birabirwanya."),
    "scd_high_moisture": ("Wet grain was loaded: grain moisture rises toward 19%.",
                          "Hinjijwe imyaka itumye: ubuhehere bw'imyaka buzamuka bugana kuri 19%."),
    "scd_poor_ventilation": ("Vents are blocked: damp, warm air builds up. Once humidity passes the crop's limit, "
                             "automatic control turns the ventilation on and fixes it.",
                             "Aho umwuka unyura harafunze: umwuka uhehereye kandi ushyushye uriyongera. Ubuhehere "
                             "bumaze kurenga imbibi, igenzura ryikora rifungura umwuka rikabikemura."),
    "scd_sensor_disconnection": ("The sensor node stops sending readings. Use Reset sensor connection to fix it.",
                                 "Sensa ihagarika kohereza ibipimo. Koresha Ongera uhuze sensa kugira ngo bikemuke."),
    "scd_power_failure": ("No power: ventilation, cooling fan and dehumidifier stop, the sensor goes offline "
                          "and stale air builds up. Choose another scenario to restore power.",
                          "Nta muriro: kongera umwuka, umuyaga ukonjesha n'imashini ikurura ubuhehere birahagarara, "
                          "sensa ntiyohereza kandi umwuka uhehereye uriyongera. Hitamo ikindi gihe kugira ngo umuriro ugaruke."),
    "risk_low": ("Low risk", "Ibyago bike"),
    "risk_medium": ("Medium risk", "Ibyago biringaniye"),
    "risk_high": ("High risk", "Ibyago byinshi"),
    "risk_pct": ("Spoilage risk, next 72 h", "Ibyago byo kwangirika, amasaha 72 ari imbere"),
    "no_model": ("No trained AI model (or under 48 h of readings): the risk class comes from the storage rule "
                 "on today's readings, so no percentage is shown. Run train_model.py to enable it.",
                 "Nta AI yatojwe (cyangwa ibipimo biri munsi y'amasaha 48): urwego rw'ibyago ruva ku itegeko "
                 "ryo kubika ku bipimo by'uyu munsi, nta janisha rigaragazwa. Koresha train_model.py."),
    "ai_no_data": ("Not enough readings to analyse yet.", "Nta bipimo bihagije byo gusesengura."),
    "ai_stale": ("The sensor is offline, so this prediction uses the last readings ({ts}).",
                 "Sensa ntiyohereza, iri teganya rikoresha ibipimo bya nyuma ({ts})."),
    "ai_based_on": ("Based on readings up to {ts} · safe storage about {d:.0f} days at current conditions",
                    "Bishingiye ku bipimo kugeza {ts} · kubika nta kibazo hafi iminsi {d:.0f} ukurikije ibipimo by'ubu"),
    "factors_header": ("What contributes to the risk", "Ibitera ibyago"),
    "no_factors": ("No reading is pushing the risk up.", "Nta gipimo kizamura ibyago."),
    "fx_moisture": ("Grain moisture {v:.1f}% is above the safe {safe:g}%", "Ubuhehere bw'imyaka {v:.1f}% burenze {safe:g}%"),
    "fx_humidity": ("Air humidity {v:.0f}% is above 70%", "Ubuhehere bw'umwuka {v:.0f}% burenze 70%"),
    "fx_temp": ("Grain temperature {v:.1f} °C is above 22 °C", "Ubushyuhe bw'imyaka {v:.1f} °C burenze 22 °C"),
    "fx_halves": ("cuts safe storage time {x:.1f}×", "bigabanya igihe cyo kubika inshuro {x:.1f}"),
    "fx_m_trend": ("Grain moisture is rising ({v:+.2f}% per day)", "Ubuhehere bw'imyaka buriyongera ({v:+.2f}% ku munsi)"),
    "fx_rh_trend": ("Air humidity is rising ({v:+.1f}% per day)", "Ubuhehere bw'umwuka buriyongera ({v:+.1f}% ku munsi)"),
    "fx_heating": ("Grain is {v:.1f} °C warmer than the air: possible mould or insect activity",
                   "Imyaka irusha umwuka ubushyuhe {v:.1f} °C: hashobora kuba uruhumbu cyangwa udukoko"),
    "recs_header": ("Recommended actions", "Ingamba zisabwa"),
    "rec_offline": ("Press **Reset sensor connection**, then check the node's cable and battery. "
                    "Inspect the store by hand until readings return.",
                    "Kanda **Ongera uhuze sensa**, hanyuma urebe umugozi na batiri bya sensa. "
                    "Genzura ububiko n'amaso kugeza ibipimo bigarutse."),
    "rec_power": ("Restore power or start the generator: fans and the dehumidifier are stopped. "
                  "Open doors and vents on dry hours and inspect the grain by hand.",
                  "Garura umuriro cyangwa utangize moteri itanga umuriro: imiyaga n'imashini ikurura ubuhehere "
                  "byarahagaze. Fungura imiryango n'aho umwuka unyura mu masaha y'izuba kandi ugenzure imyaka n'amaso."),
    "rec_dry": ("Dry the grain below {m:g}% (sun-drying or a dryer) before storing it longer.",
                "Mwanike imyaka kugeza munsi ya {m:g}% (ku zuba cyangwa mu mashini) mbere yo kuyibika igihe kirekire."),
    "rec_bags": ("Keep bags on pallets and away from walls.", "Shyira imifuka ku mbaho kandi kure y'inkuta."),
    "rec_shade": ("Shade the store, ventilate at night and check for insects.",
                  "Shyira igicucu ku bubiko, winjize umwuka nijoro kandi urebe udukoko."),
    "rec_inspect": ("Record a manual inspection: check for mould, insects, smell and hot spots.",
                    "Andika igenzura ry'amaso: reba uruhumbu, udukoko, impumuro n'ahashyushye."),
    "rec_ok": ("Conditions are safe. Keep weekly inspections.",
               "Ibipimo ni byiza. Komeza igenzura rya buri cyumweru."),
    "eq_ventilation": ("Ventilation", "Kongera umwuka"),
    "eq_fan": ("Cooling fan", "Umuyaga ukonjesha"),
    "eq_dehum": ("Dehumidifier", "Imashini ikurura ubuhehere"),
    "eq_power_off": ("Power failure: the equipment cannot run.", "Umuriro wabuze: ibikoresho ntibishobora gukora."),
    "eq_help": ("Equipment is simulated: it changes the store's conditions over the next simulated hours.",
                "Ibikoresho ni iby'igerageza: bihindura ibipimo by'ububiko mu masaha akurikira."),
    "reset_conn": ("Reset sensor connection", "Ongera uhuze sensa"),
    "conn_reset_ok": ("Sensor at {store} reconnected.", "Sensa yo kuri {store} yongeye guhuzwa."),
    "conn_already": ("The sensor at {store} is already connected.", "Sensa yo kuri {store} isanzwe ihujwe."),
    "conn_no_power": ("No power at {store}: the sensor cannot reconnect until power returns.",
                      "Nta muriro kuri {store}: sensa ntishobora kongera guhuzwa umuriro utaragaruka."),
    "insp_header": ("Record manual inspection", "Andika igenzura ry'amaso"),
    "insp_inspector": ("Inspector", "Uwagenzuye"),
    "insp_findings": ("What did you find?", "Wabonye iki?"),
    "in_ok": ("No problems", "Nta kibazo"),
    "in_insects": ("Insects", "Udukoko"),
    "in_mould": ("Mould", "Uruhumbu"),
    "in_smell": ("Bad smell", "Impumuro mbi"),
    "in_hot": ("Hot spots in the grain", "Ahashyushye mu myaka"),
    "in_wet_bags": ("Wet or damaged bags", "Imifuka itose cyangwa yangiritse"),
    "in_rodents": ("Rodents", "Imbeba"),
    "insp_moisture": ("Moisture measured by hand (%, optional)", "Ubuhehere bwapimwe n'intoki (%, si ngombwa)"),
    "insp_notes": ("Notes / action taken", "Ibisobanuro / ingamba zafashwe"),
    "insp_save": ("Save inspection", "Bika igenzura"),
    "insp_saved": ("Inspection #{id} saved for {store}.", "Igenzura #{id} ryabitswe kuri {store}."),
    "insp_need_name": ("Enter the inspector's name.", "Andika izina ry'uwagenzuye."),
    "insp_recent": ("Recent inspections", "Igenzura riheruka"),
    "insp_none": ("No inspections recorded for this store yet.", "Nta genzura ryanditswe kuri ubu bubiko."),
    "ic_when": ("When", "Igihe"), "ic_by": ("Inspector", "Uwagenzuye"), "ic_findings": ("Findings", "Ibyabonetse"),
    "ic_moisture": ("Moisture (%)", "Ubuhehere (%)"), "ic_notes": ("Notes", "Ibisobanuro"),

    # ---- admin: login ----
    "admin_title": ("Admin", "Ubuyobozi"),
    "login_title": ("Admin login", "Kwinjira k'umuyobozi"),
    "username": ("Username", "Izina ukoresha"),
    "password": ("Password", "Ijambo ry'ibanga"),
    "login_btn": ("Log in", "Injira"),
    "login_bad": ("Wrong username or password.", "Izina cyangwa ijambo ry'ibanga si byo."),
    "login_hint": ("Demo accounts: **admin / admin123** (Admin) and **manager / manager123** (Warehouse manager). "
                   "Change them with the SFLP_ADMIN_PASSWORD and SFLP_MANAGER_PASSWORD environment variables.",
                   "Konti z'igerageza: **admin / admin123** (Umuyobozi) na **manager / manager123** "
                   "(Ushinzwe ububiko). Hindura amagambo y'ibanga ukoresheje SFLP_ADMIN_PASSWORD na "
                   "SFLP_MANAGER_PASSWORD."),
    "logged_in": ("Logged in as **{name}**  \nRole: {role}", "Winjiye nka **{name}**  \nUruhare: {role}"),
    "logout": ("Log out", "Sohoka"),
    "Admin": ("Admin", "Umuyobozi"),
    "Warehouse manager": ("Warehouse manager", "Ushinzwe ububiko"),

    # ---- admin: tabs ----
    "tab_reg": ("Register food", "Kwandika ibiribwa"),
    "tab_stock": ("Food in storage", "Ibiribwa biri mu bubiko"),
    "tab_limits": ("Crop storage limits", "Imbibi zo kubika"),

    # ---- admin: registration ----
    "reg_header": ("Register food entering a store", "Andika ibiribwa byinjira mu bubiko"),
    "facility": ("Storage facility", "Ububiko"),
    "crop_type": ("Crop / food type", "Igihingwa / ubwoko bw'ibiribwa"),
    "limits_info": ("**Storage limits for {crop}:** grain temperature {tmin:g}–{tmax:g} °C · "
                    "air humidity {rmin:g}–{rmax:g}% · grain moisture {mmin:g}–{m:g}%",
                    "**Imbibi zo kubika {crop}:** ubushyuhe bw'imyaka {tmin:g}–{tmax:g} °C · "
                    "ubuhehere bw'umwuka {rmin:g}–{rmax:g}% · ubuhehere bw'imyaka {mmin:g}–{m:g}%"),
    "crop_mismatch": ("{store} is set up for {crop}. The live sensors and AI risk for this store use {crop} settings.",
                      "{store} bwagenewe {crop}. Sensa n'ibyago (AI) by'ubu bubiko bikoresha ibipimo bya {crop}."),
    "qty": ("Quantity (kg)", "Ingano (kg)"),
    "bags": ("Number of bags", "Umubare w'imifuka"),
    "date_in": ("Date received", "Itariki byakiriwe"),
    "supplier": ("Supplier (farmer or cooperative)", "Uwabizanye (umuhinzi cyangwa koperative)"),
    "supplier_phone": ("Supplier phone", "Telefoni y'uwabizanye"),
    "intake_m": ("Grain moisture at intake (%)", "Ubuhehere bw'imyaka byinjira (%)"),
    "intake_t": ("Grain temperature at intake (°C)", "Ubushyuhe bw'imyaka byinjira (°C)"),
    "quality": ("Quality grade", "Urwego rw'ubuziranenge"),
    "Grade 1": ("Grade 1", "Urwego rwa 1"),
    "Grade 2": ("Grade 2", "Urwego rwa 2"),
    "Grade 3": ("Grade 3", "Urwego rwa 3"),
    "Ungraded": ("Ungraded", "Nta rwego"),
    "notes": ("Notes", "Ibisobanuro"),
    "notes_ph": ("Variety, condition of bags, pests seen...", "Ubwoko, uko imifuka imeze, udukoko twabonetse..."),
    "reg_btn": ("Register food", "Andika ibiribwa"),
    "e_qty": ("Enter the quantity in kg.", "Andika ingano mu kg."),
    "e_supplier": ("Enter the supplier's name.", "Andika izina ry'uwabizanye."),
    "reg_ok": ("Batch #{id} registered: {kg:,.0f} kg of {crop} into {store}.",
               "Icyiciro #{id} cyanditswe: {kg:,.0f} kg za {crop} muri {store}."),
    "reg_warn": ("Outside storage limits at intake: {b}. Dry the grain below {m:g}% and cool it before long storage.",
                 "Birenze imbibi byinjira: {b}. Mwanike imyaka kugeza munsi ya {m:g}% kandi muyikonjeshe "
                 "mbere yo kuyibika igihe kirekire."),

    # ---- admin: stock ----
    "no_batches": ("No food registered yet. Use the **Register food** tab.",
                   "Nta biribwa biranditswe. Koresha **Kwandika ibiribwa**."),
    "m_batches": ("Batches in storage", "Ibyiciro biri mu bubiko"),
    "m_food": ("Food in storage", "Ibiribwa biri mu bubiko"),
    "m_problems": ("Batches with intake problems", "Ibyiciro byinjiranye ikibazo"),
    "filter_store": ("Filter by store", "Hitamo ububiko"),
    "filter_status": ("Filter by status", "Hitamo uko bihagaze"),
    "In storage": ("In storage", "Biri mu bubiko"),
    "Dispatched": ("Dispatched", "Byasohotse"),
    "c_batch": ("Batch", "Icyiciro"), "c_store": ("Store", "Ububiko"), "c_crop": ("Crop", "Igihingwa"),
    "c_qty": ("Quantity (kg)", "Ingano (kg)"), "c_bags": ("Bags", "Imifuka"), "c_supplier": ("Supplier", "Uwabizanye"),
    "c_phone": ("Phone", "Telefoni"), "c_date_in": ("Date in", "Itariki byinjiye"),
    "c_moisture": ("Moisture (%)", "Ubuhehere (%)"), "c_temp": ("Temp (°C)", "Ubushyuhe (°C)"),
    "c_grade": ("Grade", "Urwego"), "c_check": ("Intake check", "Igenzura ryo kwinjira"),
    "c_status": ("Status", "Uko bihagaze"), "c_date_out": ("Date out", "Itariki byasohotse"),
    "c_by": ("Registered by", "Byanditswe na"), "c_notes": ("Notes", "Ibisobanuro"),
    "download": ("Download as CSV", "Kuramo (CSV)"),
    "dispatch_header": ("Dispatch food leaving the store", "Andika ibiribwa bisohoka mu bubiko"),
    "batch": ("Batch", "Icyiciro"),
    "date_out": ("Date out", "Itariki bisohotse"),
    "dispatch_btn": ("Mark as dispatched", "Emeza ko byasohotse"),
    "dispatched_toast": ("Batch #{id} marked as dispatched.", "Icyiciro #{id} cyanditswe ko cyasohotse."),

    # ---- admin: limits ----
    "limits_header": ("Storage limits per crop", "Imbibi zo kubika kuri buri gihingwa"),
    "limits_help": ("Each crop must stay between the lowest and highest value of every reading. "
                    "Readings outside these limits are flagged on the main dashboard, and stores on "
                    "automatic control switch their equipment to bring them back. "
                    "Temperature is the grain temperature, humidity is the air in the store.",
                    "Buri gihingwa kigomba kuguma hagati y'agaciro ko hasi n'ako hejuru kuri buri gipimo. "
                    "Ibipimo birenze izi mbibi bigaragazwa ku kibaho nyamukuru, kandi ububiko buri ku "
                    "igenzura ryikora bufungura ibikoresho kugira ngo bibisubize mu mbibi. "
                    "Ubushyuhe ni ubw'imyaka, ubuhehere ni ubw'umwuka uri mu bubiko."),
    "l_temp": ("Grain temperature (°C)", "Ubushyuhe bw'imyaka (°C)"),
    "l_rh": ("Air humidity (%)", "Ubuhehere bw'umwuka (%)"),
    "l_m": ("Grain moisture (%)", "Ubuhehere bw'imyaka (%)"),
    "l_range": ("{lo:g} – {hi:g}", "{lo:g} – {hi:g}"),
    "l_mmin": ("Min moisture (%)", "Ubuhehere bw'imyaka bwo hasi (%)"),
    "f_mmin": ("Minimum grain moisture (%)", "Ubuhehere bw'imyaka bwo hasi ntarengwa (%)"),
    "e_m_order": ("Minimum moisture must be lower than maximum moisture.",
                  "Ubuhehere bwo hasi bugomba kuba munsi y'ubwo hejuru."),

    # ---- admin: automatic warehouse control ----
    "tab_auto": ("Automatic warehouse control", "Igenzura ryikora ry'ububiko"),
    "auto_header": ("Automatic warehouse control", "Igenzura ryikora ry'ububiko"),
    "auto_help": ("Every store's equipment is switched **automatically**; nobody switches it by hand. When a "
                  "reading goes above or below the crop's storage limits, the matching machine turns on, and it "
                  "turns off again once the reading is safely back inside (5% humidity / 1 °C margin).",
                  "Ibikoresho by'ububiko bwose bikora **ubwabyo**; nta muntu ubifungura n'intoki. Igipimo "
                  "kirenze cyangwa kijya munsi y'imbibi z'igihingwa, imashini ibikwiye irafunguka, ikongera "
                  "igafunga igipimo kimaze gusubira mu mbibi neza (5% by'ubuhehere / 1 °C)."),
    "auto_rules_above": ("⬆️ **Above the limits:** grain temperature over **{tmax:g} °C** → cooling fan and "
                         "ventilation ON · air humidity over **{rmax:g}%** or grain moisture over **{mmax:g}%** → "
                         "dehumidifier (dries the air to {dh:g}%) and ventilation ON",
                         "⬆️ **Hejuru y'imbibi:** ubushyuhe bw'imyaka burenze **{tmax:g} °C** → umuyaga ukonjesha "
                         "no kongera umwuka birafunguka · ubuhehere bw'umwuka burenze **{rmax:g}%** cyangwa "
                         "ubw'imyaka burenze **{mmax:g}%** → imashini ikurura ubuhehere (yumisha umwuka kugeza "
                         "{dh:g}%) no kongera umwuka birafunguka"),
    "auto_rules_below": ("⬇️ **Below the limits:** grain temperature under **{tmin:g} °C** → heater ON (warms to "
                         "{ht:g} °C) · air humidity under **{rmin:g}%** or grain moisture under **{mmin:g}%** → "
                         "humidifier ON (moistens the air to {hu:g}%), ventilation and dehumidifier OFF",
                         "⬇️ **Munsi y'imbibi:** ubushyuhe bw'imyaka buri munsi ya **{tmin:g} °C** → icyuma "
                         "gishyushya kirafunguka (gishyushya kugeza {ht:g} °C) · ubuhehere bw'umwuka buri munsi ya "
                         "**{rmin:g}%** cyangwa ubw'imyaka buri munsi ya **{mmin:g}%** → imashini yongera ubuhehere "
                         "irafunguka (kugeza {hu:g}%), kongera umwuka n'imashini ikurura ubuhehere birafunga"),
    "auto_change_limits": ("To change when the machines switch, change the crop's limits in the "
                           "**Crop storage limits** tab.",
                           "Kugira ngo uhindure igihe imashini zifungukira, hindura imbibi z'igihingwa muri "
                           "**Imbibi zo kubika**."),
    "auto_no_limits": ("No storage limits for this crop: automatic control cannot run.",
                       "Nta mbibi z'iki gihingwa: igenzura ryikora ntirishobora gukora."),
    "auto_active": ("🤖 **Automatic control:** the equipment switches by itself when readings go above or below "
                    "the {crop} limits.",
                    "🤖 **Igenzura ryikora:** ibikoresho bifunguka ubwabyo iyo ibipimo birenze cyangwa bijya munsi "
                    "y'imbibi za {crop}."),
    "auto_limits_line": ("Limits: temperature {tmin:g}–{tmax:g} °C · humidity {rmin:g}–{rmax:g}% · "
                         "moisture {mmin:g}–{mmax:g}%",
                         "Imbibi: ubushyuhe {tmin:g}–{tmax:g} °C · ubuhehere bw'umwuka {rmin:g}–{rmax:g}% · "
                         "ubuhehere bw'imyaka {mmin:g}–{mmax:g}%"),
    "eq_state_on": ("ON", "Birakora"),
    "eq_state_off": ("OFF", "Birazimye"),
    "eq_no_status": ("Start the simulation to see the equipment working.",
                     "Tangiza igerageza kugira ngo urebe uko ibikoresho bikora."),
    "auto_log_header": ("Recent automatic actions", "Ibikorwa biheruka by'igenzura ryikora"),
    "auto_log_none": ("No switching yet: readings are within limits.",
                      "Nta gikoresho kirahinduka: ibipimo biri mu mbibi."),
    "auto_log_on": ("{eq} ON: {why}", "{eq} yafunguwe: {why}"),
    "auto_log_off": ("{eq} OFF: {why}", "{eq} yafunzwe: {why}"),
    "rec_auto": ("Automatic control is switching the equipment to bring readings back within limits.",
                 "Igenzura ryikora riri gufungura ibikoresho kugira ngo ibipimo bisubire mu mbibi."),
    "eq_heater": ("Heater", "Icyuma gishyushya"),
    "eq_humidifier": ("Humidifier", "Imashini yongera ubuhehere"),
    "l_crop": ("Crop", "Igihingwa"),
    "l_tmin": ("Min temp (°C)", "Ubushyuhe bwo hasi (°C)"), "l_tmax": ("Max temp (°C)", "Ubushyuhe bwo hejuru (°C)"),
    "l_rmin": ("Min humidity (%)", "Ubuhehere bwo hasi (%)"), "l_rmax": ("Max humidity (%)", "Ubuhehere bwo hejuru (%)"),
    "l_mmax": ("Max moisture (%)", "Ubuhehere bw'imyaka ntarengwa (%)"),
    "l_by": ("Last changed by", "Byahinduwe na"), "l_at": ("Changed at", "Igihe byahinduriwe"),
    "admin_only": ("Only the Admin can change crop limits.", "Umuyobozi wenyine ni we ushobora guhindura imbibi."),
    "edit_header": ("Change limits or add a crop", "Hindura imbibi cyangwa wongereho igihingwa"),
    "add_crop": ("+ Add a new crop", "+ Ongeraho igihingwa gishya"),
    "crop_name": ("Crop name", "Izina ry'igihingwa"),
    "f_tmin": ("Minimum temperature (°C)", "Ubushyuhe bwo hasi ntarengwa (°C)"),
    "f_tmax": ("Maximum temperature (°C)", "Ubushyuhe bwo hejuru ntarengwa (°C)"),
    "f_rmin": ("Minimum humidity (%)", "Ubuhehere bwo hasi ntarengwa (%)"),
    "f_rmax": ("Maximum humidity (%)", "Ubuhehere bwo hejuru ntarengwa (%)"),
    "f_mmax": ("Maximum grain moisture (%)", "Ubuhehere bw'imyaka ntarengwa (%)"),
    "save_limits": ("Save limits", "Bika imbibi"),
    "e_temp_order": ("Minimum temperature must be lower than maximum temperature.",
                     "Ubushyuhe bwo hasi bugomba kuba munsi y'ubwo hejuru."),
    "e_rh_order": ("Minimum humidity must be lower than maximum humidity.",
                   "Ubuhehere bwo hasi bugomba kuba munsi y'ubwo hejuru."),
    "e_rh_range": ("Humidity must be between 0 and 100%.", "Ubuhehere bugomba kuba hagati ya 0 na 100%."),
    "e_m_range": ("Maximum moisture must be between 0 and 40%.", "Ubuhehere bw'imyaka bugomba kuba hagati ya 0 na 40%."),
    "e_crop_name": ("Enter the crop name.", "Andika izina ry'igihingwa."),
    "e_crop_exists": ("A crop called '{name}' already exists.", "Igihingwa cyitwa '{name}' gisanzwe gihari."),
    "limits_saved": ("Limits for {name} saved.", "Imbibi za {name} zabitswe."),
    "new_crop_note": ("New crops can be registered and checked against their limits. "
                      "The AI risk prediction only covers maize, rice, sorghum and beans.",
                      "Ibihingwa bishya bishobora kwandikwa no kugenzurwa ku mbibi zabyo. "
                      "Iteganya ry'ibyago (AI) rireba gusa ibigori, umuceri, amasaka n'ibishyimbo."),
}


def tr(key: str, lang: str = "en", **kw) -> str:
    en, rw = STRINGS.get(key, (key, key))
    text = rw if lang == "rw" else en
    return text.format(**kw) if kw else text


def lang() -> str:
    return st.session_state.get("language", "en")


def t(key: str, **kw) -> str:
    return tr(key, lang(), **kw)


def crop_name(crop: str, label: str | None = None) -> str:
    """Crop name in the chosen language (Kinyarwanda names exist for the built-in crops)."""
    if lang() == "rw" and crop in CROPS:
        return CROPS[crop]["rw"].capitalize()
    return label or (CROPS[crop]["label"] if crop in CROPS else crop)


def _remember_choice():
    st.session_state.language = st.session_state._language_picker


_TOOLBAR_CSS = """
<style>
/* Pin the language button into Streamlit's top bar, right next to the ⋮ menu
   (where the Light / Dark theme setting lives). */
.st-key-lang_toolbar {
    position: fixed; top: 0.6rem; right: 3.6rem;
    z-index: 999991; width: auto !important;
}
.st-key-lang_toolbar button { padding: 0.1rem 0.6rem; min-height: 2rem; }
[data-testid="stPopoverBody"]:has(.sflp-nset) { min-width: 300px; max-width: 360px; }
/* The Deploy button would sit in the same spot; it is not used by this app. */
[data-testid="stAppDeployButton"] { display: none; }
/* Hide Streamlit's own footer so the app shows its own name only. */
footer, [data-testid="stFooter"] { visibility: hidden; height: 0; }
</style>
"""


def header(title_key: str):
    """Page title, plus the English / Kinyarwanda switch in the top bar beside the ⋮ menu."""
    st.session_state.setdefault("language", "en")
    # The picker's own key is reset per page, so copy the remembered choice into it.
    st.session_state._language_picker = st.session_state.language
    st.markdown(_TOOLBAR_CSS, unsafe_allow_html=True)
    from notify import ask_permission, settings_panel   # imported here: notify itself uses this module
    with st.container(key="lang_toolbar"):
        with st.popover(f"⚙️ {lang().upper()}", help=t("settings")):
            st.radio("🌐 Language / Ururimi", list(LANGS), format_func=LANGS.get,
                     key="_language_picker", on_change=_remember_choice)
            st.divider()
            st.markdown(f"**🔔 {t('ns_header')}**")
            settings_panel()
    ask_permission()
    from config import APP_TAGLINE, LOGO_SVG
    st.logo(LOGO_SVG, size="large")
    from branding import inject_app_manifest   # "Install app" shows Hunika, not Streamlit
    inject_app_manifest()
    st.title(t(title_key))
    if title_key == "app_title":
        st.caption(APP_TAGLINE)
