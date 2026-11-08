"""Fetch curated public projects, anchored to exact default-branch commits."""
import re
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

import requests

from common import API, DATA, USERNAME, GitHub, read_json, run, today, write_json
from fetch_builds import latest_commit, repository_activity, safe_url

FINANCE_APP = "https://ai-finance-tracker-delta-drab.vercel.app/"
PROJECTS = {"finance": "AIFinanceTracker", "crosssell": "dealership-crosssell-propensity", "valuation": "Jogja-House-Valuation"}
SCHEMA_VERSION = 2  # 2: cross-sell results include the strongest segment


def source_text(client, full_name, sha, path):
    url = f"https://raw.githubusercontent.com/{full_name}/{sha}/{quote(path, safe='/')}"
    try:
        return client.get(url).text
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def inventory(tree, kind, sources):
    if tree.get("truncated"):
        raise ValueError("GitHub returned an incomplete source tree; keeping the previous snapshot")
    files = sorted(row["path"] for row in tree["tree"] if row["type"] == "blob")
    if kind == "finance":
        tools = sources.get("src/lib/ai/tools.ts")
        if tools is not None:
            uncommented = re.sub(r"/\*.*?\*/", "", tools, flags=re.DOTALL)
            tool_names = sorted(set(re.findall(r"^\s*(\w+)\s*:\s*tool\s*\(", uncommented, re.MULTILINE)))
        else:
            tool_names = None
        routes = [p for p in files if p.startswith("src/app/(app)/") and p.endswith("/page.tsx")]
        features = [{"label": label, "path": path, "present": path in files} for label, path in [
            ("AI advisor", "src/app/api/ai/chat/route.ts"),
            ("Auto categories", "src/app/api/ai/categorize/route.ts"),
            ("Spending alerts", "src/app/api/ai/anomaly/route.ts"),
            ("Monthly reports", "src/app/api/ai/report/route.ts")]]
        locales = [p for p in files if re.fullmatch(r"(?:src/)?messages/[a-z]{2}\.json", p)]
        return {"tools": tool_names, "routes": routes, "locales": locales, "features": features}
    if kind == "crosssell":
        return crosssell_inventory(files, sources.get("README.md") or "")
    if kind == "valuation":
        return {"results": valuation_results(sources.get("README.md") or ""), "demo": "docs/app_demo.gif" in files,
                "market_map": "docs/app_market_map.png" in files, "report": "reports/metrics.md" in files}
    raise ValueError(f"Unknown curated project kind: {kind}")


def crosssell_inventory(files, readme):
    stages = [{"label": label, "path": folder, "files": [p for p in files if p.startswith(folder + "/") and p.endswith(suffix)]}
              for label, folder, suffix in [("SQL EDA", "sql", ".sql"), ("Model", "notebooks", ".ipynb"), ("Scores", "dashboard", ".csv")]]
    tableau = re.search(r"https://public\.tableau\.com/[^\s)\]>\"']+", readme)
    status = [{"label": " ".join(label.split()), "done": mark.lower() == "x"}
              for mark, label in re.findall(r"^\s*[-*] \[([ xX])\] (.+)$", section(readme, "Project status"), re.MULTILINE)]
    return {"stages": stages, "results": readme_results(readme), "status": status,
            "dashboard_url": safe_url(tableau[0]) if tableau else "",
            "screenshot": "dashboard/screenshot.png" in files, "shap": "notebooks/shap_summary.png" in files}


def section(markdown, heading):
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", markdown, re.MULTILINE | re.DOTALL)
    return match[1] if match else ""


def readme_results(readme):
    # Quoted from the project's own README at the pinned commit; never recomputed or estimated here.
    text = section(readme, "Results")
    rows = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and len(cells) == 2 and not set(cells[1]) <= set("-: "):
            rows[cells[0]] = cells[1]

    def row(pattern):
        return next(((label, value) for label, value in rows.items() if re.search(pattern, label, re.IGNORECASE)), ("", ""))

    def bold(pattern):
        return re.findall(r"\*\*(.+?)\*\*", row(pattern)[1])

    auc, decile = bold(r"ROC-AUC"), bold(r"top-decile lift")
    label, value = row(r"capture at \d+%")
    capture = re.findall(r"\*\*(.+?)\*\*", value)
    share = re.search(r"(\d+)%", label)
    rate = re.search(r"[\d.]+%", row(r"overall response rate")[1])
    size = re.search(r"test set of ([\d,]+) customers", text)
    driver = row(r"strongest driver")[1]
    segment, segment_rate = driver.split(":")[0].strip(), re.findall(r"\*\*(.+?)\*\*", driver)
    return {"auc": auc[0] if auc else None, "top_decile_lift": decile[0] if decile else None,
            "capture_share": share[1] + "%" if share else None, "captured": capture[0] if capture else None,
            "capture_lift": capture[1].removesuffix(" lift").strip() if len(capture) > 1 else None,
            "response_rate": rate[0] if rate else None, "test_customers": size[1] if size else None,
            "segment": segment if segment and segment_rate else None, "segment_rate": segment_rate[0] if segment_rate else None}


def percent_cell(text, label, index=1):
    # Takes the first percentage in one cell of the first Markdown table row whose label matches.
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and re.search(label, cells[0], re.IGNORECASE):
            found = re.search(r"[\d.]+%", cells[index]) if len(cells) > index else None
            return found[0] if found else None
    return None


def valuation_results(readme):
    # Quoted from the project's own README at the pinned commit; never recomputed or estimated here.
    results = section(readme, "Results")
    cleaning = re.search(r"^### Cleaning \(([\d,]+) → ([\d,]+) listings", readme, re.MULTILINE)
    reposts = re.search(r"^\|\s*Repost[^|]*\|\s*([\d,]+)\s*\|", readme, re.MULTILINE)
    honest = re.search(r"^\|\s*\*\*Per-kabupaten.*?honest nested check: ([\d.]+)", results, re.MULTILINE)
    drift = re.search(r"(\d+) current Rumah123 listings", section(readme, "Staleness and drift"))
    return {"raw_listings": cleaning[1] if cleaning else None, "clean_listings": cleaning[2] if cleaning else None,
            "reposts": reposts[1] if reposts else None, "baseline_mape": percent_cell(results, r"baseline"),
            "mape": percent_cell(results, r"LightGBM"), "range_coverage": honest[1] + "%" if honest else None,
            "drift_listings": drift[1] if drift else None}


def latest_run(client, full_name, branch, sha):
    query = urlencode({"branch": branch, "per_page": 1})
    values = client.json(f"{API}/repos/{full_name}/actions/runs?{query}")["workflow_runs"]
    if not values:
        return None
    item = values[0]
    return {"name": item["name"], "status": item["status"], "conclusion": item["conclusion"],
            "head_sha": item["head_sha"], "matches_tip": item["head_sha"] == sha,
            "updated_at": item["updated_at"], "url": safe_url(item["html_url"])}


def check_app(client, checked_at):
    # A public landing-page check, never a login, transaction query, or uptime claim.
    result = {"url": FINANCE_APP, "checked_at": checked_at, "http_status": None, "reachable": False}
    try:
        response = client.session.get(FINANCE_APP, timeout=(10, 20), allow_redirects=True)
        result.update(http_status=response.status_code,
                      reachable=200 <= response.status_code < 300 and "Smart Finn Track" in response.text)
    except requests.RequestException:
        pass
    return result


def main():
    client, as_of = GitHub(), today()
    cached_path = DATA / "highlights.json"
    cached = read_json(cached_path) if cached_path.exists() else {}
    previous = cached.get("projects", {}) if cached.get("schema_version") == SCHEMA_VERSION else {}
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    projects = {}
    for kind, name in PROJECTS.items():
        full_name = f"{USERNAME}/{name}"
        repo = client.json(f"{API}/repos/{full_name}")
        if repo.get("private") or repo.get("archived"):
            raise ValueError(f"Curated project {full_name} is no longer an active public repository")
        commit = latest_commit(client, full_name, repo["default_branch"])
        if commit is None:
            raise ValueError(f"Curated project {full_name} has no default-branch commit")
        project = {"name": name, "full_name": full_name, "url": safe_url(repo["html_url"]),
                   "description": repo.get("description") or "", "default_branch": repo["default_branch"],
                   "commit": commit, "stars": repo["stargazers_count"], "forks": repo["forks_count"]}
        old = previous.get(kind, {})
        if old.get("commit", {}).get("sha") == commit["sha"] and "inventory" in old:
            project["inventory"] = old["inventory"]
        else:
            tree = client.json(f"{API}/repos/{full_name}/git/trees/{commit['sha']}?recursive=1")
            paths = ["src/lib/ai/tools.ts"] if kind == "finance" else ["README.md"]
            sources = {path: source_text(client, full_name, commit["sha"], path) for path in paths}
            project["inventory"] = inventory(tree, kind, sources)
        project["activity_days"] = repository_activity(client, project, as_of, window_days=90)
        project["languages"] = client.json(f"{API}/repos/{full_name}/languages")
        project["workflow"] = latest_run(client, full_name, project["default_branch"], commit["sha"])
        projects[kind] = project
    write_json(cached_path, {"schema_version": SCHEMA_VERSION, "fetched_at": fetched_at, "as_of": as_of.isoformat(),
                            "projects": projects, "app": check_app(client, fetched_at)})
    print("Fetched curated source inventories, activity, languages, and workflow observations")


if __name__ == "__main__":
    run(main)
