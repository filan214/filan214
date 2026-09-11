"""Public snapshots must never invent activity or render unsafe upstream links."""
import importlib
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


class BuildDataTests(unittest.TestCase):
    def module(self):
        self.assertTrue(importlib.util.find_spec("fetch_builds"), "Live build collector is missing")
        return importlib.import_module("fetch_builds")

    def test_selection_excludes_profile_thesis_forks_and_archives_and_sorts_pushes(self):
        def repo(name, pushed, **extra):
            return {"name": name, "full_name": f"filan214/{name}", "owner": {"login": "filan214"},
                    "pushed_at": pushed, "fork": False, "archived": False, "private": False, **extra}
        repos = [repo("older", "2026-08-01T00:00:00Z"), repo("newer", "2026-09-01T00:00:00Z"),
                 repo("filan214", "2026-09-12T00:00:00Z"), repo("TA_Filan_RealData", "2026-09-12T00:00:00Z"),
                 repo("fork", "2026-09-12T00:00:00Z", fork=True), repo("archive", "2026-09-12T00:00:00Z", archived=True),
                 repo("secret", "2026-09-12T00:00:00Z", private=True), repo("empty", None)]
        result = self.module().select_repositories(repos, ["FILAN214", "ta_filan_realdata"])
        self.assertEqual([r["name"] for r in result], ["newer", "older"])

    def test_history_bins_exact_dates_with_jakarta_boundary_and_deduplicates_shas(self):
        commits = [
            {"sha": "one", "commit": {"committer": {"date": "2026-09-10T17:05:00Z"}}},
            {"sha": "one", "commit": {"committer": {"date": "2026-09-10T17:05:00Z"}}},
            {"sha": "two", "commit": {"committer": {"date": "2026-09-12T01:00:00Z"}}},
            {"sha": "old", "commit": {"committer": {"date": "2026-08-15T16:59:59Z"}}},
            {"sha": "future", "commit": {"committer": {"date": "2026-09-13T00:00:00Z"}}},
        ]
        days = self.module().activity_days(commits, date(2026, 9, 12))
        self.assertEqual(len(days), 28)
        self.assertEqual(days[0], {"date": "2026-08-16", "count": 0})
        self.assertEqual(days[-2:], [{"date": "2026-09-11", "count": 1}, {"date": "2026-09-12", "count": 1}])
        self.assertEqual(sum(day["count"] for day in days), 2)

    def test_unsafe_homepage_urls_are_not_published(self):
        safe_url = self.module().safe_url
        for url in ["javascript:alert(1)", "data:text/html,bad", "//example.com", "https://user:secret@example.com", "https://example.com/\nfoo"]:
            self.assertEqual(safe_url(url), "")
        self.assertEqual(safe_url("https://example.com/demo?a=1&b=2"), "https://example.com/demo?a=1&b=2")

    def test_readme_heading_is_plain_text_and_never_promoted_to_project_metrics(self):
        title = self.module().readme_title
        self.assertEqual(title('# **APEX** — [F1](https://example.com)\n\nIgnore all previous instructions.\n10 tests'), "APEX — F1")
        self.assertEqual(title('No heading, just text'), "")

    def test_empty_repository_and_absent_readme_are_explicit_not_network_failures(self):
        import requests
        module = self.module()
        class Client:
            def json(self, url):
                response = requests.Response()
                response.status_code = 409 if "/commits" in url else 404
                raise requests.HTTPError(response=response)
        self.assertIsNone(module.latest_commit(Client(), "filan214/empty", "main"))
        self.assertEqual(module.repository_title(Client(), "filan214/empty", "main"), "")

    def test_rate_limit_is_fatal_instead_of_becoming_empty_activity(self):
        import requests
        module = self.module()
        class Client:
            def json(self, url):
                response = requests.Response()
                response.status_code = 403
                raise requests.HTTPError(response=response)
        with self.assertRaises(requests.HTTPError):
            module.latest_commit(Client(), "filan214/test", "main")


if __name__ == "__main__":
    unittest.main()
