"""The user's latest public push events across repositories and branches."""
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from common import API, DATA, USERNAME, GitHub, read_json, run, today, write_json
from fetch_last_event import latest_push


def collect_pushes(events, get_json, excluded):
    excluded = {name.casefold() for name in excluded} | {USERNAME.casefold(), f"{USERNAME}/{USERNAME}".casefold()}
    unique = {}
    for event in events:
        if event.get("type") != "PushEvent" or not event.get("public", True):
            continue
        if event.get("actor", {}).get("login", USERNAME).casefold() != USERNAME.casefold():
            continue
        name = event["repo"]["name"]
        if name.casefold() in excluded or name.rsplit("/", 1)[-1].casefold() in excluded:
            continue
        unique[str(event["id"])] = event
    selected = sorted(unique.values(), key=lambda event: (event["created_at"], str(event["id"])), reverse=True)[:10]
    pushes = []
    for event in selected:
        available = True
        try:
            commit = latest_push([event], get_json)
        except requests.HTTPError as exc:
            # A force-pushed/deleted commit can disappear while its public event remains.
            # Retain the observed push but never replace its message with a newer commit.
            if exc.response is None or exc.response.status_code not in (404, 410, 422):
                raise
            repo, sha = event["repo"]["name"], event["payload"]["head"]
            commit = {"repo": repo, "sha": sha, "message": "Exact commit message unavailable", "created_at": event["created_at"],
                      "url": f"https://github.com/{quote(repo, safe='/')}/commit/{quote(sha, safe='')}"}
            available = False
        pushes.append({**commit, "event_id": str(event["id"]), "branch": event["payload"].get("ref", "").removeprefix("refs/heads/"),
                       "message_available": available})
    return pushes


def main():
    client = GitHub()
    source = f"{API}/users/{USERNAME}/events/public"
    events = [event for page in client.pages(source, max_pages=3) for event in page]
    pushes = collect_pushes(events, client.json, read_json(DATA / "profile-config.json")["excluded_repositories"])
    write_json(DATA / "commit-stream.json", {"username": USERNAME, "source": source, "as_of": today().isoformat(),
               "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
               "scope": "Up to 10 latest available public PushEvents by this user; one exact head commit per push, all branches; profile and configured exclusions omitted",
               "pushes": pushes})
    print(f"Fetched {len(pushes)} public pushes across {len({item['repo'] for item in pushes})} repositories")


if __name__ == "__main__":
    run(main)
