"""End-to-end tests for tracker.main() with a stubbed fetch.

These cover the audit scenarios the parser tests cannot reach:
changed-entry detection, corrupt snapshots, --only validation,
source-id validation, the run lock, fetch retries and entry()
coercion of non-string values.
"""
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tracker  # noqa: E402

RSS_V1 = (b"<rss><channel>"
          b"<item><title>Alpha</title><link>https://x.test/a</link></item>"
          b"<item><title>Beta</title><link>https://x.test/b</link></item>"
          b"</channel></rss>")
RSS_V2 = (b"<rss><channel>"
          b"<item><title>Alpha v2</title><link>https://x.test/a</link></item>"
          b"<item><title>Beta</title><link>https://x.test/b</link></item>"
          b"</channel></rss>")


def rss_many(n):
    items = "".join(
        f"<item><title>Item {i}</title>"
        f"<link>https://x.test/{i}</link></item>" for i in range(n))
    return ("<rss><channel>" + items + "</channel></rss>").encode()


def make_registry(state, source_id="demo"):
    src = {"id": source_id, "name": "Demo", "type": "feed",
           "format": "rss", "url": "https://x.test/feed",
           "tier": "forum", "wake": True, "region": "global",
           "categories": ["other"], "notes": ""}
    reg = Path(state) / "reg.json"
    reg.write_text(json.dumps({"sources": [src]}))
    return reg


class MainRunCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "state"
        self.reg = make_registry(self.tmp.name)
        self.feed = {"data": RSS_V1}

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *extra):
        argv = ["tracker.py", "--sources", str(self.reg),
                "--state-dir", str(self.state), *extra]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(tracker, "fetch",
                                  lambda url, timeout=25: self.feed["data"]):
            return tracker.main()

    def summary(self):
        return json.loads((self.state / "last-run.json").read_text())

    def test_count_drop_warns_on_collapse(self):
        self.feed["data"] = rss_many(20)
        self.assertEqual(self.run_main("--seed"), 0)
        self.feed["data"] = rss_many(5)
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.summary()["count_warnings"],
                         [{"source": "demo", "previous": 20,
                           "current": 5}])

    def test_count_drop_silent_above_half(self):
        self.feed["data"] = rss_many(20)
        self.assertEqual(self.run_main("--seed"), 0)
        self.feed["data"] = rss_many(12)
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.summary()["count_warnings"], [])

    def test_changed_fires_on_title_change(self):
        self.assertEqual(self.run_main("--seed"), 0)
        self.feed["data"] = RSS_V2
        self.assertEqual(self.run_main(), 0)
        s = self.summary()
        self.assertEqual(s["changed_count"], 1)
        self.assertEqual(s["wake_changed_count"], 1)
        diff = json.loads((self.state / "last-diff.json").read_text())
        self.assertEqual(diff["changed"][0]["title"], "Alpha v2")

    def test_corrupt_snapshot_fails_without_reseed(self):
        self.assertEqual(self.run_main("--seed"), 0)
        snap = self.state / "snapshots" / "demo.json"
        snap.write_text("{not json")
        before = snap.read_bytes()
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.summary()["sources_failed"], ["demo"])
        self.assertEqual(snap.read_bytes(), before)

    def test_wrong_shape_snapshot_counts_as_corrupt(self):
        self.assertEqual(self.run_main("--seed"), 0)
        snap = self.state / "snapshots" / "demo.json"
        snap.write_text("[1, 2, 3]")
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.summary()["sources_failed"], ["demo"])
        self.assertEqual(snap.read_text(), "[1, 2, 3]")

    def test_only_unknown_id_is_an_error(self):
        self.assertEqual(self.run_main("--only", "nope"), 2)

    def test_unsafe_source_id_is_rejected(self):
        make_registry(self.tmp.name, source_id="../evil")
        self.assertEqual(self.run_main(), 2)

    def test_fresh_lock_blocks_run(self):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "run.lock").write_text("1 1")
        self.assertEqual(self.run_main(), 3)


class CountDroppedCase(unittest.TestCase):
    def test_boundaries(self):
        self.assertFalse(tracker.count_dropped(9, 0))
        self.assertFalse(tracker.count_dropped(10, 5))
        self.assertTrue(tracker.count_dropped(10, 4))
        self.assertFalse(tracker.count_dropped(20, 10))
        self.assertTrue(tracker.count_dropped(20, 9))
        self.assertTrue(tracker.count_dropped(131, 40))


class FetchAndEntryCase(unittest.TestCase):
    def test_entry_coerces_non_strings(self):
        self.assertEqual(tracker.entry(None, 123, None),
                         {"title": "", "link": "123", "extra": ""})

    def test_fetch_retries_once_on_503(self):
        calls = {"n": 0}

        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self, n=-1):
                return b"ok"

        def fake_urlopen(req, timeout=25):
            calls["n"] += 1
            if calls["n"] == 1:
                raise urllib.error.HTTPError(
                    "https://x.test", 503, "unavailable", None, None)
            return Resp()

        with mock.patch.object(tracker.urllib.request, "urlopen",
                               fake_urlopen), \
                mock.patch.object(tracker.time, "sleep", lambda s: None):
            self.assertEqual(tracker.fetch("https://x.test"), b"ok")
        self.assertEqual(calls["n"], 2)


if __name__ == "__main__":
    unittest.main()
