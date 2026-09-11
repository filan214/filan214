"""Aggregate actual language bytes across the eligible public project pool."""
from collections import Counter
from urllib.parse import quote

from common import API, DATA, USERNAME, GitHub, read_json, run, today, write_json
from fetch_builds import select_repositories


def aggregate_languages(repos, get_json, cache=None):
    cache = cache or {}
    totals = Counter()
    current_cache = {}
    for repo in repos:
        name, pushed = repo["full_name"], repo.get("pushed_at")
        old = cache.get(name, {})
        languages = old.get("languages") if pushed and old.get("pushed_at") == pushed else None
        if languages is None:
            languages = get_json(f"{API}/repos/{quote(name, safe='/')}/languages")
        if not isinstance(languages, dict) or any(type(value) is not int or value < 0 for value in languages.values()):
            raise ValueError(f"Invalid language bytes for {name}")
        totals.update(languages)
        current_cache[name] = {"pushed_at": pushed, "languages": languages}
    total = sum(totals.values())
    return {"repo_count": len(repos), "total_bytes": total,
            "languages": [{"name": name, "bytes": value, "percent": round(100 * value / total, 2)} for name, value in sorted(totals.items(), key=lambda item: (-item[1], item[0])) if value > 0],
            "repos": current_cache}


def main():
    client = GitHub()
    source = f"{API}/users/{USERNAME}/repos"
    repos = select_repositories([repo for page in client.pages(source + "?type=owner&sort=full_name") for repo in page], read_json(DATA / "profile-config.json")["excluded_repositories"])
    path = DATA / "languages.json"
    old = read_json(path) if path.exists() else {}
    # Refresh all bytes once a day: Linguist can finish after pushed_at changes.
    refresh = old.get("as_of") != today().isoformat()
    result = aggregate_languages(repos, client.json, {} if refresh else old.get("repos", {}))
    write_json(path, {"username": USERNAME, "as_of": today().isoformat(), "source": source, **result})
    print(f"Aggregated {result['total_bytes']:,} language bytes across {len(repos)} repositories")


if __name__ == "__main__":
    run(main)
