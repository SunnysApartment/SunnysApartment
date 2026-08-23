"""Regenerate dark_mode.svg / light_mode.svg with live GitHub stats.

Runs daily via GitHub Actions. Standard library only, no dependencies.
Creative layer on top of the neofetch idea: a baked ASCII portrait, a type-in
boot animation (CSS keyframes survive GitHub's image proxy), a live language
bar and contribution heatmap drawn straight from the GraphQL API, and an
Arabic/RTL accent. Falls back to demo data when no token is present so it
always renders something (e.g. before ACCESS_TOKEN is configured).
"""
import calendar
import html
import json
import os
import urllib.request
from datetime import date, datetime, timezone

USER = "SunnysApartment"
NAME = "Khaled Omar"
TAGLINE = "Software Engineer"   # top-right label; set "" to hide
W = 56  # info column width in characters

# ---- editable free-text fields (the ones the API can't know) ----------------
FIELDS = dict(
    os="macOS, Windows",
    host="Egypt \u00b7 Remote",
    role="Software Engineer & Technical Lead",
    stack=".NET \u00b7 React \u00b7 WordPress \u00b7 AI \u00b7 Automation",
    ide="Claude Code, VS Code, Cursor",
    real="Arabic, English",
    focus="Building scalable digital products",
    specialty="Arabic / RTL web \u00b7 self-hosted tools",
    # Contact — leave a value as "" to hide that row entirely.
    email="",
    instagram="@khaled__omar",
    facebook="Always.Sunny.19",
    linkedin="",
)

ART = r"""
                        .:        ..                    
                      . .=--=. .==:--..                 
                 ..----...-:-..:==..-===-:              
              :..::::.     ..     ..:-:-==.             
            . :..                    ...::.--           
          --        .:-=+*######*=-:.     .:--.         
         .-:    .=+#%@@@@@@@@@@@@@@@%#+-.    :.         
             .=#@@@@@@@@@@@@@@@@@@@@@@@@%+:     .       
           .+%@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*:  :-.      
      ..  -%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%= .. .     
     -:  =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+ :.-.    
    .:  -@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+  .-.   
    .  .#@@@@@@@@%%%%@@@@@@@@@@@@@%%##**#%@@@@@#:  :-   
   ..  -%@@@%*=:.    :-+#%@@@@@%*=.     . :=%@@#: ....  
   .  ..#@@#-:=*****=-::-*@@@@@*=::=+**#*++==*@@+   .:  
       -@@#-+*###%%%%%*+=*%@@@%*:=#%%%%%##*+-.=%@=      
      .%@%: -+***##****++=#@@@%=+*****#*+==:   :%+=     
      -+#+    :--=====-:=*@@@@@*=---=-=-.      .##-     
     :=%%+.         ...:#@@@@@@@*=:.           -=%*     
     .*%##*-.        .-*%@@@@@@@@#=:.       .-+*##*.    
      #@%%#*=-::::-=+*#@@@@@@@@%#%%#*+=------=*#%##-.*+ 
  :=:.%@@%##*****#%%@@@@#==*#*+-.-*%@@@%%##*****%%%=-=- 
  -+*=%@@@@@@@@@@@@@@@%==-:-::..:-=+%@@@@@@@@@@%%@%*==  
   .++@@@@@@@@@@@@@@@@%#**##**+*==+*@@@@@@@@@@@@@@%*+*  
   -%+%@@@@@@@@@@@@@@@@%#%%%#%#%#*+*#%@@@@@@@@%@%%#*+*. 
   =%*+%@@@@@@@@@@@@%##%@%%%%%%####**+##%%@@%%#%%#*=##  
   -@#-*#%%@@@@@@@%*++**===+++++==-==--+**######*++=#+  
    *%-=+*%%%@@@%%*==++*#%%###***##**+==+*###*++++++#:  
    -%+-++*##%%@%%%%@@@@%#+-....-+*%%%%%%###*+==++=-=   
     --:++++**#%#%%@@@@@@%%**++*#%@@%%%##**+=-==++:     
        -==+++****#%%@@@@@@@@%%%%%@@%%#*+=--::----      
         :---====++*##%%@%@%%#%%#***++===-:.....:       
            .::-::--=+++***++=====---::::..             
          .:       ..::.::......  .           ::        
          .=.                                .=-        
          .+-.                               :+=        
          .++-.                             :-+=        
          .+++-:                           .:-++-       
           +++==:.                        ..:-=+*=      
"""

LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "C#": "#178600",
    "PHP": "#4F5D95", "Python": "#3572A5", "HTML": "#e34c26", "CSS": "#563d7c",
    "Shell": "#89e051", "C++": "#f34b7d", "Java": "#b07219", "Vue": "#41b883",
    "Dockerfile": "#384d54", "SCSS": "#c6538c",
}

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
PRIV_TOKEN = os.environ.get("ACCESS_TOKEN") or TOKEN


def gh(url, payload=None, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {token or TOKEN}",
                 "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or "{}")


def graphql(query, variables=None, token=None):
    resp = gh("https://api.github.com/graphql",
              {"query": query, "variables": variables or {}}, token)
    if resp.get("errors"):
        raise RuntimeError(resp["errors"])
    return resp["data"]


def age(b, t):
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    months = (t.month - b.month - (t.day < b.day)) % 12
    if t.day >= b.day:
        days = t.day - b.day
    else:
        pm_year, pm = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
        days = calendar.monthrange(pm_year, pm)[1] - b.day + t.day
    return years, months, days


def fetch_all():
    if not TOKEN:
        raise RuntimeError("no token -> demo")
    created = graphql(f'query {{ user(login:"{USER}") {{ createdAt }} }}')["user"]["createdAt"]
    joined = datetime.fromisoformat(created.replace("Z", "+00:00"))
    yr_aliases = "\n".join(
        f'y{y}: contributionsCollection(from:"{y}-01-01T00:00:00Z", to:"{y+1}-01-01T00:00:00Z")'
        " { totalCommitContributions restrictedContributionsCount }"
        for y in range(joined.year, datetime.now(timezone.utc).year + 1)
    )
    q = f"""
    query {{
      user(login: "{USER}") {{
        id createdAt
        followers {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {{
          totalCount
          nodes {{ name stargazerCount
            languages(first: 8, orderBy: {{field: SIZE, direction: DESC}}) {{
              edges {{ size node {{ name color }} }} }} }}
        }}
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {{ totalCount }}
        contributionsCollection {{ contributionCalendar {{ weeks {{ contributionDays {{ contributionCount }} }} }} }}
        {yr_aliases}
      }}
    }}"""
    u = graphql(q, token=PRIV_TOKEN)["user"]
    commits = sum(v["totalCommitContributions"] + v["restrictedContributionsCount"]
                  for k, v in u.items() if k.startswith("y") and isinstance(v, dict))
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            langs.setdefault(name, [0, e["node"]["color"] or "#888"])
            langs[name][0] += e["size"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]]
             for w in u["contributionsCollection"]["contributionCalendar"]["weeks"]]
    names = [n["name"] for n in u["repositories"]["nodes"]]
    stats = {
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "commits": commits,
        "uptime": age(joined.date(), date.today()),
        "langs": sorted(((n, v[0], v[1]) for n, v in langs.items()),
                        key=lambda x: -x[1])[:6],
        "weeks": weeks[-30:],
    }
    stats.update(loc(names, u["id"]))
    return stats


LOC_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      history(first: 100, author: {id: $id}, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { additions deletions }
      } } } } } }"""


def loc(repo_names, user_id):
    add = rem = 0
    for name in repo_names:
        cursor = None
        try:
            while True:
                ref = graphql(LOC_QUERY, {"owner": USER, "name": name, "id": user_id,
                                          "cursor": cursor}, token=PRIV_TOKEN)["repository"]["defaultBranchRef"]
                if ref is None:
                    break
                h = ref["target"]["history"]
                add += sum(n["additions"] for n in h["nodes"])
                rem += sum(n["deletions"] for n in h["nodes"])
                if not h["pageInfo"]["hasNextPage"]:
                    break
                cursor = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"loc {name}: {e}")
    return {"loc_add": add, "loc_del": rem, "loc": add - rem}


def demo_stats():
    """Fallback used when no token is available.

    Deliberately renders em-dashes instead of invented numbers: this output can
    end up public if the Action has not run yet, and a profile must never
    display statistics that are not really yours.
    """
    return {
        "followers": None, "repos": None, "contributed": None,
        "stars": None, "commits": None, "uptime": None,
        "langs": [],
        "weeks": [[0] * 7 for _ in range(30)],
        "loc_add": None, "loc_del": None, "loc": None,
    }


PALETTES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "art": "#F2A03D", "h": "#58a6ff",
             "k": "#ffa657", "v": "#c9d1d9", "d": "#484f58", "g": "#3fb950", "r": "#f85149",
             "ar": "#8b949e", "hm": ["#161b22", "#0e2a5e", "#1e3a8a", "#2B4CF2", "#5b76f5"],
             "g1": "#2B4CF2", "g2": "#F2A03D"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "art": "#b4611f", "h": "#0969da",
              "k": "#953800", "v": "#24292f", "d": "#afb8c1", "g": "#1a7f37", "r": "#cf222e",
              "ar": "#57606a", "hm": ["#ebedf0", "#a9b8ff", "#5b76f5", "#2B4CF2", "#1e3a8a"],
              "g1": "#0969da", "g2": "#b4611f"},
}


def kv(key, val, width=W):
    dots = "." * max(width - len(key) - len(str(val)) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (str(val), "v")]


def kv2(k1, v1, k2, v2):
    return kv(k1, v1, 30) + [(" | ", "d")] + kv(k2, v2, 23)


def rule(title=""):
    label = f"\u2500 {title} " if title else ""
    return [(label, "h"), ("\u2500" * (W - len(label)), "d")]


def info_lines(s):
    up = s["uptime"]
    uptime_txt = ("awaiting first sync" if up is None
                  else f"{up[0]} years, {up[1]} months, {up[2]} days on GitHub")
    n = lambda x: "—" if x is None else f"{x:,}"
    lang_summary = ", ".join(name for name, _, _ in s["langs"][:5]) or "\u2014"
    return [
        [(f"{USER.lower()}@github ", "h"), ("\u2500" * (W - len(USER) - 8), "d"),
         ("\u2588", "cur")],
        [],
        kv("OS", FIELDS["os"]),
        kv("Uptime", uptime_txt),
        kv("Host", FIELDS["host"]),
        kv("Kernel", FIELDS["role"]),
        kv("Stack", FIELDS["stack"]),
        kv("IDE", FIELDS["ide"]),
        [],
        kv("Languages.Code", lang_summary),
        kv("Languages.Real", FIELDS["real"]),
        kv("Specialty", FIELDS["specialty"]),
        kv("Focus", FIELDS["focus"]),
        [],
        rule("Contact"),
        *([kv("Email", FIELDS["email"])] if FIELDS["email"] else []),
        *([kv("LinkedIn", FIELDS["linkedin"])] if FIELDS["linkedin"] else []),
        *([kv("Instagram", FIELDS["instagram"])] if FIELDS["instagram"] else []),
        *([kv("Facebook", FIELDS["facebook"])] if FIELDS["facebook"] else []),
        [],
        rule("GitHub Stats"),
        kv2("Repos", (f"{s['repos']} {{Contributed: {s['contributed']}}}"
              if s["repos"] is not None else "—"), "Stars", n(s["stars"])),
        kv2("Commits", n(s["commits"]), "Followers", n(s["followers"])),
        [("Lines of Code: ", "k"), (n(s["loc"]), "v"), (" ( ", "d"),
         (n(s["loc_add"]) + "++", "g"), (", ", "d"),
         (n(s["loc_del"]) + "--", "r"), (" )", "d")],
    ]


def lang_bar(s, p, x, y, w):
    if not s["langs"]:
        return (f'<text x="{x}" y="{y}" fill="{p["h"]}" font-size="12">─ Languages</text>'
                f'<text x="{x}" y="{y+22}" fill="{p["d"]}" font-size="11">awaiting first sync</text>')
    total = sum(sz for _, sz, _ in s["langs"]) or 1
    out = [f'<text x="{x}" y="{y}" fill="{p["h"]}" font-size="12">\u2500 Languages</text>']
    bx, by, bh = x, y + 10, 14
    seg = bx
    out.append(f'<clipPath id="lc"><rect x="{bx}" y="{by}" width="{w}" height="{bh}" rx="4"/></clipPath>')
    out.append(f'<g clip-path="url(#lc)">')
    for name, sz, col in s["langs"]:
        seg_w = w * sz / total
        c = LANG_COLORS.get(name, col or "#888")
        out.append(f'<rect x="{seg:.1f}" y="{by}" width="{seg_w:.1f}" height="{bh}" fill="{c}"/>')
        seg += seg_w
    out.append("</g>")
    ly = by + bh + 18
    lx = x
    for name, sz, col in s["langs"][:5]:
        pct = 100 * sz / total
        c = LANG_COLORS.get(name, col or "#888")
        out.append(f'<circle cx="{lx+4}" cy="{ly-4}" r="4" fill="{c}"/>')
        label = f"{name} {pct:.0f}%"
        out.append(f'<text x="{lx+13}" y="{ly}" fill="{p["v"]}" font-size="11">{html.escape(label)}</text>')
        lx += 15 + len(label) * 6.6
    return "\n".join(out)


def heatmap(s, p, x, y):
    weeks = s["weeks"]
    mx = max((max(w) for w in weeks if w), default=1) or 1
    cell, gap = 9, 2
    out = [f'<text x="{x}" y="{y}" fill="{p["h"]}" font-size="12">\u2500 Contribution activity</text>']
    gy = y + 12
    for wi, week in enumerate(weeks):
        for di, cnt in enumerate(week):
            lvl = 0 if cnt == 0 else min(4, 1 + int(cnt / mx * 3.999))
            cx = x + wi * (cell + gap)
            cyy = gy + di * (cell + gap)
            out.append(f'<rect x="{cx}" y="{cyy}" width="{cell}" height="{cell}" rx="2" '
                       f'fill="{p["hm"][lvl]}"/>')
    return "\n".join(out)


def render(mode, s):
    p = PALETTES[mode]
    Wd, Hd = 1020, 800
    style = f"""
    @keyframes rise {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
    @keyframes blink {{ 0%,49% {{ opacity: 1 }} 50%,100% {{ opacity: 0 }} }}
    .art {{ opacity: 0; animation: rise .9s ease forwards .1s; fill: {p['art']}; }}
    .ln {{ opacity: 0; animation: rise .4s ease forwards; }}
    .cur {{ fill: {p['h']}; animation: blink 1.1s step-end infinite; }}
    .foot {{ opacity: 0; animation: rise .6s ease forwards 1.9s; }}
    text {{ font-family: Consolas, "DejaVu Sans Mono", Menlo, monospace; }}
    """
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wd}" height="{Hd}" '
        f'viewBox="0 0 {Wd} {Hd}" font-size="13px">',
        f'<defs><style>{style}</style>'
        f'<linearGradient id="tt" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{p["g1"]}"/><stop offset="1" stop-color="{p["g2"]}"/>'
        f'</linearGradient></defs>',
        f'<rect x="0.5" y="0.5" width="{Wd-1}" height="{Hd-1}" rx="12" '
        f'fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    # window dots + arabic accent
    out += [
        f'<circle cx="26" cy="26" r="6" fill="#ff5f56"/>',
        f'<circle cx="46" cy="26" r="6" fill="#F2A03D"/>',
        f'<circle cx="66" cy="26" r="6" fill="#3fb950"/>',
        f'<text x="{Wd-34}" y="32" text-anchor="end" fill="{p["ar"]}" '
        f'font-size="15">{html.escape(TAGLINE)}</text>',
    ]
    # portrait
    out.append('<g class="art" xml:space="preserve">')
    for i, line in enumerate(ART.strip("\n").split("\n")):
        out.append(f'<text x="26" y="{72 + i*12.4:.1f}" fill="{p["art"]}" font-size="11.5">{html.escape(line)}</text>')
    out.append("</g>")
    # name under portrait
    out.append(f'<text x="26" y="{72 + 39*12.4 + 26:.0f}" class="ln" style="animation-delay:1.6s" '
               f'fill="url(#tt)" font-size="20" font-weight="700">{html.escape(NAME)}</text>')
    # info panel (staggered)
    for i, segs in enumerate(info_lines(s)):
        if not segs:
            continue
        spans = "".join(
            f'<tspan class="cur">{html.escape(t)}</tspan>' if c == "cur"
            else f'<tspan fill="{p[c] if c != "h" else p["h"]}">{html.escape(t)}</tspan>'
            for t, c in segs)
        delay = 0.3 + i * 0.06
        out.append(f'<text x="545" y="{56 + i*20.5:.1f}" xml:space="preserve" class="ln" '
                   f'style="animation-delay:{delay:.2f}s">{spans}</text>')
    # footer widgets
    out.append(f'<line x1="24" y1="628" x2="{Wd-26}" y2="628" stroke="{p["border"]}"/>')
    out.append('<g class="foot">')
    out.append(lang_bar(s, p, 28, 660, 430))
    out.append(heatmap(s, p, 545, 650))
    out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


def selfcheck():
    assert age(date(1989, 1, 15), date(2026, 7, 10)) == (37, 5, 25)
    assert age(date(2000, 1, 1), date(2026, 1, 1)) == (26, 0, 0)
    assert len("".join(t for t, _ in kv("OS", "Windows, macOS"))) == W


if __name__ == "__main__":
    selfcheck()
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    try:
        stats = fetch_all()
        print("live stats:", {k: v for k, v in stats.items() if k not in ("weeks", "langs")})
    except Exception as e:
        # Locally: fall back so you can preview the layout without a token.
        # In CI: fail loudly. Silently committing em-dashes would turn a broken
        # sync into a green run and leave the profile showing placeholders.
        if in_ci:
            raise SystemExit(
                f"\nERROR: could not fetch GitHub stats: {e}\n"
                "Check that ACCESS_TOKEN is set (Settings > Secrets and variables > Actions)\n"
                "and that the token has the 'repo' (or 'public_repo') scope.\n"
            )
        print("no token -> rendering placeholder locally:", e)
        stats = demo_stats()
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode, stats))
    print("wrote dark_mode.svg, light_mode.svg")
