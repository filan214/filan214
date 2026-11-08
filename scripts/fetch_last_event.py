"""Resolve the newest public push event to its exact head commit."""
from urllib.parse import quote

from common import API


def latest_push(events, get_json):
    pushes = [event for event in events if event.get("type") == "PushEvent"]
    if not pushes:
        return None
    event = max(pushes, key=lambda item: item["created_at"])
    repo = event["repo"]["name"]
    payload = event["payload"]
    commits = payload.get("commits", [])
    sha = payload.get("head") or (commits[-1]["sha"] if commits else None)
    if not sha:
        raise ValueError("Latest PushEvent has no head commit; existing data was preserved")
    embedded = next((commit for commit in commits if commit["sha"] == sha), None)
    if embedded and embedded.get("message"):
        message = embedded["message"]
    else:
        commit = get_json(f"{API}/repos/{quote(repo, safe='/')}/commits/{quote(sha, safe='')}")
        message = commit["commit"]["message"]
    return {"repo": repo, "sha": sha, "message": message.splitlines()[0] if message else "(empty commit message)", "created_at": event["created_at"], "url": f"https://github.com/{repo}/commit/{sha}"}
