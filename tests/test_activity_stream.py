"""Real repo history, ordered public pushes, and accessible activity visuals."""
import importlib
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
NS = {"s": "http://www.w3.org/2000/svg"}


def push(event_id, repo="filan214/POS", when="2026-09-11T01:00:00Z", sha="abcdef1234"):
    return {"id": event_id, "type": "PushEvent", "public": True, "actor": {"login": "filan214"},
            "repo": {"name": repo}, "created_at": when,
            "payload": {"head": sha, "ref": "refs/heads/feature/chart", "commits": [{"sha": sha, "message": "feat: real update"}]}}


class HistoryTests(unittest.TestCase):
    def test_each_repository_history_is_pinned_and_all_pages_counted(self):
        import fetch_builds
        self.assertTrue(hasattr(fetch_builds, "repository_activity"), "Per-repository activity fetch is missing")
        class Client:
            def pages(inner, url):
                query = parse_qs(urlsplit(url).query)
                self.assertEqual(query["sha"], ["exact-tip"])
                self.assertEqual(query["since"], ["2026-08-16T00:00:00+07:00"])
                self.assertEqual(query["until"], ["2026-09-13T00:00:00+07:00"])
                yield [{"sha": "one", "commit": {"committer": {"date": "2026-09-11T01:00:00Z"}}}]
                yield [{"sha": "two", "commit": {"committer": {"date": "2026-09-11T02:00:00Z"}}}]
        project = {"full_name": "filan214/POS", "commit": {"sha": "exact-tip"}}
        days = fetch_builds.repository_activity(Client(), project, date(2026, 9, 12))
        self.assertEqual(days[-2], {"date": "2026-09-11", "count": 2})
        self.assertEqual(sum(day["count"] for day in days), 2)


class PushStreamTests(unittest.TestCase):
    def module(self):
        self.assertTrue(importlib.util.find_spec("fetch_commit_stream"), "Push stream collector is missing")
        return importlib.import_module("fetch_commit_stream")

    def test_sort_deduplicate_filter_then_limit_without_padding(self):
        old = push("1", when="2026-09-09T01:00:00Z")
        new = push("2", "filan214/other", "2026-09-11T01:00:00Z")
        events = [old, new, new, push("3", "filan214/filan214"), push("4", "filan214/TA_Filan_RealData"),
                  {**push("5"), "public": False}, {**push("6"), "type": "WatchEvent"}]
        result = self.module().collect_pushes(events, lambda url: self.fail("Messages already supplied"), ["TA_Filan_RealData"])
        self.assertEqual([item["event_id"] for item in result], ["2", "1"])
        self.assertEqual(result[0]["branch"], "feature/chart")
        self.assertEqual(result[0]["repo"], "filan214/other")
        many = [push(str(i), when=f"2026-09-{i+1:02}T00:00:00Z") for i in range(15)]
        self.assertEqual(len(self.module().collect_pushes(many, lambda url: None, [])), 10)

    def test_message_lookup_uses_event_head_never_current_branch(self):
        event = push("1", sha="old-head")
        event["payload"].pop("commits")
        def get_json(url):
            self.assertEqual(url, "https://api.github.com/repos/filan214/POS/commits/old-head")
            return {"sha": "old-head", "commit": {"message": "fix: <log> & totals\n\nMore context"}}
        item = self.module().collect_pushes([event], get_json, [])[0]
        self.assertEqual(item["sha"], "old-head")
        self.assertEqual(item["message"], "fix: <log> & totals")
        self.assertEqual(item["created_at"], "2026-09-11T01:00:00Z")

    def test_missing_commit_is_explicit_but_rate_limit_aborts(self):
        import requests
        event = push("1")
        event["payload"].pop("commits")
        def missing(url):
            response = requests.Response(); response.status_code = 404
            raise requests.HTTPError(response=response)
        item = self.module().collect_pushes([event], missing, [])[0]
        self.assertFalse(item["message_available"])
        self.assertIn("unavailable", item["message"])
        def limited(url):
            raise RuntimeError("rate limited")
        with self.assertRaises(RuntimeError):
            self.module().collect_pushes([event], limited, [])

    def test_no_events_is_an_empty_stream(self):
        self.assertEqual(self.module().collect_pushes([], lambda url: self.fail("No lookup"), []), [])


class ActivityRenderingTests(unittest.TestCase):
    def module(self, name):
        self.assertTrue(importlib.util.find_spec(name), f"{name} is missing")
        return importlib.import_module(name)

    def test_sparkline_tracks_real_counts_and_zero_activity_stays_flat(self):
        render = self.module("render_repo_sparklines").render
        for counts in ([0, 0, 0], [0, 3, 0]):
            days = [{"date": f"2026-09-{i+1:02}", "count": count} for i, count in enumerate(counts)]
            root = ET.fromstring(render({"name": "demo", "activity_days": days, "default_branch": "main"}, "2026-09-12T00:00:00Z"))
            line = root.find('.//s:polyline[@class="spark-line"]', NS)
            ys = [float(point.split(',')[1]) for point in line.get("points").split()]
            self.assertEqual(ys[0], ys[2])
            self.assertEqual(ys[0] == ys[1], sum(counts) == 0)
            self.assertIn(f"{sum(counts)} commits", root.find("s:desc", NS).text)

    def test_stream_keeps_all_events_accessible_and_static_mode_readable(self):
        render = self.module("render_commit_stream").render
        pushes = [{"event_id": str(i), "repo": "filan214/demo", "sha": f"sha{i:04}", "message": 'fix <script> & "text"',
                   "created_at": "2026-09-11T00:00:00Z", "branch": "main", "url": "https://github.com/filan214/demo/commit/abcd", "message_available": True} for i in range(10)]
        data = {"pushes": pushes, "fetched_at": "2026-09-12T00:00:00Z"}
        root = ET.fromstring(render(data))
        self.assertIsNone(root.find('.//s:script', NS))
        self.assertIn("sha0009", root.find("s:desc", NS).text)
        self.assertIn("prefers-reduced-motion", root.find("s:style", NS).text)
        with patch.dict(os.environ, {"STATIC": "1"}):
            frozen = ET.fromstring(render(data))
        self.assertNotIn("@keyframes", frozen.find("s:style", NS).text)
        self.assertIn("sha0009", " ".join(frozen.itertext()))

    def test_sparkline_is_inside_each_project_row_and_stream_is_below_table(self):
        from render_readme import render
        from test_live_panels import SNAPSHOT, BUILD
        from bs4 import BeautifulSoup
        data = {**SNAPSHOT, "projects": [BUILD, {**BUILD, "name": "second"}]}
        # The new stream is an independent snapshot; an empty response stays empty.
        import inspect
        self.assertIn("stream", inspect.signature(render).parameters, "README cannot consume push stream")
        page = BeautifulSoup(render(data, {"pushes": [], "fetched_at": SNAPSHOT["fetched_at"]}), 'html.parser')
        sparks = page.find_all('img', src=lambda src: src and 'repo-activity-' in src)
        self.assertEqual(len(sparks), 2)
        self.assertTrue(all(img.find_parent('tr') for img in sparks))
        feed = page.find('img', src='./commit-stream.svg')
        self.assertTrue(feed and feed.get('alt'))
        self.assertIsNone(feed.find_parent('table'))
        self.assertIsNone(feed.find_parent('details'))


if __name__ == "__main__":
    unittest.main()
