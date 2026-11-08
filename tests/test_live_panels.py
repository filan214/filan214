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
            "repositories": [{"name": f"repo-{i}", "url": f"https://github.com/filan214/repo-{i}", "description": "", "language": None if i == 1 else "Python",
                              "pushed_at": f"2026-09-{12-i:02d}T00:00:00Z"} for i in range(8)]
                            + [{"name": "old-repo", "url": "https://github.com/filan214/old-repo", "description": "", "language": "HTML", "pushed_at": "2026-01-01T00:00:00Z"}],
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
        stream = {"pushes": [], "fetched_at": SNAPSHOT["fetched_at"]}
        page = BeautifulSoup(render(SNAPSHOT, stream), "html.parser")
        self.assertIsNone(page.find("script"))
        self.assertTrue(page.find("details"))
        self.assertTrue(page.find("a", href="https://github.com/filan214/new-project"))
        self.assertTrue(page.find("a", href="https://example.com/?x=1&y=2"))
        self.assertTrue(all(img.get("alt") for img in page.find_all("img")))
        self.assertIsNone(page.find("img", src="./recent-build.svg"))
        repositories = [{"name": "latest-push", "url": "https://github.com/filan214/latest-push", "description": "Fresh <b>idea</b>",
                         "language": None, "pushed_at": "2026-10-07T00:00:00Z"},
                        {"name": "older-push", "url": "https://github.com/filan214/older-push", "description": "",
                         "language": "Python", "pushed_at": "2026-09-30T00:00:00Z"},
                        {"name": "third-push", "url": "https://github.com/filan214/third-push", "description": "",
                         "language": "HTML", "pushed_at": "2026-09-29T00:00:00Z"}]
        page = BeautifulSoup(render({**SNAPSHOT, "repositories": repositories}, stream), "html.parser")
        self.assertNotIn("git portfolio", page.text)
        headings = [h.text for h in page.find_all("h3")]
        self.assertEqual(headings.index("Recent repositories"), len(headings) - 2, "Recent repositories sit just above the sources footer")
        links = [img.parent["href"] for img in page.find_all("img") if img["src"].startswith("./repo-card-")]
        self.assertEqual(links, [f"https://github.com/filan214/{name}" for name in ("latest-push", "older-push", "third-push")])
        self.assertIn("Fresh <b>idea</b>", page.find("img", src="./repo-card-1.svg")["alt"])
        self.assertTrue(page.find("a", string="See all repositories"))
        self.assertIn("No eligible public repositories.", render({**SNAPSHOT, "repositories": []}, stream))

    def test_repo_cards_follow_snapshot_and_omit_missing_fields(self):
        from render_repo_cards import outputs as cards
        repos = [{"name": "first", "description": 'Fresh <script>x</script> & idea', "language": "Python", "pushed_at": "2026-10-07T00:00:00Z"},
                 {"name": "bare", "description": "", "language": None, "pushed_at": "2026-10-06T00:00:00Z"},
                 {"name": "odd", "description": "", "language": "Brainfuck", "pushed_at": "2026-10-05T00:00:00Z"}]
        result = cards({**SNAPSHOT, "repositories": repos})
        self.assertEqual(list(result), ["repo-card-1.svg", "repo-card-2.svg", "repo-card-3.svg"])
        first, bare, odd = (ET.fromstring(result[f"repo-card-{i}.svg"]) for i in (1, 2, 3))
        self.assertEqual(first.get("width"), "420")
        self.assertIn("first", list(first.itertext()))
        self.assertIn("Public", list(first.itertext()))
        self.assertIsNone(first.find(".//s:script", NS))
        self.assertIn("#3572A5", first.find("s:style", NS).text)
        self.assertIsNone(bare.find(".//s:circle", NS), "No language means no language dot")
        self.assertIn("var(--muted)", odd.find("s:style", NS).text)
        self.assertEqual(len(cards(SNAPSHOT)), 6)

    def test_repo_overview_shows_public_total_and_measured_stats(self):
        from render_repo_overview import render as overview
        root = ET.fromstring(overview(SNAPSHOT))
        content = list(root.itertext())
        self.assertIn("9", content)
        self.assertIn("public repositories", content)
        self.assertIn("8", content, "A repository pushed months ago is not counted as recent")
        self.assertIn("Python", content)
        self.assertFalse(any(t.startswith("repo-") for t in content), "Repository names live in the README cards")
        empty = list(ET.fromstring(overview({**SNAPSHOT, "repositories": []})).itertext())
        self.assertIn("no language reported", empty)

    def test_readme_replaces_git_log_strip_with_repo_overview(self):
        from bs4 import BeautifulSoup
        render = importlib.import_module("render_readme").render
        page = BeautifulSoup(render(SNAPSHOT, {"pushes": [], "fetched_at": SNAPSHOT["fetched_at"]}), "html.parser")
        self.assertIsNone(page.find("img", src="./commit-log.svg"))
        self.assertEqual(page.find("img", src="./repo-overview.svg").parent["href"], "https://github.com/filan214?tab=repositories")
        headings = [h.text for h in page.find_all("h3")]
        self.assertIn("calendar", headings[0])
        self.assertIn("repos --overview", headings[1])
        self.assertIn("contact --reach", headings[2])

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
