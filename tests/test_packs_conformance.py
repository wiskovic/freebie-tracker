"""Conformance tests for EVERY real country pack in packs/.

Adding a pack folder automatically puts it under test, with no new
test code: each pack must pass the linter (schema validation plus
README/pack.json mechanical consistency), and its feeds must pull
and seed cleanly through the real runner with a stubbed fetch.
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
import lint_packs  # noqa: E402

STUB_LINK = "https://example.com/stub"


def stub_payload(feed):
    fmt = feed.get("format")
    if fmt in ("rss", "atom"):
        return (b'<rss><channel><item><title>Stub</title>'
                b"<link>" + STUB_LINK.encode() + b"</link>"
                b"</item></channel></rss>")
    if fmt == "json-list":
        item = {"id": "stub-1", "title": "Stub", "link": STUB_LINK}
        if feed.get("list_key"):
            return json.dumps({feed["list_key"]: [item]}).encode()
        return json.dumps([item]).encode()
    if fmt == "md-table":
        return ("| Name | Link |\n|---|---|\n"
                f"| Stub | {STUB_LINK} |\n").encode()
    if fmt == "html-list":
        return (f'<ul><li><a href="{STUB_LINK}">Stub</a></li></ul>'
                ).encode()
    raise AssertionError(f"no stub payload for format {fmt!r}")


class AllPacksCase(unittest.TestCase):
    def test_at_least_one_pack_exists(self):
        self.assertTrue(lint_packs.discover_packs(),
                        "no country packs discovered under packs/")

    def test_every_pack_passes_the_linter(self):
        for pack_dir in lint_packs.discover_packs():
            with self.subTest(pack=pack_dir.name):
                self.assertEqual(lint_packs.check_pack(pack_dir), [])

    def test_every_pack_feeds_seed_through_the_runner(self):
        for pack_dir in lint_packs.discover_packs():
            pack = json.loads((pack_dir / "pack.json").read_text())
            feeds = pack.get("feeds", [])
            if not feeds:
                continue
            payloads = {f["url"]: stub_payload(f) for f in feeds}
            with self.subTest(pack=pack_dir.name), \
                    tempfile.TemporaryDirectory() as tmp:
                argv = ["pack_runner.py", str(pack_dir),
                        "--state-dir", str(Path(tmp) / "state"),
                        "--seed",
                        "--only", ",".join(f["id"] for f in feeds)]
                with mock.patch.object(sys, "argv", argv), \
                        mock.patch.object(
                            tracker, "fetch",
                            lambda url, timeout=25: payloads[url]):
                    self.assertEqual(pack_runner.main(), 0)
                summary = json.loads((Path(tmp) / "state"
                                      / "last-run.json").read_text())
                self.assertEqual(summary["sources_failed"], [])
                self.assertEqual(
                    set(summary["items_per_source"]),
                    {f["id"] for f in feeds})


if __name__ == "__main__":
    unittest.main()
