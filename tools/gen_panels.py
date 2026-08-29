"""Generate the language panel for the profile README.

Self-hosted on purpose. Every popular profile widget is a free third-party
deployment, and they go down: github-readme-stats returns 503 and
github-profile-trophy returns 402 as of Aug 2026. This reads the GitHub API and
writes an SVG into the repository, so the panel is served by GitHub itself and
cannot break.

Standard library only, and it runs on the workflow's built-in GITHUB_TOKEN.
"""

import json
import os
import urllib.request

USER = os.environ.get("PROFILE_USER", "Bhargs24")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "panels")

# Generated, vendored or markup output. Counting these measures the toolchain,
# not the person: Flutter emits the C++/CMake/Swift shells, Unity emits the
# shader files, and every web project emits HTML and CSS.
EXCLUDED = {
    "HTML", "CSS", "SCSS", "CMake", "Makefile", "Batchfile", "Shell",
    "Objective-C", "Objective-C++", "Swift", "C++", "C", "ShaderLab",
    "HLSL", "GLSL", "PowerShell", "Dockerfile", "Kotlin", "Java",
    "Wolfram Language",
}

COLOURS = {
    "Dart": "#00B4AB", "Python": "#3572A5", "C#": "#68217A",
    "TypeScript": "#3178C6", "JavaScript": "#F1E05A", "Go": "#00ADD8",
    "Ruby": "#701516", "Rust": "#DEA584",
}
FALLBACK = "#6346E6"

THEMES = {
    "dark":  dict(bg="#0D1117", panel="#161B22", edge="#30363D", title="#E6EDF3",
                  text="#C9D1D9", mute="#8B949E", track="#21262D"),
    "light": dict(bg="#FFFFFF", panel="#F6F8FA", edge="#D0D7DE", title="#1F2328",
                  text="#1F2328", mute="#59636E", track="#EAEEF2"),
}


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    totals, repos = {}, 0
    page = 1
    while True:
        batch = api("/users/%s/repos?per_page=100&type=owner&page=%d" % (USER, page))
        if not batch:
            break
        for repo in batch:
            if repo.get("private") or repo.get("archived"):
                continue
            repos += 1
            try:
                langs = api("/repos/%s/%s/languages" % (USER, repo["name"]))
            except Exception:
                continue
            for name, size in langs.items():
                if name in EXCLUDED:
                    continue
                totals[name] = totals.get(name, 0) + size
        page += 1
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in ranked) or 1
    return [(n, v * 100.0 / total) for n, v in ranked], repos


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(rows, repos, theme):
    t = THEMES[theme]
    W, H, PAD = 860, 232, 28
    bar_x, bar_y, bar_w, bar_h = PAD, 104, W - PAD * 2, 22
    font = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="Languages by share of authored code">'
        % (W, H, W, H),
        '<rect width="%d" height="%d" rx="10" fill="%s" stroke="%s"/>' % (W, H, t["panel"], t["edge"]),
        '<text x="%d" y="46" fill="%s" font-family="%s" font-size="17" font-weight="600">'
        'Languages by share of authored code</text>' % (PAD, t["title"], font),
        '<text x="%d" y="70" fill="%s" font-family="%s" font-size="12.5">'
        'across %d public repositories, with generated and markup files excluded</text>'
        % (PAD, t["mute"], font, repos),
        '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s"/>'
        % (bar_x, bar_y, bar_w, bar_h, bar_h // 2, t["track"]),
        '<clipPath id="clip"><rect x="%d" y="%d" width="%d" height="%d" rx="%d"/></clipPath>'
        % (bar_x, bar_y, bar_w, bar_h, bar_h // 2),
        '<g clip-path="url(#clip)">',
    ]

    x = float(bar_x)
    for name, pct in rows:
        w = bar_w * pct / 100.0
        out.append('<rect x="%.2f" y="%d" width="%.2f" height="%d" fill="%s"/>'
                   % (x, bar_y, max(w, 0.6), bar_h, COLOURS.get(name, FALLBACK)))
        x += w
    out.append("</g>")

    # legend, three per row
    lx, ly = PAD, 172
    for i, (name, pct) in enumerate(rows):
        cx = lx + (i % 3) * 272
        cy = ly + (i // 3) * 28
        out.append('<circle cx="%d" cy="%d" r="5.5" fill="%s"/>' % (cx + 6, cy - 4, COLOURS.get(name, FALLBACK)))
        out.append('<text x="%d" y="%d" fill="%s" font-family="%s" font-size="13.5" font-weight="600">%s</text>'
                   % (cx + 20, cy, t["text"], font, esc(name)))
        out.append('<text x="%d" y="%d" fill="%s" font-family="%s" font-size="13.5">%.1f%%</text>'
                   % (cx + 20 + 9 * len(name) + 10, cy, t["mute"], font, pct))
    out.append("</svg>")
    return "\n".join(out)


def main():
    rows, repos = collect()
    os.makedirs(OUT_DIR, exist_ok=True)
    for theme in THEMES:
        path = os.path.join(OUT_DIR, "languages-%s.svg" % theme)
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(rows, repos, theme))
        print("wrote", path)
    for name, pct in rows:
        print("  %-12s %5.1f%%" % (name, pct))


if __name__ == "__main__":
    main()
