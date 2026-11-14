"""Tests for packs/pack_runner.py with a stubbed tracker.fetch.

Covers the happy paths (seed, changed, new) and the failure paths
the pack audit demanded: fetch failure, empty parses, corrupt
snapshots and --seed recovery, write failures, unsafe or duplicate
ids, community validation, --only, the run lock, watch URL
handling, and the real France pack loading and validating.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packs"))
import tracker  # noqa: E402
import pack_runner  # noqa: E402

RSS_V1 = (b"<rss><channel>"
          b"<item><title>Outil A</title><link>https://x.test/a</link></item>"
          b"</channel></rss>")
RSS_V2 = (b"<rss><channel>"
          b"<item><title>Outil A+</title><link>https://x.test/a</link></item>"
          b"</channel></rss>")
RSS_TWO = (b"<rss><channel>"
           b"<item><title>Un</title><link>https://x.test/1</link></item>"
           b"<item><title>Deux</title><link>https://x.test/2</link></item>"
           b"</channel></rss>")
RSS_ONE = (b"<rss><channel>"
           b"<item><title>Un</title><link>https://x.test/1</link></item>"
           b"</channel></rss>")
RSS_EMPTY = b"<rss><channel></channel></rss>"
LIST_V1 = (b'<a href="https://disboard.org/server/111">HostOne</a>'
           b'<a href="/about">About</a>')
LIST_V2 = (b'<a href="https://disboard.org/server/111">HostOne</a>'
           b'<a href="https://disboard.org/server/222">HostTwo</a>')
LIST_REL = b'<a href="/server/333">HostThree</a>'
LIST_SQ = b"<a href='https://disboard.org/server/444'>HostFour</a>"


def base_pack():
    return {
        "version": 1,
        "country": {"code": "FR", "name": "France",
                    "languages": ["fr"]},
        "terms": {"core": ["VPS gratuit"]},
        "feeds": [{"id": "fr-feed", "type": "feed", "format": "rss",
                   "url": "https://x.test/feed", "tier": "firehose",
                   "wake": False, "categories": ["dev-tools"]}],
        "communities": [{"id": "fr-hunter", "platform": "x",
                         "name": "@petitchasseur",
                         "url": "https://x.com/petitchasseur",
                         "focus": "Posts French hosting trials.",
                         "cadence": "daily"}],
        "hunting_grounds": [
            {"id": "fr-list", "kind": "listing", "name": "Listing",
             "url": "https://disboard.org/servers/tag/vps?fl=fr",
             "how": "Read the listing.", "cadence": "weekly",
             "watch": {"link_pattern": r"server/\d+"}}],
    }


class PackRunnerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pack_dir = Path(self.tmp.name) / "france"
        self.pack_dir.mkdir(parents=True)
        self.state = Path(self.tmp.name) / "state"
        self.data = {"feed": RSS_V1, "list": LIST_V1}
        self.broken = set()
        self.write_pack(base_pack())

        def fake_fetch(url, timeout=25):
            key = "list" if "disboard" in url else "feed"
            if key in self.broken:
                raise OSError("network down")
            return self.data[key]
        self.fake_fetch = fake_fetch

    def tearDown(self):
        self.tmp.cleanup()

    def write_pack(self, pack):
        (self.pack_dir / "pack.json").write_text(json.dumps(pack))

    def run_runner(self, *extra):
        argv = ["pack_runner.py", str(self.pack_dir),
                "--state-dir", str(self.state), *extra]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(tracker, "fetch", self.fake_fetch):
            return pack_runner.main()

    def summary(self):
        return json.loads((self.state / "last-run.json").read_text())

    def diff(self):
        return json.loads((self.state / "last-diff.json").read_text())

    # happy paths

    def test_seed_then_changes_across_layers(self):
        self.assertEqual(self.run_runner("--seed"), 0)
        s = self.summary()
        self.assertEqual(s["sources_ok"], 2)
        self.assertEqual(s["items_per_source"],
                         {"fr-feed": 1, "fr-list": 1})
        self.data["feed"] = RSS_V2
        self.data["list"] = LIST_V2
        self.assertEqual(self.run_runner(), 0)
        s = self.summary()
        self.assertEqual(s["changed_count"], 1)
        self.assertEqual(s["new_count"], 1)
        d = self.diff()
        self.assertEqual(d["new"][0]["source"], "fr-list")
        self.assertEqual(d["new"][0]["pack"], "france")
        self.assertEqual(d["changed"][0]["title"], "Outil A+")

    def test_removed_semantics(self):
        self.data["feed"] = RSS_TWO
        self.assertEqual(self.run_runner("--seed"), 0)
        self.data["feed"] = RSS_ONE
        self.assertEqual(self.run_runner(), 0)
        self.assertEqual(self.summary()["removed_count"], 1)

    def test_watch_relative_url_is_resolved(self):
        self.data["list"] = LIST_REL
        self.assertEqual(self.run_runner("--seed"), 0)
        snap = json.loads((self.state / "snapshots"
                           / "fr-list.json").read_text())
        self.assertIn("https://disboard.org/server/333", snap)

    def test_watch_single_quoted_href(self):
        self.data["list"] = LIST_SQ
        self.assertEqual(self.run_runner("--seed"), 0)
        snap = json.loads((self.state / "snapshots"
                           / "fr-list.json").read_text())
        self.assertIn("https://disboard.org/server/444", snap)

    def test_forum_tier_feed_is_accepted(self):
        pack = base_pack()
        pack["feeds"][0]["tier"] = "forum"
        self.write_pack(pack)
        self.assertEqual(self.run_runner("--seed"), 0)
        self.assertEqual(self.summary()["sources_ok"], 2)

    # failure paths

    def test_fetch_failure_is_recorded_not_fatal(self):
        self.broken.add("feed")
        self.assertEqual(self.run_runner("--seed"), 0)
        self.assertIn("fr-feed", self.summary()["sources_failed"])

    def test_empty_feed_parse_keeps_snapshot(self):
        self.assertEqual(self.run_runner("--seed"), 0)
        snap = self.state / "snapshots" / "fr-feed.json"
        before = snap.read_text()
        self.data["feed"] = RSS_EMPTY
        self.assertEqual(self.run_runner(), 0)
        self.assertIn("fr-feed", self.summary()["sources_failed"])
        self.assertEqual(snap.read_text(), before)

    def test_corrupt_snapshot_blocks_then_seed_recovers(self):
        self.assertEqual(self.run_runner("--seed"), 0)
        snap = self.state / "snapshots" / "fr-feed.json"
        snap.write_text("this is not json{{{")
        self.assertEqual(self.run_runner(), 0)
        self.assertIn("fr-feed", self.summary()["sources_failed"])
        self.assertEqual(snap.read_text(), "this is not json{{{")
        self.assertEqual(self.run_runner("--seed"), 0)
        self.assertEqual(self.summary()["sources_failed"], [])
        self.assertEqual(self.summary()["items_per_source"]["fr-feed"],
                         1)

    def test_wrong_shape_snapshot_counts_as_corrupt(self):
        self.assertEqual(self.run_runner("--seed"), 0)
        snap = self.state / "snapshots" / "fr-feed.json"
        snap.write_text("[1, 2, 3]")
        self.assertEqual(self.run_runner(), 0)
        self.assertIn("fr-feed", self.summary()["sources_failed"])
        self.assertEqual(snap.read_text(), "[1, 2, 3]")

    def test_final_write_failure_returns_1(self):
        real = tracker.write_json_atomic

        def flaky(path, obj):
            if Path(path).name == "last-diff.json":
                raise OSError("disk full")
            return real(path, obj)
        argv = ["pack_runner.py", str(self.pack_dir),
                "--state-dir", str(self.state), "--seed"]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(tracker, "fetch", self.fake_fetch), \
                mock.patch.object(tracker, "write_json_atomic", flaky):
            self.assertEqual(pack_runner.main(), 1)

    def test_run_lock_blocks_second_run(self):
        self.state.mkdir(parents=True)
        (self.state / "run.lock").write_text("99999 1")
        self.assertEqual(self.run_runner("--seed"), 3)

    # pack validation and selection

    def test_unsafe_id_is_refused(self):
        pack = base_pack()
        pack["feeds"][0]["id"] = "../evil"
        self.write_pack(pack)
        self.assertEqual(self.run_runner("--seed"), 2)

    def test_duplicate_id_across_layers_is_refused(self):
        pack = base_pack()
        pack["hunting_grounds"][0]["id"] = "fr-feed"
        self.write_pack(pack)
        self.assertEqual(self.run_runner("--seed"), 2)

    def test_communities_are_agent_leg_data(self):
        # A valid community entry validates, is a known id, and is
        # never pulled by the runner: the seed still counts only
        # the machine sources.
        self.assertEqual(self.run_runner("--seed"), 0)
        s = self.summary()
        self.assertNotIn("fr-hunter", s["items_per_source"])
        self.assertEqual(self.run_runner("--only", "fr-hunter"), 0)

    def test_invalid_community_platform_is_refused(self):
        pack = base_pack()
        pack["communities"][0]["platform"] = "tiktok"
        self.write_pack(pack)
        self.assertEqual(self.run_runner("--seed"), 2)

    def test_community_missing_focus_is_refused(self):
        pack = base_pack()
        del pack["communities"][0]["focus"]
        self.write_pack(pack)
        self.assertEqual(self.run_runner("--seed"), 2)

    def test_only_selection_and_unknown_id(self):
        self.assertEqual(self.run_runner("--seed", "--only", "fr-feed"),
                         0)
        self.assertEqual(list(self.summary()["items_per_source"]),
                         ["fr-feed"])
        self.assertEqual(self.run_runner("--only", "nope"), 2)


class RealFrancePackCase(unittest.TestCase):
    def test_france_pack_validates(self):
        pack = json.loads((ROOT / "packs" / "europe" / "france"
                           / "pack.json").read_text())
        self.assertEqual(pack_runner.validate_pack(pack), [])


if __name__ == "__main__":
    unittest.main()
