"""Check rendered contracts, safe upstream text, and calendar boundaries."""
import importlib.util
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from make_info_card import render as info
from render_build_spotlight import render as spotlight
from make_tagline import render as tagline
from render_commit_log import render as commit
from render_heatmap_svg import calendar_days, render as heatmap
from render_languages_svg import render as languages
from render_status_bar import render as status
from test_live_panels import SNAPSHOT, LANGUAGES as LIVE_LANGUAGES

NS = {"s": "http://www.w3.org/2000/svg"}
CALENDAR = {"as_of": "2026-09-12", "days": [{"date": "2026-09-11", "count": 3, "level": 2}]}
LANGUAGES = {"as_of": "2026-09-12", "repo_count": 2, "total_bytes": 400, "languages": [{"name": "Python", "bytes": 300, "percent": 75}, {"name": "HTML", "bytes": 100, "percent": 25}]}
STATUS = {"objectives_done": 5, "objectives_total": 5, "defense_status": "pending"}


class SvgTests(unittest.TestCase):
    def renders(self):
        return [info(SNAPSHOT, LIVE_LANGUAGES), spotlight(SNAPSHOT, LIVE_LANGUAGES), tagline(SNAPSHOT, LIVE_LANGUAGES), commit({"event": None}), heatmap(CALENDAR), languages(LANGUAGES), status(STATUS)]

    def test_all_panels_have_accessible_self_contained_theme_markup(self):
        for source in self.renders():
            root = ET.fromstring(source)
            with self.subTest(title=root.find("s:title", NS).text):
                self.assertTrue(root.find("s:title", NS).text)
                self.assertTrue(root.find("s:desc", NS).text)
                self.assertEqual(root.get("aria-labelledby"), "title desc")
                self.assertIn("prefers-color-scheme: dark", root.find("s:style", NS).text)
                self.assertIsNone(root.find(".//s:script", NS))
                self.assertIsNone(root.find(".//s:image", NS))
                ids = [element.get("id") for element in root.iter() if element.get("id")]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertIn(root.get("width"), ("490", "860"))

    def test_static_outputs_remove_smil_and_disable_css_motion(self):
        with patch.dict(os.environ, {"STATIC": "1"}):
            for source in self.renders():
                root = ET.fromstring(source)
                self.assertIsNone(root.find(".//s:animate", NS))
                self.assertIsNone(root.find(".//s:animateTransform", NS))
                self.assertNotIn("@keyframes", root.find("s:style", NS).text)

    def test_commit_message_cannot_inject_svg_markup(self):
        hostile = 'fix <script>alert("x")</script> & totals\x00'
        source = commit({"event": {"repo": "filan214/demo", "sha": "abc12345", "message": hostile, "created_at": "2026-09-12"}})
        root = ET.fromstring(source)
        self.assertIsNone(root.find(".//s:script", NS))
        self.assertIn('fix <script>alert("x")</script> & totals', root.find("s:desc", NS).text)

    def test_calendar_has_53_sunday_first_weeks_across_leap_year(self):
        days = calendar_days(date(2024, 3, 1))
        self.assertEqual(len(days), 371)
        self.assertEqual(days[0], date(2023, 2, 26))
        self.assertEqual(days[-1], date(2024, 3, 2))
        self.assertIn(date(2024, 2, 29), days)

    def test_missing_days_are_not_drawn_as_zero_contributions(self):
        root = ET.fromstring(heatmap(CALENDAR))
        cells = root.findall('.//s:g[@class="drop"]/s:rect', NS)
        self.assertEqual(len(cells), 371)
        self.assertEqual(sum(cell.get("class") == "unknown" for cell in cells), 370)

    def test_thesis_bar_uses_objectives_even_when_defense_is_pending(self):
        root = ET.fromstring(status({"objectives_done": 2, "objectives_total": 5, "defense_status": "pending"}))
        fill = root.find('.//s:g[@class="wipe"]/s:rect', NS)
        self.assertEqual(float(fill.get("width")), 92)
        self.assertIn("2/5 objectives finalized, defense: pending", root.find("s:desc", NS).text)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Portrait dependency is intentionally absent in daily CI")
    def test_portrait_has_53_independent_wipes_with_100_characters(self):
        from make_ascii_svg import render
        from PIL import Image
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            photo = Path(folder) / "portrait.png"
            Image.new("L", (60, 80), 100).save(photo)
            root = ET.fromstring(render(photo))
        rows = root.findall('.//s:text[@class="portrait"]', NS)
        self.assertEqual(len(rows), 53)
        self.assertTrue(all(len(row.text) == 100 for row in rows))
        self.assertEqual(len(root.findall('.//s:animate', NS)), 53)


if __name__ == "__main__":
    unittest.main()
