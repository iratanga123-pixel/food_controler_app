"""Makes the "Install app" feature of Chrome / Edge show Hunika instead of Streamlit.

Streamlit ships its own manifest.json (name "Streamlit", red logo). This module injects a
Hunika manifest into the page, plus the icon and title for the home screen / desktop shortcut.
The icons are served from the static/ folder (enabled in .streamlit/config.toml).

Browsers read the manifest when you press "Install", so this must run before installing.
If an old "Streamlit" app is already installed, uninstall it and install again.
"""
import json

import streamlit.components.v1 as components

from config import APP_NAME, APP_TAGLINE

_SCRIPT = """
<script>
(function () {
  try {
    // On Streamlit Cloud the app runs in an iframe (same origin) inside a wrapper page, and the
    // browser's "Install app" reads the wrapper's manifest. So the change goes to the top page too.
    var loc = window.parent.location;
    var origin = loc.origin, base = origin + loc.pathname.replace(/\\/$/, "") + "/app/static/";
    var docs = [window.parent.document];
    try { if (window.top.document !== docs[0]) docs.push(window.top.document); } catch (e) {}
    var cfg = %s;
    var manifest = {
      name: cfg.name + " - " + cfg.tagline, short_name: cfg.name, description: cfg.tagline,
      start_url: origin + "/", scope: origin + "/", display: "standalone",
      background_color: "#f4faf6", theme_color: "#1d6b52",
      icons: [
        {src: base + "hunika-192.png", sizes: "192x192", type: "image/png", purpose: "any"},
        {src: base + "hunika-512.png", sizes: "512x512", type: "image/png", purpose: "any"},
        {src: base + "hunika-512.png", sizes: "512x512", type: "image/png", purpose: "maskable"}
      ]
    };
    var url = URL.createObjectURL(new Blob([JSON.stringify(manifest)], {type: "application/manifest+json"}));

    docs.forEach(function (doc) {
      function setLink(rel, href, extra) {
        // Replace every existing link of this kind (Streamlit has several icon links).
        doc.querySelectorAll('link[rel~="' + rel + '"]').forEach(function (old) { old.remove(); });
        var el = doc.createElement("link");
        el.setAttribute("rel", rel); el.setAttribute("href", href);
        for (var k in (extra || {})) el.setAttribute(k, extra[k]);
        doc.head.appendChild(el);
      }
      function setMeta(name, content) {
        var el = doc.querySelector('meta[name="' + name + '"]') || doc.createElement("meta");
        el.setAttribute("name", name); el.setAttribute("content", content);
        if (!el.parentNode) doc.head.appendChild(el);
      }
      setLink("manifest", url);
      setLink("icon", base + "hunika-192.png", {type: "image/png"});
      setLink("apple-touch-icon", base + "hunika-192.png");
      setMeta("theme-color", "#1d6b52");
      setMeta("application-name", cfg.name);
    });
  } catch (e) { console.warn("Hunika manifest not applied:", e); }
})();
</script>
"""


def inject_app_manifest() -> None:
    components.html(_SCRIPT % json.dumps({"name": APP_NAME, "tagline": APP_TAGLINE}), height=0)
