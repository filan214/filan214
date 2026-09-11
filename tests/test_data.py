"""Regression cases for upstream formats, derived stats, and manual input."""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_contributions import parse_contributions, contribution_stats
from fetch_last_event import latest_push
from fetch_languages import aggregate_languages
from render_status_bar import validate_status
from common import GitHub


class ContributionsTests(unittest.TestCase):
    def test_request_spans_53_weeks_instead_of_year_to_date(self):
        from fetch_contributions import main
        saved = {}
        fixtures = {
            "2025": '<rect data-date="2025-09-06" data-count="99"/><rect data-date="2025-09-07" data-count="1"/><rect data-date="2025-12-31" data-count="2"/>',
            "2026": '<rect data-date="2026-01-01" data-count="3"/><rect data-date="2026-09-12" data-count="0"/>',
        }
        def get(url, **kwargs):
            return SimpleNamespace(text=fixtures[kwargs["params"]["to"][:4]])
        with patch("fetch_contributions.today", return_value=date(2026, 9, 12)), patch("fetch_contributions.GitHub", return_value=SimpleNamespace(get=get)), patch("fetch_contributions.write_json", side_effect=lambda path, value: saved.update(value)):
            main()
        self.assertEqual([day["date"] for day in saved["days"]], ["2025-09-07", "2025-12-31", "2026-01-01", "2026-09-12"])
        self.assertEqual(saved["stats"]["total"], 6)

    def test_tooltip_counts_are_not_color_levels(self):
        html = '''<td id="d2" data-date="2026-01-02" data-level="4"></td>
        <tool-tip for="d2">1,234 contributions on January 2nd.</tool-tip>
        <td id="d1" data-date="2026-01-01" data-level="0"></td>
        <tool-tip for="d1">No contributions on January 1st.</tool-tip>'''
        self.assertEqual(parse_contributions(html), [
            {"date": "2026-01-01", "count": 0, "level": 0},
            {"date": "2026-01-02", "count": 1234, "level": 4},
        ])

    def test_legacy_count_attribute(self):
        self.assertEqual(parse_contributions('<rect data-date="2026-01-01" data-count="7" data-level="2"/>')[0]["count"], 7)

    def test_changed_markup_does_not_become_zero_activity(self):
        for html in ('<html>Sign in</html>', '<td data-date="2026-01-01" data-level="2"></td>'):
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_contributions(html)

    def test_streak_uses_yesterday_when_today_is_unfinished(self):
        days = [{"date": f"2026-01-{n:02}", "count": c, "level": 1} for n, c in [(1, 4), (2, 2), (3, 0), (4, 5), (5, 6), (6, 0), (7, 99)]]
        stats = contribution_stats(days, date(2026, 1, 6))
        self.assertEqual(stats["current_streak"], 2)
        self.assertEqual(stats["longest_streak"], 2)
        self.assertEqual(stats["best_day"], {"date": "2026-01-05", "count": 6})
        self.assertEqual(stats["monthly_totals"], {"2026-01": 17})
        self.assertEqual(stats["total"], 17)

    def test_missing_dates_break_streak(self):
        stats = contribution_stats([{"date": "2026-01-01", "count": 1}, {"date": "2026-01-03", "count": 1}], date(2026, 1, 3))
        self.assertEqual(stats["longest_streak"], 1)
        self.assertEqual(stats["current_streak"], 1)

    def test_old_activity_is_not_a_current_streak(self):
        stats = contribution_stats([{"date": "2026-01-01", "count": 1}], date(2026, 1, 4))
        self.assertEqual(stats["current_streak"], 0)

    def test_missing_today_is_not_an_unfinished_zero_day(self):
        stats = contribution_stats([{"date": "2026-01-03", "count": 1}], date(2026, 1, 4))
        self.assertEqual(stats["current_streak"], 0)


class EventTests(unittest.TestCase):
    def test_head_lookup_uses_exact_event_sha(self):
        def get_json(url):
            self.assertEqual(url, "https://api.github.com/repos/filan214/POS/commits/abcdef123456")
            return {"sha": "abcdef123456", "commit": {"message": "fix: <cart> & totals\n\nDetails"}}
        event = {"id": "9", "type": "PushEvent", "repo": {"name": "filan214/POS"}, "created_at": "2026-01-05T01:00:00Z", "payload": {"head": "abcdef123456"}}
        result = latest_push([event], get_json)
        self.assertEqual(result["message"], "fix: <cart> & totals")
        self.assertEqual(result["sha"], "abcdef123456")

    def test_legacy_event_selects_head_not_first_commit(self):
        event = {"type": "PushEvent", "repo": {"name": "filan214/POS"}, "created_at": "2026-01-05T01:00:00Z", "payload": {"head": "b", "commits": [{"sha": "a", "message": "old"}, {"sha": "b", "message": "new"}]}}
        result = latest_push([event], lambda url: self.fail("No lookup needed"))
        self.assertEqual(result["message"], "new")

    def test_no_push_is_explicit_empty_state(self):
        self.assertIsNone(latest_push([{"type": "WatchEvent"}], lambda url: self.fail("No commit to fetch")))


class LanguageTests(unittest.TestCase):
    def test_byte_totals_include_all_pages_and_reuse_unchanged_cache(self):
        repos = [{"full_name": "filan214/one", "pushed_at": "a"}, {"full_name": "filan214/two", "pushed_at": "b"}]
        cached = {"filan214/one": {"pushed_at": "a", "languages": {"Python": 100, "HTML": 50}}}
        def get_json(url):
            self.assertEqual(url, "https://api.github.com/repos/filan214/two/languages")
            return {"Python": 300, "SQL": 50}
        result = aggregate_languages(repos, get_json, cached)
        self.assertEqual(result["total_bytes"], 500)
        self.assertEqual(result["languages"][0], {"name": "Python", "bytes": 400, "percent": 80.0})
        self.assertEqual(result["repo_count"], 2)

    def test_deleted_repository_is_removed_from_totals(self):
        result = aggregate_languages([], lambda url: self.fail("No repos"), {"gone": {"languages": {"Python": 5}}})
        self.assertEqual(result["total_bytes"], 0)
        self.assertEqual(result["languages"], [])

    def test_pagination_follows_next_link_without_dropping_repositories(self):
        client = GitHub()
        pages = {
            "https://api.github.com/users/filan214/repos": SimpleNamespace(json=lambda: [{"full_name": "filan214/one"}], links={"next": {"url": "https://api.github.com/users/filan214/repos?page=2&per_page=100"}}),
            "https://api.github.com/users/filan214/repos?page=2&per_page=100": SimpleNamespace(json=lambda: [{"full_name": "filan214/two"}], links={}),
        }
        with patch.object(client, "get", side_effect=lambda url, **kw: pages[url]):
            result = [repo["full_name"] for page in client.pages("https://api.github.com/users/filan214/repos") for repo in page]
        self.assertEqual(result, ["filan214/one", "filan214/two"])


class StatusTests(unittest.TestCase):
    def test_complete_objectives_do_not_imply_defense_complete(self):
        self.assertEqual(validate_status({"objectives_done": 5, "objectives_total": 5, "defense_status": "pending"}), (5, 5, "pending"))

    def test_invalid_totals_fail_before_rendering(self):
        for done, total in [(6, 5), (-1, 5), (0, 0), (True, 5), (2.5, 5)]:
            with self.subTest(done=done, total=total), self.assertRaises(ValueError):
                validate_status({"objectives_done": done, "objectives_total": total, "defense_status": "pending"})


if __name__ == "__main__":
    unittest.main()
