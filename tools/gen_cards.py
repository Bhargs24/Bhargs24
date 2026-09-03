"""Generate one clickable project card per repository, for the profile README.

Two reasons this is generated rather than fetched from a service:
github-readme-stats, which is what most profiles use for repo pin cards, has
been returning 503; and a single SVG cannot have per-card links, so each card is
its own file and the README wraps each one in its own anchor.

Standard library only. Runs on the workflow's built-in GITHUB_TOKEN.
"""

import json
import os
import urllib.request

USER = os.environ.get("PROFILE_USER", "Bhargs24")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "panels")

# Chosen on what is actually in each repo, not on what sounds good.
# note = a fact the card can show that a reader would otherwise have to dig for.
CARDS = [
    ("plumbline", "Proves an AI agent really ran its financial controls, and names the step where it did not.", "2,082 committed runs"),
    ("keel", "An AI founding team in your terminal. One idea to a planned, designed, tested product.", "8-stage pipeline"),
    ("rqsm-engine", "Deterministic LLM orchestration. Control flow leaves the model, so sessions replay exactly.", "Patent IN202641086881"),
    ("beachhead", "A market thesis in, a ranked target list out, scored from live hiring signal.", "32 companies mapped"),
    ("Unified-Operational-Data-Pipeline", "One source of truth across tools that contradict each other, resolved by ownership rules.", "Governance layer"),
    ("Inferno", "A VR fire drill you can fail, graded against the building's real evacuation protocol.", "Best UI/UX, Yantra 2025"),
]

LANG_COLOUR = {
    "Python": "#3572A5", "C#": "#68217A", "TypeScript": "#3178C6",
    "Dart": "#00B4AB", "JavaScript": "#F1E05A", "Go": "#00ADD8", "HTML": "#E34C26",
}

THEMES = {
    "dark":  dict(card="#0D1117", edge="#30363D", title="#2F81F7", text="#8B949E",
                  meta="#8B949E", chip="#161B22", chipEdge="#30363D", chipText="#C9D1D9"),
    "light": dict(card="#FFFFFF", edge="#D0D7DE", title="#0969DA", text="#59636E",
                  meta="#59636E", chip="#F6F8FA", chipEdge="#D0D7DE", chipText="#1F2328"),
}

FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
W, H = 440, 132

REPO_ICON = (
    '<path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 '
    '0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 '
    '1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 '
    '1-.4.2l-1.45-1.087a.25.25 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/>'
)


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


def wrap(text, limit=56):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > limit and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines[:2]


def render(name, blurb, note, lang, theme):
    t = THEMES[theme]
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'role="img" aria-label="%s">' % (W, H, W, H, esc(name)),
         '<rect x="0.5" y="0.5" width="%d" height="%d" rx="8" fill="%s" stroke="%s"/>'
         % (W - 1, H - 1, t["card"], t["edge"]),
         '<svg x="16" y="17" width="16" height="16" viewBox="0 0 16 16" fill="%s">%s</svg>'
         % (t["meta"], REPO_ICON),
         '<text x="40" y="30" fill="%s" font-family="%s" font-size="15" font-weight="600">%s</text>'
         % (t["title"], FONT, esc(name))]
    y = 56
    for line in wrap(blurb):
        o.append('<text x="16" y="%d" fill="%s" font-family="%s" font-size="12.5">%s</text>'
                 % (y, t["text"], FONT, esc(line)))
        y += 17
    # the fact chip
    cw = int(7.0 * len(note)) + 22
    o.append('<rect x="16" y="%d" width="%d" height="22" rx="11" fill="%s" stroke="%s"/>'
             % (H - 36, cw, t["chip"], t["chipEdge"]))
    o.append('<text x="%d" y="%d" fill="%s" font-family="%s" font-size="11.5" font-weight="500">%s</text>'
             % (16 + cw / 2, H - 21, t["chipText"], FONT, esc(note)))
    o[-1] = o[-1].replace('<text x=', '<text text-anchor="middle" x=', 1)
    if lang:
        o.append('<circle cx="%d" cy="%d" r="5.5" fill="%s"/>' % (W - 16 - 7 * len(lang) - 14, H - 25, LANG_COLOUR.get(lang, "#6346E6")))
        o.append('<text x="%d" y="%d" fill="%s" font-family="%s" font-size="12" text-anchor="end">%s</text>'
                 % (W - 16, H - 21, t["meta"], FONT, esc(lang)))
    o.append("</svg>")
    return "\n".join(o)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, blurb, note in CARDS:
        try:
            lang = (api("/repos/%s/%s" % (USER, name)) or {}).get("language")
        except Exception:
            lang = None
        slug = name.lower()
        for theme in THEMES:
            p = os.path.join(OUT, "card-%s-%s.svg" % (slug, theme))
            with open(p, "w", encoding="utf-8") as f:
                f.write(render(name, blurb, note, lang, theme))
        print("  card:", name, "|", lang)


if __name__ == "__main__":
    main()
