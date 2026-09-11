"""Public text, activity and project changes flow through to the README."""
import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
NS = {"s": "http://www.w3.org/2000/svg"}
BUILD = {"name": "new-project", "full_name": "filan214/new-project", "title": 'Project <script> & "data"',
         "description": "Real repository description", "url": "https://github.com/filan214/new-project",
         "homepage": "https://example.com/?x=1&y=2", "language": "Python", "default_branch": "main",
         "pushed_at": "2026-09-11T00:00:00Z", "stars": 2, "forks": 0, "topics": [],
         "commit": {"sha": "abcdef1234", "repo": "filan214/new-project", "message": "fix: correct values",
                    "created_at": "2026-09-11T00:00:00Z", "url": "https://github.com/filan214/new-project/commit/abcdef1234", "branch": "main"}}
SNAPSHOT = {"username": "filan214", "as_of": "2026-09-12", "fetched_at": "2026-09-12T00:01:00Z",
            "profile": {"name": "Filan", "login": "filan214", "bio": None, "location": None, "public_repos": 9, "followers": 3, "following": 2},
            "eligible_repo_count": 7, "projects": [BUILD],
            "activity_days": [{"date": "2026-09-11", "count": 3}, {"date": "2026-09-12", "count": 0}]}
LANGUAGES = {"as_of": "2026-09-12", "repo_count": 7, "total_bytes": 400, "languages": [{"name": "Python", "bytes": 400, "percent": 100}],
             "repos": {"filan214/new-project": {"languages": {"Python": 300, "HTML": 100}}}}


class LivePanelTests(unittest.TestCase):
    def spotlight(self):
        self.assertTrue(importlib.util.find_spec("render_build_spotlight"), "Spotlight renderer is missing")
        return importlib.import_module("render_build_spotlight")

    def test_spotlight_activity_is_measured_and_upstream_text_cannot_be_markup(self):
        root = ET.fromstring(self.spotlight().render(SNAPSHOT, LANGUAGES))
        self.assertIsNone(root.find(".//s:script", NS))
        desc = root.find("s:desc", NS).text
        self.assertIn('Project <script> & "data"', desc)
        self.assertIn("3 commits", desc)
        self.assertIn("default branch", desc)
        self.assertIn("2026-09-12T00:01:00Z", desc)
        self.assertEqual(len(root.findall('.//s:rect[@class="activity-bar accent"]', NS)), 1)

    def test_empty_spotlight_has_no_invented_project_or_progress(self):
        root = ET.fromstring(self.spotlight().render({**SNAPSHOT, "projects": [], "activity_days": []}, LANGUAGES))
        self.assertIn("No eligible public projects", root.find("s:desc", NS).text)

    def test_readme_project_links_update_and_details_use_safe_html(self):
        self.assertTrue(importlib.util.find_spec("render_readme"), "Dynamic README renderer is missing")
        render = importlib.import_module("render_readme").render
        from bs4 import BeautifulSoup
        page = BeautifulSoup(render(SNAPSHOT), "html.parser")
        self.assertIsNone(page.find("script"))
        self.assertTrue(page.find("details"))
        self.assertTrue(page.find("a", href="https://github.com/filan214/new-project"))
        self.assertTrue(page.find("a", href="https://example.com/?x=1&y=2"))
        self.assertTrue(all(img.get("alt") for img in page.find_all("img")))
        changed = {**BUILD, "name": "next-build", "url": "https://github.com/filan214/next-build", "homepage": "javascript:alert(1)"}
        page = BeautifulSoup(render({**SNAPSHOT, "projects": [changed]}), "html.parser")
        self.assertEqual(page.find("img", src="./recent-build.svg").parent["href"], "https://github.com/filan214/next-build")
        self.assertFalse(any(a["href"].startswith("javascript:") for a in page.find_all("a", href=True)))

    def test_biography_and_tagline_follow_fetched_profile_and_projects(self):
        from make_info_card import render as info
        from make_tagline import render as tagline
        for render in (info, tagline):
            with self.subTest(renderer=render.__module__):
                # The old hard-coded renderers cannot consume a live snapshot.
                import inspect
                self.assertGreaterEqual(len(inspect.signature(render).parameters), 2, "Renderer still uses fixed biography")
                root = ET.fromstring(render(SNAPSHOT, LANGUAGES))
                content = " ".join(root.itertext())
                self.assertIn("new-project", content)
                self.assertNotIn("weekend driver", content)

    def test_spotlight_static_and_reduced_motion_keep_content_and_styles(self):
        with patch.dict(os.environ, {"STATIC": "1"}):
            root = ET.fromstring(self.spotlight().render(SNAPSHOT, LANGUAGES))
        self.assertIsNone(root.find(".//s:animate", NS))
        style = root.find("s:style", NS).text
        self.assertIn("prefers-color-scheme: dark", style)
        self.assertNotIn("@keyframes", style)
        self.assertIn("activity-bar", style)


if __name__ == "__main__":
    unittest.main()
