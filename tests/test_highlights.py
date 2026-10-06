"""Truthful source inventories, failure handling, and accessible project navigation."""
import copy
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from xml.etree import ElementTree as ET
from urllib.parse import parse_qs, urlsplit

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_highlights as fetch
from render_freshness import render as freshness
from render_contact import outputs as contact
from render_highlights import outputs, workflow_label
from render_readme import render as readme
from test_live_panels import SNAPSHOT, BUILD

NS = {"s": "http://www.w3.org/2000/svg"}
CROSSSELL_README = """# Dealership Cross-Sell Propensity Model

## Results
Scored on a held-out test set of 76,222 customers (20% stratified split, never seen in training).

| Metric | Result |
|---|---|
| LightGBM ROC-AUC | **0.857** (logistic regression baseline: 0.850) |
| Overall response rate | 12.3% |
| Top-decile lift | **3.2×**: the top 10% of customers capture 32.2% of responders |
| Capture at 30% of customers called | **79.0%** of responders, **2.6× lift** |

## Dashboard
Tableau Public: [Dashboard](https://public.tableau.com/app/profile/demo/viz/Demo/Dashboard1)

## Project status
- [x] SQL EDA
- [ ] Model
"""


def tree(*paths):
    return {"truncated": False, "tree": [{"type": "blob", "path": path} for path in paths]}


def fixture():
    project = {**copy.deepcopy(BUILD), "languages": {"TypeScript": 80, "CSS": 20},
               "activity_days": [{"date": "2026-09-11", "count": 0}, {"date": "2026-09-12", "count": 0}], "workflow": None}
    finance = {**project, "inventory": fetch.inventory(tree("src/app/api/ai/chat/route.ts", "messages/en.json"), "finance", {})}
    crosssell = {**project, "inventory": fetch.inventory(tree("sql/01_eda.sql"), "crosssell", {})}
    return {"fetched_at": "2026-09-12T01:00:00Z", "projects": {"finance": finance, "crosssell": crosssell},
            "app": {"http_status": 200, "reachable": True, "checked_at": "2026-09-12T01:00:00Z"}}


class HighlightTests(unittest.TestCase):
    def test_curated_history_can_span_90_days_with_matching_api_bounds(self):
        class Client:
            def pages(inner, url):
                query = parse_qs(urlsplit(url).query)
                self.assertEqual(query["since"], ["2026-06-15T00:00:00+07:00"])
                self.assertEqual(query["sha"], ["exact-tip"])
                yield [{"sha": "first", "commit": {"committer": {"date": "2026-06-14T17:00:00Z"}}},
                       {"sha": "older", "commit": {"committer": {"date": "2026-06-14T16:59:59Z"}}}]
        days = fetch.repository_activity(Client(), {"full_name": "filan214/demo", "commit": {"sha": "exact-tip"}}, date(2026, 9, 12), window_days=90)
        self.assertEqual(len(days), 90)
        self.assertEqual(days[0], {"date": "2026-06-15", "count": 1})
        self.assertEqual(sum(day["count"] for day in days), 1)

    def test_crosssell_inventory_follows_source_and_quotes_readme_results(self):
        data = tree("sql/01_eda.sql", "sql/.gitkeep", "notebooks/01_model.ipynb", "dashboard/customer_scores.csv", "dashboard/screenshot.png")
        data["tree"].append({"type": "tree", "path": "sql/empty.sql"})
        result = fetch.inventory(data, "crosssell", {"README.md": CROSSSELL_README})
        self.assertEqual([len(stage["files"]) for stage in result["stages"]], [1, 1, 1])
        self.assertEqual(result["results"], {"auc": "0.857", "top_decile_lift": "3.2×", "capture_share": "30%", "captured": "79.0%",
                                             "capture_lift": "2.6×", "response_rate": "12.3%", "test_customers": "76,222"})
        self.assertTrue(result["dashboard_url"].startswith("https://public.tableau.com/app/profile/"))
        self.assertEqual([item["done"] for item in result["status"]], [True, False])
        self.assertTrue(result["screenshot"])
        self.assertFalse(result["shap"])

    def test_missing_readme_results_stay_unknown_instead_of_invented(self):
        result = fetch.inventory(tree("README.md"), "crosssell", {"README.md": None})
        self.assertTrue(all(value is None for value in result["results"].values()))
        self.assertEqual((result["dashboard_url"], result["status"]), ("", []))
        content = " ".join(ET.fromstring(outputs({**fixture(), "projects": {**fixture()["projects"], "crosssell": {
            **fixture()["projects"]["crosssell"], "inventory": result}}})["crosssell-spotlight.svg"]).itertext())
        self.assertIn("not linked", content)
        self.assertNotIn("0.857", content)

    def test_finance_tools_are_observed_and_missing_source_is_unknown(self):
        data = tree("src/app/(app)/chat/page.tsx", "src/app/api/ai/chat/route.ts", "messages/en.json", "messages/id.json")
        source = '/*\n fake: tool({})\n*/\n query: tool({}),\n // removed: tool({}),\n chart: tool({}),\n query: tool({})'
        result = fetch.inventory(data, "finance", {"src/lib/ai/tools.ts": source})
        self.assertEqual(result["tools"], ["chart", "query"])
        self.assertEqual(len(result["routes"]), 1)
        self.assertEqual(len(result["locales"]), 2)
        self.assertEqual(sum(f["present"] for f in result["features"]), 1)
        self.assertIsNone(fetch.inventory(data, "finance", {})["tools"])

    def test_partial_tree_is_rejected_instead_of_publishing_lower_counts(self):
        with self.assertRaises(ValueError):
            fetch.inventory({"truncated": True, "tree": []}, "crosssell", {})

    def test_absent_source_is_distinct_from_a_failed_request(self):
        class Client:
            code = 404
            def get(self, url):
                response = requests.Response()
                response.status_code = self.code
                raise requests.HTTPError(response=response)
        client = Client()
        self.assertIsNone(fetch.source_text(client, "filan214/demo", "abc", "path.ts"))
        client.code = 403
        with self.assertRaises(requests.HTTPError):
            fetch.source_text(client, "filan214/demo", "abc", "path.ts")

    def test_failed_github_fetch_preserves_previous_snapshot(self):
        with TemporaryDirectory() as folder:
            snapshot = Path(folder) / "highlights.json"
            before = '{"schema_version":1,"projects":{},"fetched_at":"earlier"}'
            snapshot.write_text(before, encoding="utf-8")
            with patch.object(fetch, "DATA", Path(folder)), patch.object(fetch, "GitHub") as client:
                client.return_value.json.side_effect = requests.HTTPError("Rate limited")
                with self.assertRaises(requests.HTTPError):
                    fetch.main()
            self.assertEqual(snapshot.read_text(encoding="utf-8"), before)

    def test_landing_page_status_needs_success_and_product_marker(self):
        with patch.object(fetch, "GitHub") as client:
            response = client.session.get.return_value
            response.status_code, response.text = 200, "Deployment unavailable"
            self.assertFalse(fetch.check_app(client, "now")["reachable"])
            response.text = "Smart Finn Track"
            self.assertTrue(fetch.check_app(client, "now")["reachable"])
            response.status_code = 503
            self.assertFalse(fetch.check_app(client, "now")["reachable"])
            client.session.get.side_effect = requests.ConnectionError()
            self.assertIsNone(fetch.check_app(client, "now")["http_status"])

    def test_workflow_result_for_older_revision_cannot_be_current_tip(self):
        project = {"workflow": {"name": "Checks", "conclusion": "success", "status": "completed", "matches_tip": False, "head_sha": "abcdef123"}}
        self.assertEqual(workflow_label(project), "Checks: success · abcdef1")

    def test_empty_commit_history_is_flat_and_titles_are_accessible(self):
        for content in outputs(fixture()).values():
            root = ET.fromstring(content)
            self.assertEqual(root.get("width"), "860")
            self.assertTrue(root.find("s:title", NS).text)
            self.assertTrue(root.find("s:desc", NS).text)
            self.assertIsNone(root.find(".//s:script", NS))
            self.assertIn("prefers-color-scheme: dark", root.find("s:style", NS).text)
            self.assertIn("prefers-reduced-motion", root.find("s:style", NS).text)
            points = root.find('.//s:polyline[@class="trace"]', NS).get("points").split()
            self.assertEqual(len({p.split(",")[1] for p in points}), 1)
            self.assertIn("0 commits", " ".join(root.itertext()))

    def test_static_cards_keep_data_without_animation(self):
        with patch.dict(os.environ, {"STATIC": "1"}):
            for content in outputs(fixture()).values():
                root = ET.fromstring(content)
                self.assertIsNone(root.find(".//s:animate", NS))
                self.assertNotIn("@keyframes", root.find("s:style", NS).text)
                self.assertIn("animation:none!important", root.find("s:style", NS).text)

    def test_readme_preserves_project_links_and_replaces_old_business_paragraph(self):
        data = fixture()
        data["projects"]["finance"]["url"] = "https://github.com/filan214/AIFinanceTracker"
        data["projects"]["crosssell"]["url"] = "https://github.com/filan214/dealership-crosssell-propensity"
        data["projects"]["crosssell"]["inventory"] = fetch.inventory(tree("notebooks/01_model.ipynb", "dashboard/screenshot.png"), "crosssell", {"README.md": CROSSSELL_README})
        page = BeautifulSoup(readme(SNAPSHOT, {"pushes": [], "fetched_at": SNAPSHOT["fetched_at"]}, data), "html.parser")
        self.assertNotIn("Building for a real business", page.text)
        self.assertNotIn("Jogja Ride", page.text)
        self.assertEqual(page.find("img", src="./finance-spotlight.svg").parent["href"], fetch.FINANCE_APP)
        dashboard = data["projects"]["crosssell"]["inventory"]["dashboard_url"]
        self.assertEqual(page.find("img", src="./crosssell-spotlight.svg").parent["href"], dashboard)
        self.assertNotIn("EPL", page.text)
        headings = [h.text for h in page.find_all("h3") if "showcase" in h.text]
        self.assertIn("--data-science", headings[0])
        self.assertIn("--finance", headings[1])
        self.assertTrue(page.find("img", src="https://raw.githubusercontent.com/filan214/new-project/abcdef1234/dashboard/screenshot.png").find_parent("details").has_attr("open"))
        self.assertTrue(page.find("a", href=data["projects"]["crosssell"]["url"]))
        self.assertTrue(page.find("a", href=data["projects"]["crosssell"]["url"] + "/blob/abcdef1234/notebooks/01_model.ipynb"))
        self.assertTrue(page.find("img", src="https://raw.githubusercontent.com/filan214/new-project/abcdef1234/dashboard/screenshot.png"))
        self.assertTrue(page.find("img", src="./data-freshness.svg"))
        self.assertEqual(page.find("img", src="./contact-email.svg").parent["href"], "mailto:valentinus.filan@gmail.com")
        self.assertEqual(page.find("img", src="./contact-linkedin.svg").parent["href"],
                         "https://www.linkedin.com/in/valentinus-filan-gunawan-087538226")
        self.assertTrue(all(img.get("alt") for img in page.find_all("img")))
        self.assertIsNone(page.find("script"))

    def test_contact_buttons_are_accessible_themed_svgs(self):
        for name, content in contact().items():
            root = ET.fromstring(content)
            self.assertTrue(root.find("s:title", NS).text)
            self.assertTrue(root.find("s:desc", NS).text)
            self.assertIsNone(root.find(".//s:script", NS))
            self.assertIn("prefers-color-scheme: dark", root.find("s:style", NS).text)
        self.assertIn("valentinus.filan@gmail.com", " ".join(ET.fromstring(contact()["contact-email.svg"]).itertext()))

    def test_freshness_displays_each_collector_time_and_date_only_sources(self):
        root = ET.fromstring(freshness({"fetched_at": "2026-09-12T00:00:00Z"}, {"fetched_at": "2026-09-12T01:00:00Z"},
                                     {"fetched_at": "2026-09-12T02:00:00Z"}, {"as_of": "2026-09-11"}, {"as_of": "2026-09-10"}))
        content = " ".join(root.itertext())
        for expected in ("07:00 WIB", "08:00 WIB", "09:00 WIB", "Calendar as of 2026-09-11", "Languages snapshot 2026-09-10"):
            self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()
