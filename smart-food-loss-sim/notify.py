"""Desktop (browser) notifications.

When the app opens, a small card asks the user to allow notifications. After that, every time a store's
risk level goes up (or comes back to Good) the computer shows a pop-up notification, even when the
browser tab is in the background. It uses the browser's Notification API, which works on
http://localhost (or https); nothing is sent to any outside service.
"""
import json

import streamlit as st

from alerts import check_and_alert
from i18n import lang, t
from predictor import predict_all

_PROMPT_JS = """
<script>
(function () {
  if (!("Notification" in window) || Notification.permission !== "default") return;
  if (sessionStorage.getItem("sflp_notify_later") || document.getElementById("sflp-notify")) return;
  const T = %(text)s;
  const app = document.querySelector(".stApp") || document.body;
  const cs = getComputedStyle(app);
  const box = document.createElement("div");
  box.id = "sflp-notify";
  box.setAttribute("role", "dialog");
  box.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:1000000;max-width:340px;" +
    "padding:14px 16px;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.25);" +
    "border:1px solid rgba(128,128,128,.3);font-family:inherit;font-size:14px;line-height:1.4;" +
    "background:" + cs.backgroundColor + ";color:" + cs.color + ";";
  box.innerHTML = '<div style="font-weight:700;margin-bottom:4px"></div><div style="opacity:.85"></div>' +
    '<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">' +
    '<button data-a="later" style="padding:6px 12px;border-radius:8px;border:1px solid rgba(128,128,128,.5);background:transparent;color:inherit;cursor:pointer"></button>' +
    '<button data-a="allow" style="padding:6px 12px;border-radius:8px;border:0;background:#2c7f4a;color:#fff;font-weight:600;cursor:pointer"></button></div>';
  box.children[0].textContent = " " + T.title;
  box.children[1].textContent = T.body;
  box.querySelector('[data-a="later"]').textContent = T.later;
  box.querySelector('[data-a="allow"]').textContent = T.allow;
  box.querySelector('[data-a="later"]').onclick = function () {
    sessionStorage.setItem("sflp_notify_later", "1"); box.remove();
  };
  box.querySelector('[data-a="allow"]').onclick = function () {
    Notification.requestPermission().then(function (p) {
      box.remove();
      if (p === "granted") new Notification(T.ok_title, {body: T.ok_body, tag: "sflp-welcome"});
    });
  };
  document.body.appendChild(box);
})();
</script>
"""

_PUSH_JS = """
<script>
(function () {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  const items = %(items)s;
  let seen = [];
  try { seen = JSON.parse(sessionStorage.getItem("sflp_seen") || "[]"); } catch (e) {}
  items.forEach(function (it) {
    if (seen.indexOf(it.id) >= 0) return;
    seen.push(it.id);
    const n = new Notification(it.title, {body: it.body, tag: it.tag, requireInteraction: it.urgent});
    n.onclick = function () { window.focus(); n.close(); };
  });
  sessionStorage.setItem("sflp_seen", JSON.stringify(seen.slice(-50)));
})();
</script>
"""

_SETTINGS_JS = """
<div class="sflp-nset" style="font-size:14px;line-height:1.45"></div>
<script>
(function () {
  const T = %(text)s;
  const btn = "padding:6px 12px;margin-top:8px;border-radius:8px;border:0;background:#2c7f4a;color:#fff;font-weight:600;cursor:pointer";
  function draw(el) {
    el.innerHTML = "";
    const msg = document.createElement("div");
    let label = null, action = null;
    if (!("Notification" in window)) {
      msg.textContent = " " + T.unsupported;
    } else if (Notification.permission === "granted") {
      msg.textContent = " " + T.on;
      label = T.test;
      action = function () { new Notification(T.test_title, {body: T.test_body, tag: "sflp-test"}); };
    } else if (Notification.permission === "denied") {
      msg.textContent = " " + T.blocked;
    } else {
      msg.textContent = " " + T.off;
      label = " " + T.allow;
      action = function () {
        Notification.requestPermission().then(function (p) {
          const card = document.getElementById("sflp-notify");
          if (card) card.remove();
          if (p === "granted") new Notification(T.test_title, {body: T.test_body, tag: "sflp-test"});
          drawAll();
        });
      };
    }
    el.appendChild(msg);
    if (label) {
      const b = document.createElement("button");
      b.type = "button"; b.style.cssText = btn; b.textContent = label; b.onclick = action;
      el.appendChild(b);
    }
  }
  function drawAll() { document.querySelectorAll(".sflp-nset").forEach(draw); }
  drawAll();
})();
</script>
"""

_ICON = {"Good": "✅", "Watch": "⚠️", "Act now": "🚨"}


def _js(value) -> str:
    """JSON that is safe to place inside a <script> tag."""
    return json.dumps(value).replace("</", "<\\/")


def ask_permission():
    """Show the 'Allow notifications' card (only until the user answers it)."""
    text = {k: t("nt_" + k) for k in ("title", "body", "later", "allow", "ok_title", "ok_body")}
    st.html(_PROMPT_JS % {"text": _js(text)}, unsafe_allow_javascript=True)


def settings_panel():
    """Notifications section of the top-bar settings menu: status plus an Allow (or Test) button.
    The button is plain HTML so the click counts as a user action, which browsers require."""
    keys = ("unsupported", "on", "off", "blocked", "allow", "test", "test_title", "test_body")
    text = {k: t("ns_" + k) for k in keys}
    st.html(_SETTINGS_JS % {"text": _js(text)}, unsafe_allow_javascript=True)


def show_alerts(alerts: list[dict]):
    """Toast in the page and a desktop notification for each new alert."""
    if not alerts:
        return
    items = []
    for a in alerts:
        st.toast(t("sms_toast") + a["line"])
        lines = a["text"].splitlines()
        body = lines[1] if lang() == "rw" and len(lines) > 1 else lines[0]
        items.append({"id": a["id"], "tag": "sflp-" + a["store"], "urgent": a["level"] == 2,
                      "title": f"{_ICON.get(a['level_name'], '')} {a['store']}: {t(a['level_name'])}",
                      "body": body})
    st.html(_PUSH_JS % {"items": _js(items)}, unsafe_allow_javascript=True)


@st.fragment(run_every=5)
def alert_watch():
    """Check the stores every 5 seconds on pages that do not do it themselves."""
    preds = predict_all()
    if preds:
        show_alerts(check_and_alert(preds))
