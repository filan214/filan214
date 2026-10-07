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
.xsell .trace{stroke:var(--violet)} .xsell .area{fill:var(--violet)}
.area{fill:var(--accent);opacity:.08} .guide{fill:none;stroke:var(--line);stroke-dasharray:3 5}
.connector{fill:none;stroke:var(--line);stroke-width:1.5}
.sans{font-family:Arial,Helvetica,sans-serif}
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
    body = chrome(860, 462, "showcase --project AIFinanceTracker", "02 / PRODUCT SPOTLIGHT")
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


def crosssell(data):
    project = data["projects"]["crosssell"]
    inv = project["inventory"]
    results = inv["results"]
    body = chrome(860, 530, "showcase --project dealership-crosssell-propensity", "01 / DATA SCIENCE")
    body += '<g class="xsell">'
    body += text(28, 75, "SQL × MACHINE LEARNING × BI", "violet bold", 10)
    body += text(28, 112, "Dealership Cross-Sell Propensity", "display", 30)
    body += text(28, 138, "Too many customers, too few calls. Who goes first?", "muted", 12)
    body += rect(675, 67, 157, 29, "v-wash", 14)
    body += text(753, 86, "PROPENSITY MODEL", "violet bold", 9, extra='text-anchor="middle"')
    # Stage counts come from the source tree at the shown commit, not from a running pipeline.
    stages = [(stage["label"], str(len(stage["files"])), unit, bool(stage["files"]))
              for stage, unit in zip(inv["stages"], ("query files", "notebooks", "scored exports"))]
    stages.append(("Tableau", "↗" if inv["dashboard_url"] else "—", "public dashboard" if inv["dashboard_url"] else "not linked", bool(inv["dashboard_url"])))
    for i, (label, value, unit, present) in enumerate(stages):
        x, y = 28+i*207, 166
        body += rect(x, y, 183, 78, "v-wash" if present else "panel", 8)
        body += text(x+14, y+22, f"0{i+1} / {label.upper()}", "violet bold", 10)
        body += text(x+14, y+54, value, "display", 25)
        body += text(x+45, y+54, unit, "muted", 10)
        if i < 3:
            body += wipe(f"stage-{i}", x+184, y+30, 22, 20,
                         f'<path d="M{x+188} {y+39}h13l-4 -4m4 4l-4 4" class="connector"/>', delay=.15*i)
    body += text(28, 264, "Repository structure at the shown commit · file presence does not certify execution", "muted", 9)
    body += text(28, 295, "REPORTED RESULTS", "violet bold", 10)
    share = results["capture_share"] or "—"
    tiles = [("ROC-AUC", results["auc"]), ("TOP-DECILE LIFT", results["top_decile_lift"]),
             (f"REACHED · TOP {share} CALLED", results["captured"]), (f"LIFT · TOP {share} CALLED", results["capture_lift"])]
    for i, (label, value) in enumerate(tiles):
        x, y = 28 + (i % 2)*225, 306+(i//2)*58
        body += rect(x, y, 209, 50, "panel", 6)
        body += text(x+12, y+18, label, "muted tiny")
        body += text(x+12, y+41, shorten(value or "—", 12), "display violet", 20)
    held_out = f"{results['test_customers']} held-out customers" if results["test_customers"] else "held-out test set"
    body += text(28, 434, f"Quoted from the project README at this commit · {held_out}", "muted", 9)
    body += rect(486, 281, 346, 153, "panel", 10)
    body += activity(project, 505, 304, 308, 100)
    body += text(505, 423, "Default branch · all authors · Jakarta dates", "muted", 8.5)
    body += '<path d="M28 450H832" class="line"/>'
    done = [item for item in inv["status"] if item["done"]]
    status = (f"Project checklist: {len(done)}/{len(inv['status'])} done · " + " · ".join(item["label"] for item in done)
              if inv["status"] else "Project checklist: not found in README")
    body += text(28, 473, shorten(status, 112), "amber", 10)
    body += text(28, 492, shorten("Latest workflow observation: " + workflow_label(project), 115), "muted", 9)
    body += footer(project, data, 514) + '</g>'
    reported = "; ".join(f"{label.title()}: {value}" for label, value in tiles if value)
    desc = (f"Dealership Cross-Sell Propensity. Source inventory at {project['commit']['sha']}. "
            + "; ".join(f"{s['label']}: {len(s['files'])} files" for s in inv["stages"])
            + (". Tableau Public dashboard linked. " if inv["dashboard_url"] else ". No Tableau dashboard link found. ")
            + (f"Results quoted from the project README, not recomputed: {reported}. " if reported else "No results table found in the project README. ")
            + f"{status}. "
            + f"Daily commits, default branch, all authors: {[d['count'] for d in project['activity_days']]}. "
            + f"Fetched {data['fetched_at']}.")
    return svg(860, 530, "Dealership Cross-Sell Propensity — model results and source explorer", desc, body, styles=STYLES)


def story(data):
    # Plain-language case study: every number is quoted from the project README at the shown commit.
    project = data["projects"]["crosssell"]
    r = project["inventory"]["results"]
    share, lift = r["capture_share"] or "top slice", r["capture_lift"] or "—"
    beats = [("PROBLEM", r["response_rate"], ["of customers say yes.", "Too many to call them all;", "random calls mostly miss."]),
             ("INSIGHT", r["segment_rate"], ["respond when the car was", "damaged and uninsured.", "SQL showed where to look."]),
             ("MODEL", r["test_customers"], ["unseen customers scored", "on how likely each is to", "buy, then ranked."]),
             ("IMPACT", r["captured"], ["of interested customers", f"reached via the top {share},", f"{lift} better than random."])]
    body = chrome(860, 340, "story --project dealership-crosssell-propensity", "01 / DATA SCIENCE")
    body += '<g class="xsell">'
    body += text(28, 82, "Who should sales call first?", "display", 28)
    body += text(28, 106, "A dealership cross-sell case, from question to call list.", "muted", 12)
    for i, (label, value, lines) in enumerate(beats):
        x = 28+i*207
        body += f'<g class="enter" style="animation-delay:{.15+i*.18:.2f}s">'
        body += rect(x, 126, 183, 156, "v-wash" if i == 3 else "panel", 10)
        body += text(x+16, 150, f"0{i+1} · {label}", "violet bold", 10)
        body += text(x+16, 192, shorten(value or "—", 9), "display violet", 30)
        for j, line in enumerate(lines):
            body += text(x+16, 218+j*17, line, "sans", 11)
        body += '</g>'
        if i < 3:
            body += f'<path d="M{x+188} {204}h13l-4 -4m4 4l-4 4" class="connector"/>'
    body += text(28, 310, "Delivered as a Tableau call list with a “top % to call” slider for the sales team.", "sans", 12)
    body += text(832, 328, "Figures from the project README · " + project["commit"]["sha"][:7], "muted tiny", extra='text-anchor="end"')
    body += '</g>'
    desc = (f"Problem: only {r['response_rate']} of customers respond, and sales cannot call everyone. "
            f"Insight: SQL analysis found {r['segment']} customers respond at {r['segment_rate']}. "
            f"Model: {r['test_customers']} unseen customers were scored and ranked by likelihood to buy. "
            f"Impact: calling the top {share} reaches {r['captured']} of interested customers, {lift} better than random. "
            "Delivered as a Tableau call list. Figures quoted from the project README at commit " + project["commit"]["sha"] + ".")
    return svg(860, 340, "Who should sales call first? — Dealership cross-sell story", desc, body, styles=STYLES)


def outputs(data):
    return {"finance-spotlight.svg": finance(data), "crosssell-spotlight.svg": crosssell(data), "crosssell-story.svg": story(data)}


if __name__ == "__main__":
    run(lambda: [save(name, content) for name, content in outputs(read_json(DATA / "highlights.json")).items()])
