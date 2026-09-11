"""Paths, atomic snapshots, and deliberately unauthenticated GitHub reads."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
USERNAME = "filan214"
API = "https://api.github.com"
JAKARTA = timezone(timedelta(hours=7))


def today():
    return datetime.now(JAKARTA).date()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


class GitHub:
    def __init__(self):
        self.session = requests.Session()
        # Ignore .netrc credentials so these public reads remain unauthenticated.
        self.session.trust_env = False
        self.session.headers.update({"User-Agent": "filan214-profile-art", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        self.session.mount("https://", HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])))

    def get(self, url, **kwargs):
        response = self.session.get(url, timeout=(10, 30), **kwargs)
        if response.status_code in (403, 429):
            raise RuntimeError(f"GitHub denied/rate-limited {url}; remaining={response.headers.get('X-RateLimit-Remaining', '?')}, reset Unix time={response.headers.get('X-RateLimit-Reset', '?')}. Existing JSON was preserved; retry after reset.")
        response.raise_for_status()
        return response

    def json(self, url):
        return self.get(url).json()

    def pages(self, url, max_pages=100):
        for page in range(max_pages):
            response = self.get(url, params={"per_page": 100} if page == 0 else None)
            values = response.json()
            if not isinstance(values, list):
                raise ValueError(f"Expected a list from {url}")
            yield values
            url = response.links.get("next", {}).get("url")
            if not url:
                return
        raise RuntimeError("GitHub pagination limit exceeded; refusing partial data")


def run(main):
    try:
        main()
    except (requests.RequestException, ValueError, KeyError, OSError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
