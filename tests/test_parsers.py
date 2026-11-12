"""Tests for freebie-tracker: parser units, the source registry, and
end-to-end tracker runs against file:// feeds (no network).

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("tracker", ROOT / "tracker.py")
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)


class ParserTests(unittest.TestCase):
    def test_json_tools_keyed_by_slug(self):
        raw = json.dumps({"tools": [
            {"slug": "exa", "name": "Exa", "url": "https://exa.ai",
             "category": "search", "quota": "$20 credit"},
            {"slug": "demo", "name": "Demo", "url": "", "category": "ai",
             "quota": "100 req/day"},
        ]}).encode()
        out = tracker.parse_json_tools(raw, {})
        self.assertEqual(set(out), {"exa", "demo"})
        self.assertIn("search", out["exa"]["extra"])

    def test_md_table_keyed_by_full_url(self):
        src = {"item_url_pattern": r"https://lanmao\.ai/zh/o/[a-z0-9\-]+/?"}
        raw = ("| Name | Quota | Note |\n"
               "|---|---|---|\n"
               "| Tongyi | https://lanmao.ai/zh/o/tongyi-tingwu/ | free |\n"
               "| Groq | https://lanmao.ai/zh/o/groq-whisper/ | free |\n"
               ).encode()
        out = tracker.parse_md_table(raw, src)
        self.assertEqual(set(out), {"https://lanmao.ai/zh/o/tongyi-tingwu/",
                                    "https://lanmao.ai/zh/o/groq-whisper/"})
        self.assertEqual(
            out["https://lanmao.ai/zh/o/tongyi-tingwu/"]["title"], "Tongyi")

    def test_md_table_same_last_segment_different_hosts_no_collision(self):
        raw = ("| Name | Link |\n"
               "|---|---|\n"
               "| A | https://a.test/offer |\n"
               "| B | https://b.test/offer |\n").encode()
        out = tracker.parse_md_table(raw, {})
        self.assertEqual(set(out), {"https://a.test/offer",
                                    "https://b.test/offer"})

    def test_md_table_name_from_markdown_link_cell(self):
        raw = ("| API | Description | Free Tier | Auth |\n"
               "|---|---|---|---|\n"
               "| [Foo AI](https://foo.ai) | chat | 100 req/day | apiKey |\n"
               ).encode()
        out = tracker.parse_md_table(raw, {})
        self.assertEqual(len(out), 1)
        item = next(iter(out.values()))
        self.assertEqual(item["title"], "Foo AI")
        self.assertEqual(item["link"], "https://foo.ai")

    def test_md_list_inherits_section_category(self):
        raw = ("## AI and Machine Learning\n\n"
               "* [SomeAI](https://someai.example) - free tier\n\n"
               "## Databases\n\n"
               "* [SomeDB](https://somedb.example) - free plan\n").encode()
        out = tracker.parse_md_list(raw, {})
        self.assertEqual(out["https://someai.example"]["category"], "ai")
        self.assertEqual(out["https://somedb.example"]["category"],
                         "database")

    def test_rss_items(self):
        raw = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
               b"<item><title>Deal One</title>"
               b"<link>https://example.com/1</link></item>"
               b"<item><title>Deal Two</title>"
               b"<link>https://example.com/2</link></item>"
               b"</channel></rss>")
        out = tracker.parse_rss(raw, {})
        self.assertEqual(len(out), 2)
        self.assertEqual(out["https://example.com/1"]["title"], "Deal One")

    def test_jina_linuxdo_headings(self):
        raw = ("# Welfare\n\n"
               "### [Free VPS giveaway](https://linux.do/t/topic/123)\n\n"
               "### [Credit drop](https://linux.do/t/topic/456)\n").encode()
        out = tracker.parse_jina_linuxdo(raw, {})
        self.assertEqual(len(out), 2)
        self.assertIn("https://linux.do/t/topic/123", out)


class RegistryTests(unittest.TestCase):
    def test_registry_is_valid(self):
        reg = json.loads((ROOT / "sources.json").read_text())
        ids = [s["id"] for s in reg["sources"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate source ids")
        known_cats = set(reg["categories"])
        for s in reg["sources"]:
            self.assertTrue(set(s["categories"]) <= known_cats,
                            f"{s['id']}: unknown category")
            if s["type"] == "feed":
                self.assertIn(s["format"], tracker.PARSERS,
                              f"{s['id']}: unknown parser format")
                self.assertTrue(s["url"].startswith("http"))


RSS_ONE = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
           b"<item><title>New Deal</title>"
           b"<link>https://example.com/new</link></item>"
           b"</channel></rss>")
RSS_EMPTY = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
             b"</channel></rss>")


class IntegrationTests(unittest.TestCase):
    def _setup(self, feed_bytes, snapshot):
        tmp = Path(tempfile.mkdtemp())
        feed = tmp / "feed.xml"
        feed.write_bytes(feed_bytes)
        reg = {"version": 1, "categories": ["saas"], "sources": [
            {"id": "t", "name": "Test", "type": "feed", "format": "rss",
             "url": f"file://{feed}", "region": "global", "tier": "forum",
             "wake": True, "categories": ["saas"]}]}
        reg_path = tmp / "sources.json"
        reg_path.write_text(json.dumps(reg))
        state = tmp / "state"
        (state / "snapshots").mkdir(parents=True)
        if snapshot is not None:
            (state / "snapshots" / "t.json").write_text(
                json.dumps(snapshot))
        return tmp, reg_path, state

    def _run(self, reg_path, state):
        r = subprocess.run(
            [sys.executable, str(ROOT / "tracker.py"),
             "--sources", str(reg_path), "--state-dir", str(state)],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_new_entry_detected(self):
        old = {"https://example.com/old":
               {"title": "Old", "link": "https://example.com/old",
                "extra": ""}}
        _, reg_path, state = self._setup(RSS_ONE, old)
        summary = self._run(reg_path, state)
        self.assertEqual(summary["new_count"], 1)
        self.assertEqual(summary["removed_count"], 1)
        self.assertEqual(summary["wake_new_count"], 1)

    def test_empty_parse_keeps_snapshot(self):
        old = {"https://example.com/a":
               {"title": "A", "link": "https://example.com/a", "extra": ""},
               "https://example.com/b":
               {"title": "B", "link": "https://example.com/b", "extra": ""}}
        _, reg_path, state = self._setup(RSS_EMPTY, old)
        summary = self._run(reg_path, state)
        self.assertEqual(summary["sources_failed"], ["t"])
        self.assertEqual(summary["removed_count"], 0)
        kept = json.loads((state / "snapshots" / "t.json").read_text())
        self.assertEqual(set(kept), set(old),
                         "snapshot must survive an empty parse")


if __name__ == "__main__":
    unittest.main()
