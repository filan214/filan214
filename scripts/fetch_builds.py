"""Fetch real public projects; API failures never become invented activity."""
import base64
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import quote, urlencode, urlsplit

import requests

from common import API, DATA, JAKARTA, USERNAME, GitHub, read_json, run, today, write_json


def safe_url(value):
    value = value or ""
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        return ""
    try:
        parts = urlsplit(value)
        return value if parts.scheme in ("https", "http") and parts.hostname and not parts.username and not parts.password else ""
    except ValueError:
        return ""


def select_repositories(repos, excluded):
    excluded = {name.casefold() for name in excluded} | {USERNAME.casefold()}
    selected = [repo for repo in repos
                if repo["owner"]["login"].casefold() == USERNAME.casefold()
                and repo["name"].casefold() not in excluded
                and repo["full_name"].casefold() not in excluded
                and not any(repo.get(flag) for flag in ("fork", "archived", "private", "disabled"))
                and repo.get("pushed_at")]
    return sorted(selected, key=lambda repo: (repo["pushed_at"], repo["name"]), reverse=True)


def activity_days(commits, as_of, window_days=28):
    start = as_of - timedelta(days=window_days-1)
    counts, seen = Counter(), set()
    for commit in commits:
        if commit["sha"] in seen:
            continue
        seen.add(commit["sha"])
        day = datetime.fromisoformat(commit["commit"]["committer"]["date"].replace("Z", "+00:00")).astimezone(JAKARTA).date()
        if start <= day <= as_of:
            counts[day] += 1
    return [{"date": (start + timedelta(days=i)).isoformat(), "count": counts[start + timedelta(days=i)]} for i in range(window_days)]


def readme_title(markdown):
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    if not match:
        return ""
    title = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", match[1])
    return " ".join(unescape(re.sub(r"<[^>]*>", "", title)).replace("**", "").replace("`", "").strip(" #").split())[:160]


def repository_title(client, name, ref):
    try:
        value = client.json(f"{API}/repos/{quote(name, safe='/')}/readme?{urlencode({'ref': ref})}")
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return ""
        raise
    if value.get("encoding") != "base64":
        return ""
    return readme_title(base64.b64decode(value["content"]).decode("utf-8", errors="replace"))


def latest_commit(client, name, branch):
    try:
        values = client.json(f"{API}/repos/{quote(name, safe='/')}/commits?{urlencode({'sha': branch, 'per_page': 1})}")
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 409:
            return None  # GitHub's empty repository response; not a transient failure.
        raise
    if not values:
        return None
    commit = values[0]
    return {"repo": name, "sha": commit["sha"], "message": commit["commit"]["message"].splitlines()[0] if commit["commit"]["message"] else "(empty commit message)",
            "created_at": commit["commit"]["committer"]["date"], "url": safe_url(commit["html_url"]),
            "author": commit["commit"]["author"]["name"], "branch": branch}


def repository_activity(client, project, as_of, window_days=28):
    start = datetime.combine(as_of - timedelta(days=window_days-1), datetime.min.time(), JAKARTA)
    end = datetime.combine(as_of + timedelta(days=1), datetime.min.time(), JAKARTA)
    params = urlencode({"sha": project["commit"]["sha"], "since": start.isoformat(), "until": end.isoformat()})
    history = [commit for page in client.pages(f"{API}/repos/{quote(project['full_name'], safe='/')}/commits?{params}") for commit in page]
    return activity_days(history, as_of, window_days)


def main():
    client, as_of = GitHub(), today()
    config = read_json(DATA / "profile-config.json")
    profile = client.json(f"{API}/users/{USERNAME}")
    source = f"{API}/users/{USERNAME}/repos?type=owner&sort=pushed&direction=desc"
    repos = [repo for page in client.pages(source) for repo in page]
    eligible = select_repositories(repos, config["excluded_repositories"])
    projects = []
    for repo in eligible:
        if len(projects) == 4:
            break
        name, branch = repo["full_name"], repo["default_branch"]
        commit = latest_commit(client, name, branch)
        # Empty repos can have pushed_at. Skip them rather than claim a build exists.
        if commit is None:
            continue
        projects.append({"name": repo["name"], "full_name": name, "url": safe_url(repo["html_url"]),
                         "title": repository_title(client, name, commit["sha"]) or repo["name"],
                         "description": repo.get("description") or "", "homepage": safe_url(repo.get("homepage")),
                         "language": repo.get("language"), "topics": repo.get("topics", []),
                         "pushed_at": repo["pushed_at"], "default_branch": branch,
                         "stars": repo["stargazers_count"], "forks": repo["forks_count"], "commit": commit})
    for project in projects:
        project["activity_days"] = repository_activity(client, project, as_of)
    days = projects[0]["activity_days"] if projects else []
    snapshot = {"username": USERNAME, "as_of": as_of.isoformat(),
                "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "source": source, "selection": "Most recently pushed public owned projects; configured exclusions, forks and archives omitted",
                "profile": {key: profile.get(key) for key in ("login", "name", "bio", "location", "public_repos", "followers", "following", "created_at")},
                "eligible_repo_count": len(eligible), "projects": projects, "activity_days": days}
    write_json(DATA / "builds.json", snapshot)
    print(f"Fetched {len(projects)} recent builds; featured: {projects[0]['name'] if projects else 'none'}")


if __name__ == "__main__":
    run(main)
