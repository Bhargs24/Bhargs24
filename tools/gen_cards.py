"""Generate the project cards panel for the profile README.

Why this is generated rather than fetched from a service: every hosted profile
widget is a free third-party deployment and they go down. github-readme-stats,
which is what most people use for repo pin cards, returns 503 as of Aug 2026.
This writes an SVG into the repository, so GitHub serves it and it cannot break.

It shows the work, which is the one thing the contribution calendar does not,
so it adds information instead of restating a number with different weighting.

Standard library only. Runs on the workflow's built-in GITHUB_TOKEN.
"""

import json
import os
import urllib.request

USER = os.environ.get("PROFILE_USER", "Bhargs24")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "panels")

# Curated: the repo, and the one line worth reading about it. Kept here rather
# than pulled from the API description so the copy stays tight and in my voice.
CARDS = [
    ("plumbline", "Proves an AI agent actually ran its financial controls. 2,082 committed runs."),
    ("keel", "An AI founding team in your terminal. One idea to a shipped, tested product."),
    ("beachhead", "A market thesis in, a ranked target list out, scored from live hiring signal."),
    ("rqsm-engine", "Deterministic LLM orchestration. Byte-identical across 40 replays. A patent."),
    ("Unified-Operational-Data-Pipeline", "One source of truth across tools that contradict each other."),
    ("VRChemLab", "Real chemistry experiments in VR. Best AR/VR Project, VIT 2025."),
]

LANG_COLOUR = {
    "Python": "#3572A5", "C#": "#68217A", "TypeScript": "#3178C6",
    "Dart": "#00B4AB", "JavaScript": "#F1E05A", "Go": "#00ADD8",
}

THEMES = {
    "dark":  dict(card="#0D1117", edge="#30363D", title="#2F81F7", text="#8B949E", meta="#8B949E"),
    "light": dict(card="#FFFFFF", edge="#D0D7DE", title="#0969DA", text="#59636E", meta="#59636E"),
}

FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
COLS, CW, CH, GAP = 2, 422, 116, 16


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(text, limit=54):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > limit and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines[:2]


def card(x, y, name, blurb, lang, licence, t):
    o = ['<g transform="translate(%d,%d)">' % (x, y),
         '<rect width="%d" height="%d" rx="8" fill="%s" stroke="%s"/>' % (CW, CH, t["card"], t["edge"]),
         '<svg x="16" y="18" width="15" height="15" viewBox="0 0 16 16" fill="%s">'
         '<path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 '
         '0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 '
         '1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 '
         '1-.4.2l-1.45-1.087a.25.25 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/></svg>' % t["meta"],
         '<text x="40" y="30" fill="%s" font-family="%s" font-size="14.5" font-weight="600">%s</text>'
         % (t["title"], FONT, esc(name))]
    yy = 56
    for line in wrap(blurb):
        o.append('<text x="16" y="%d" fill="%s" font-family="%s" font-size="12.5">%s</text>'
                 % (yy, t["text"], FONT, esc(line)))
        yy += 17
    if lang:
        o.append('<circle cx="22" cy="%d" r="5.5" fill="%s"/>' % (CH - 20, LANG_COLOUR.get(lang, "#6346E6")))
        o.append('<text x="34" y="%d" fill="%s" font-family="%s" font-size="12">%s</text>'
                 % (CH - 16, t["meta"], FONT, esc(lang)))
    if licence:
        o.append('<text x="%d" y="%d" fill="%s" font-family="%s" font-size="12" text-anchor="end">%s</text>'
                 % (CW - 16, CH - 16, t["meta"], FONT, esc(licence)))
    o.append("</g>")
    return o


def build(theme, meta):
    rows = (len(CARDS) + COLS - 1) // COLS
    W = COLS * CW + (COLS - 1) * GAP
    H = rows * CH + (rows - 1) * GAP
    t = THEMES[theme]
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'role="img" aria-label="Selected projects">' % (W, H, W, H)]
    for i, (name, blurb) in enumerate(CARDS):
        x = (i % COLS) * (CW + GAP)
        y = (i // COLS) * (CH + GAP)
        m = meta.get(name, {})
        o += card(x, y, name, blurb, m.get("lang"), m.get("licence"), t)
    o.append("</svg>")
    return "\n".join(o)


def main():
    meta = {}
    for name, _ in CARDS:
        try:
            r = api("/repos/%s/%s" % (USER, name))
            lic = (r.get("license") or {}).get("spdx_id") or ""
            meta[name] = {"lang": r.get("language"),
                          "licence": "" if lic in ("NOASSERTION", "") else lic}
        except Exception as e:
            print("  skip meta for", name, e)
            meta[name] = {}
    os.makedirs(OUT, exist_ok=True)
    for theme in THEMES:
        p = os.path.join(OUT, "projects-%s.svg" % theme)
        with open(p, "w", encoding="utf-8") as f:
            f.write(build(theme, meta))
        print("wrote", p)


if __name__ == "__main__":
    main()
