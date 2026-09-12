"""Fetch two curated public projects, anchored to exact default-branch commits."""
import re
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

import requests

from common import API, DATA, USERNAME, GitHub, read_json, run, today, write_json
from fetch_builds import latest_commit, repository_activity, safe_url

FINANCE_APP = "https://ai-finance-tracker-delta-drab.vercel.app/"
PROJECTS = {"finance": "AIFinanceTracker", "epl": "epl-season-forecast"}
SCHEMA_VERSION = 1


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
    root = "pipeline/src/eplforecast/"
    stages = [{"label": label, "path": root + folder, "files": [p for p in files
               if p.startswith(root + folder + "/") and p.endswith(".py") and not p.endswith("/__init__.py")]}
              for label, folder in [("Ingest", "ingest"), ("Features", "features"), ("Models", "models"), ("Simulate", "simulate")]]
    models = [{"label": label, "path": root + path, "present": root + path in files} for label, path in [
        ("Bayesian goals", "models/bayes_goals.py"), ("XGBoost outcomes", "models/xgb_outcome.py"),
        ("Probability blend", "models/blend.py")]]
    return {"stages": stages, "models": models,
            "datasets": [p for p in files if re.fullmatch(r"pipeline/data/processed/fd_\d{4}\.parquet", p)],
            "tests": [p for p in files if p.startswith("pipeline/tests/test_") and p.endswith(".py")],
            "evaluation": [p for p in files if p.startswith(root + "evaluate/") and p.endswith(".py") and not p.endswith("/__init__.py")],
            "dashboard": source_state(sources.get("web/app/page.tsx")),
            "automation": source_state(sources.get(".github/workflows/weekly_forecast.yml"))}


def source_state(content):
    if content is None:
        return "not found"
    if re.search(r"placeholder|not yet implemented", content, re.IGNORECASE):
        return "scaffold"
    return "source present"  # Source alone cannot prove a deployment or a working model.


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
            paths = ["src/lib/ai/tools.ts"] if kind == "finance" else ["web/app/page.tsx", ".github/workflows/weekly_forecast.yml"]
            sources = {path: source_text(client, full_name, commit["sha"], path) for path in paths}
            project["inventory"] = inventory(tree, kind, sources)
        project["activity_days"] = repository_activity(client, project, as_of, window_days=90)
        project["languages"] = client.json(f"{API}/repos/{full_name}/languages")
        project["workflow"] = latest_run(client, full_name, project["default_branch"], commit["sha"])
        projects[kind] = project
    write_json(cached_path, {"schema_version": SCHEMA_VERSION, "fetched_at": fetched_at, "as_of": as_of.isoformat(),
                            "projects": projects, "app": check_app(client, fetched_at)})
    print("Fetched finance and EPL source inventories, activity, languages, and workflow observations")


if __name__ == "__main__":
    run(main)
