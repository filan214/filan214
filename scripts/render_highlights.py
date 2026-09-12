"""Animated project evidence cards. Counts describe public source, never user finances."""
from common import DATA, read_json, run
from render_build_spotlight import sync_label
from svg import chrome, rect, save, shorten, svg, text, wipe

STYLES = '''
:root{--violet:#6f42c1;--wash:#eef8f2;--v-wash:#f5f0fc}
@media(prefers-color-scheme:dark){:root{--violet:#c8a5ff;--wash:#11251c;--v-wash:#211a30}}
.violet{fill:var(--violet)} .wash{fill:var(--wash)} .v-wash{fill:var(--v-wash)}
.display{font-family:Arial,Helvetica,sans-serif;font-weight:700;letter-spacing:-.7px}
.outline{fill:none;stroke:var(--line)}
.trace{fill:none;stroke:var(--accent);stroke-width:2.3;stroke-linejoin:round;stroke-linecap:round}
.epl .trace{stroke:var(--violet)} .epl .area{fill:var(--violet)}
.area{fill:var(--accent);opacity:.08} .guide{fill:none;stroke:var(--line);stroke-dasharray:3 5}
.connector{fill:none;stroke:var(--line);stroke-width:1.5}
'''


def activity(project, x, y, width=304, height=106):
    days = project["activity_days"]
    counts = [day["count"] for day in days]
    if not counts or any(type(n) is not int or n < 0 for n in counts):
        raise ValueError("Highlight history needs nonnegative daily commit counts")
    peak, total = max(counts), sum(counts)
    body = text(x, y, f"{len(days)}-DAY BUILD ACTIVITY", "muted bold", 10)
    body += text(x+width, y, f"{total} commits", "bold", 11, extra='text-anchor="end"')
    top, bottom = y+20, y+height-21
    for part in range(3):
        at = top + (bottom-top)*part/2
        body += f'<path d="M{x} {at}H{x+width}" class="guide"/>'
    coords = [(round(x+width*i/max(1, len(counts)-1), 2), round(bottom-(bottom-top)*n/max(1, peak), 2)) for i, n in enumerate(counts)]
    points = " ".join(f"{a},{b}" for a, b in coords)
    chart = f'<polygon points="{x},{bottom} {points} {x+width},{bottom}" class="area"/>'
    chart += f'<polyline points="{points}" class="trace"/>'
    body += wipe("build-history", x-2, top-3, width+4, bottom-top+6, chart, duration=1.25)
    body += text(x, y+height, days[0]["date"][5:], "muted tiny")
    body += text(x+width, y+height, days[-1]["date"][5:] + f" · peak {peak}/day", "muted tiny", extra='text-anchor="end"')
    return body


def workflow_label(project):
    item = project["workflow"]
    if item is None:
        return "No public workflow run returned"
    state = item["conclusion"] or item["status"]
    revision = "current tip" if item["matches_tip"] else item["head_sha"][:7]
    return f"{shorten(item['name'], 19)}: {state} · {revision}"


def code_mix(project, x, y, width=804):
    values = sorted(((k, v) for k, v in project["languages"].items() if v > 0), key=lambda row: (-row[1], row[0]))
    total, cursor = sum(v for _, v in values), x
    body = text(x, y, "CODE MIX", "muted tiny")
    labels = " · ".join(f"{name} {v/total:.0%}" for name, v in values[:3]) if total else "Not reported"
    body += text(x+width, y, shorten(labels, 90), "muted tiny", extra='text-anchor="end"')
    for i, (_, count) in enumerate(values):
        segment = width*count/total
        body += rect(cursor, y+10, segment, 4, ("accent", "cyan", "violet", "muted")[i % 4], 0)
        cursor += segment
    return body


def footer(project, data, y):
    return (text(28, y, "SOURCE " + project["commit"]["sha"][:7] + " · " + project["commit"]["created_at"][:10], "muted tiny")
            + text(832, y, "fetched " + sync_label(data), "muted tiny", extra='text-anchor="end"'))


def finance(data):
    project = data["projects"]["finance"]
    inv, app = project["inventory"], data["app"]
    body = chrome(860, 462, "showcase --project AIFinanceTracker", "01 / PRODUCT SPOTLIGHT")
    body += text(28, 75, "AI + PERSONAL FINANCE", "accent bold", 10)
    body += text(28, 113, "Smart Finn Track", "display", 32)
    body += text(28, 137, "Ask your money better questions.", "muted", 13)
    body += rect(598, 64, 234, 71, "wash", 10)
    body += text(614, 88, "PUBLIC APP", "accent bold", 10)
    label = "Landing page reachable" if app["reachable"] else "Landing page not verified"
    body += text(614, 109, label, "", 10)
    body += text(614, 124, "HTTP " + str(app["http_status"] or "unavailable") + " · checked at fetch", "muted", 8.5)
    body += '<path d="M28 158H832" class="line"/>'
    labels = [("AI TOOLS", "—" if inv["tools"] is None else str(len(inv["tools"]))),
              ("APP VIEWS", str(len(inv["routes"]))), ("LOCALE FILES", str(len(inv["locales"])))]
    for i, (label, value) in enumerate(labels):
        x = 28+i*158
        body += text(x, 180, label, "muted tiny") + text(x, 208, value, "display accent", 26)
    body += text(28, 230, "Measured from the current public source", "muted tiny")
    for i, feature in enumerate(inv["features"]):
        x, y = 28 + (i % 2)*235, 250+(i//2)*48
        body += rect(x, y, 221, 37, "panel", 6)
        body += text(x+12, y+23, "●" if feature["present"] else "○", "accent" if feature["present"] else "muted", 10)
        body += text(x+31, y+23, feature["label"], "", 11)
    body += text(28, 359, "Source routes · explore the product via Open app below", "muted", 9)
    body += rect(514, 173, 318, 196, "panel", 10)
    body += activity(project, 530, 197, 286, 106)
    body += text(530, 326, "Default branch · all authors · Jakarta dates", "muted", 8.2)
    body += text(530, 351, shorten(workflow_label(project), 46), "muted", 9)
    body += code_mix(project, 28, 397)
    body += footer(project, data, 442)
    tools = "unavailable" if inv["tools"] is None else ", ".join(inv["tools"])
    desc = (f"Smart Finn Track, an AI-assisted personal finance app. Public source at {project['commit']['sha']}. "
            f"AI tools: {tools}. {len(inv['routes'])} app page files; {len(inv['locales'])} locale files. "
            f"Features shown when their API route exists: {', '.join(f['label'] for f in inv['features'] if f['present'])}. "
            f"Landing page HTTP {app['http_status']}, checked {app['checked_at']}; not an authenticated app health or uptime test. "
            f"Daily default-branch commits, all authors: {[d['count'] for d in project['activity_days']]}. "
            f"Latest workflow observation: {workflow_label(project)}. Fetched {data['fetched_at']}.")
    return svg(860, 462, "Smart Finn Track — project spotlight", desc, body, styles=STYLES)


def epl(data):
    project = data["projects"]["epl"]
    inv = project["inventory"]
    body = chrome(860, 530, "showcase --project epl-season-forecast", "02 / SPORTS ANALYTICS")
    body += '<g class="epl">'
    body += text(28, 75, "FOOTBALL × PROBABILISTIC MODELING", "violet bold", 10)
    body += text(28, 112, "EPL Season Forecast", "display", 31)
    body += text(28, 138, "From match history to a distribution of possible seasons.", "muted", 12)
    body += rect(675, 67, 157, 29, "v-wash", 14)
    body += text(753, 86, "SOURCE EXPLORER", "violet bold", 9, extra='text-anchor="middle"')
    # This diagram visualizes observed source structure, not a running forecast.
    for i, stage in enumerate(inv["stages"]):
        x, y = 28+i*207, 166
        body += rect(x, y, 183, 78, "v-wash" if stage["files"] else "panel", 8)
        body += text(x+14, y+22, f"0{i+1} / {stage['label'].upper()}", "violet bold", 10)
        body += text(x+14, y+54, str(len(stage["files"])), "display", 25)
        body += text(x+45, y+54, "source modules", "muted", 10)
        if i < 3:
            body += wipe(f"stage-{i}", x+184, y+30, 22, 20,
                         f'<path d="M{x+188} {y+39}h13l-4 -4m4 4l-4 4" class="connector"/>', delay=.15*i)
    body += text(28, 264, "Repository structure at the shown commit · file presence does not certify execution", "muted", 9)
    body += text(28, 295, "MODEL WORKBENCH", "violet bold", 10)
    for i, model in enumerate(inv["models"]):
        y = 321+i*26
        body += text(28, y, "●" if model["present"] else "○", "violet" if model["present"] else "muted", 10)
        body += text(49, y, model["label"], "", 12)
        body += text(446, y, "source present" if model["present"] else "not found", "muted tiny", extra='text-anchor="end"')
    body += text(28, 404, f"{len(inv['datasets'])} season data files  ·  {len(inv['tests'])} test files", "bold", 11)
    body += text(28, 425, f"{len(inv['evaluation'])} evaluation modules · counts from source", "muted", 10)
    body += rect(486, 281, 346, 153, "panel", 10)
    body += activity(project, 505, 304, 308, 100)
    body += text(505, 423, "Default branch · all authors · Jakarta dates", "muted", 8.5)
    body += '<path d="M28 450H832" class="line"/>'
    body += text(28, 473, f"Dashboard: {inv['dashboard']}  ·  Weekly forecast job: {inv['automation']}", "amber", 10)
    body += text(28, 492, shorten("Latest workflow observation: " + workflow_label(project), 115), "muted", 9)
    body += footer(project, data, 514) + '</g>'
    desc = (f"EPL Season Forecast. Source inventory at {project['commit']['sha']}. "
            + "; ".join(f"{s['label']}: {len(s['files'])} modules" for s in inv["stages"])
            + f". {len(inv['datasets'])} season parquet files; {len(inv['tests'])} test files, not tests passed. "
            + f"Dashboard: {inv['dashboard']}; weekly forecast job: {inv['automation']}. "
            + "This is a code and build-activity visualization, not published match odds or model accuracy. "
            + f"Daily commits, default branch, all authors: {[d['count'] for d in project['activity_days']]}. "
            + f"Fetched {data['fetched_at']}.")
    return svg(860, 530, "EPL Season Forecast — source and activity explorer", desc, body, styles=STYLES)


def outputs(data):
    return {"finance-spotlight.svg": finance(data), "epl-spotlight.svg": epl(data)}


if __name__ == "__main__":
    run(lambda: [save(name, content) for name, content in outputs(read_json(DATA / "highlights.json")).items()])
