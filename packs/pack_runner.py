#!/usr/bin/env python3
"""Country pack runner (zero-token).

Packs live at packs/<continent>/<country>/ in the main repository.
A pack's pack.json carries one country's filtered hunting kit in
machine-readable form: local search terms, registry-shaped feeds,
communities to follow, and agent-leg hunting grounds (schema:
packs/SCHEMA.md). This runner executes the pack's machine layers:

- feeds are pulled and parsed with the main tracker's parsers,
- hunting grounds that declare a `watch` block have their listing
  page diffed for newly surfaced links.

Everything else in a pack (terms, patterns, communities,
unwatchable grounds) is data for the agent leg, used exactly like
the main registry's social sources. The runner mirrors
tracker.py's run semantics: the same diff rules (changed fires on
title, link, or extra), the same empty-parse and corrupt-snapshot
guards, the same item cap with continuity, the same run lock, and
atomic writes throughout.

Usage:
    python3 packs/pack_runner.py packs/europe/france
    python3 packs/pack_runner.py packs/europe/france --seed
    python3 packs/pack_runner.py packs/europe/france --only fr-korben
    python3 packs/pack_runner.py packs/europe/france --state-dir /tmp/fr

Exit codes: 0 ok, 1 final state write failed, 2 invalid pack or
unknown --only ids, 3 another run holds this state dir's lock.
"""
import argparse
import json
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tracker  # noqa: E402  (fetch, PARSERS, entry, locks, caps)

GROUND_KINDS = ("listing", "site", "directory", "community")
FEED_TIERS = ("wake", "firehose", "curated", "forum")
COMMUNITY_PLATFORMS = ("x", "discord", "telegram", "facebook",
                       "forum", "other")


def validate_pack(pack):
    """Schema gate, mirroring the registry's refusal style: a pack
    that fails validation is refused whole (exit 2), never half-run.
    Returns a list of problems (empty means valid)."""
    problems = []
    if not isinstance(pack, dict):
        return ["pack.json must be a JSON object"]
    if not isinstance(pack.get("version"), int):
        problems.append("pack.json: 'version' must be an integer")
    country = pack.get("country")
    if not isinstance(country, dict):
        problems.append("pack.json: 'country' must be an object")
    else:
        for key in ("code", "name"):
            if not country.get(key):
                problems.append(f"country: '{key}' is required")
        langs = country.get("languages")
        if not isinstance(langs, list) or not langs:
            problems.append("country: 'languages' must be a "
                            "non-empty list")
    ids = []

    def check_id(owner, item):
        sid = item.get("id")
        if not sid or not tracker.ID_RE.match(str(sid)):
            problems.append(f"{owner}: id {sid!r} is missing or does "
                            "not match ^[a-z0-9][a-z0-9_-]*$")
        else:
            ids.append(str(sid))

    for f in pack.get("feeds", []):
        if not isinstance(f, dict):
            problems.append("feeds: every entry must be an object")
            continue
        check_id("feeds", f)
        if f.get("type") != "feed":
            problems.append(f"feeds: {f.get('id')}: type must be "
                            "'feed'")
        if f.get("format") not in tracker.PARSERS:
            problems.append(f"feeds: {f.get('id')}: unknown format "
                            f"{f.get('format')!r}")
        if not f.get("url"):
            problems.append(f"feeds: {f.get('id')}: url is required")
        if f.get("tier") not in FEED_TIERS:
            problems.append(f"feeds: {f.get('id')}: tier must be one "
                            f"of {FEED_TIERS}")
    for c in pack.get("communities", []):
        if not isinstance(c, dict):
            problems.append("communities: every entry must be an "
                            "object")
            continue
        check_id("communities", c)
        if c.get("platform") not in COMMUNITY_PLATFORMS:
            problems.append(f"communities: {c.get('id')}: platform "
                            f"must be one of {COMMUNITY_PLATFORMS}")
        for key in ("name", "url", "focus", "cadence"):
            if not c.get(key):
                problems.append(f"communities: {c.get('id')}: "
                                f"'{key}' is required")
    for g in pack.get("hunting_grounds", []):
        if not isinstance(g, dict):
            problems.append("hunting_grounds: every entry must be an "
                            "object")
            continue
        check_id("hunting_grounds", g)
        if g.get("kind") not in GROUND_KINDS:
            problems.append(f"hunting_grounds: {g.get('id')}: kind "
                            f"must be one of {GROUND_KINDS}")
        for key in ("name", "url", "how", "cadence"):
            if not g.get(key):
                problems.append(f"hunting_grounds: {g.get('id')}: "
                                f"'{key}' is required")
        watch = g.get("watch")
        if watch is not None:
            pat = watch.get("link_pattern") if isinstance(watch, dict) \
                else None
            if not pat:
                problems.append(f"hunting_grounds: {g.get('id')}: "
                                "watch.link_pattern is required")
            else:
                try:
                    re.compile(pat)
                except re.error as e:
                    problems.append(f"hunting_grounds: {g.get('id')}: "
                                    f"watch.link_pattern invalid: {e}")
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append("duplicate source ids across layers: "
                        + ", ".join(dupes))
    terms = pack.get("terms")
    if terms is not None:
        if not isinstance(terms, dict) or not all(
                isinstance(v, list) for v in terms.values()):
            problems.append("terms: must be an object of string lists")
    return problems


def watch_entries(ground):
    """Entries for a watched listing page. The pack's link_pattern is
    matched against each href separately, never embedded in the
    extraction regex, so patterns with their own capture groups
    cannot shift the group numbering."""
    url = ground["url"]
    html = tracker.fetch(url).decode("utf-8", "replace")
    pat = re.compile(ground["watch"]["link_pattern"])
    out = {}
    rx = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.S)
    for m in rx.finditer(html):
        link = m.group(1)
        if not pat.search(link):
            continue
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if text:
            link = urllib.parse.urljoin(url, link)
            out[link] = tracker.entry(text, link)
    return out


def read_snapshot(snap_path):
    """Return (items, corrupt). Valid JSON of the wrong shape counts
    as corrupt, exactly like the tracker."""
    if not snap_path.exists():
        return {}, False
    try:
        data = json.loads(snap_path.read_text())
    except json.JSONDecodeError:
        return {}, True
    if not isinstance(data, dict):
        return {}, True
    return data, False


def diff_source(snap_dir, sid, current, seed, pack_name, diff, totals,
                cap=True):
    """Snapshot + diff one source, mirroring tracker semantics."""
    snap_path = snap_dir / f"{sid}.json"
    old, corrupt = read_snapshot(snap_path)
    if corrupt and not seed:
        # A corrupt snapshot is a failure, never a silent reseed:
        # skipping keeps the damage visible and the file untouched.
        # An explicit --seed is the operator's recovery path.
        diff["errors"].append({
            "source": sid, "pack": pack_name,
            "error": "corrupt snapshot; source skipped, "
                     "snapshot left untouched"})
        return
    if cap and len(current) > tracker.MAX_FEED_ITEMS:
        # Cap with continuity, like the tracker: entries already
        # tracked keep their slots, so the window edge cannot churn
        # fake new/removed pairs between runs.
        kept = {k: v for k, v in current.items() if k in old}
        rest = {k: v for k, v in current.items() if k not in old}
        room = max(0, tracker.MAX_FEED_ITEMS - len(kept))
        current = {**kept, **dict(list(rest.items())[:room])}
    totals[sid] = len(current)
    if not old or seed:
        try:
            tracker.write_json_atomic(snap_path, current)
        except OSError as e:
            diff["errors"].append({
                "source": sid, "pack": pack_name,
                "error": f"snapshot write failed: {e}"[:200]})
            totals.pop(sid, None)
        return
    for key, it in current.items():
        if key not in old:
            diff["new"].append({"source": sid, "pack": pack_name, **it})
        elif (it.get("title") != old[key].get("title")
                or it.get("link") != old[key].get("link")
                or it.get("extra", "") != old[key].get("extra", "")):
            diff["changed"].append({"source": sid, "pack": pack_name,
                                    **it})
    for key in old:
        if key not in current:
            diff["removed"].append({"source": sid, "pack": pack_name,
                                    "key": key})
    try:
        tracker.write_json_atomic(snap_path, current)
    except OSError as e:
        diff["errors"].append({
            "source": sid, "pack": pack_name,
            "error": f"snapshot write failed: {e}"[:200]})
        totals.pop(sid, None)


def _fetch_feed(f):
    parser = tracker.PARSERS[f["format"]]
    entries = parser(tracker.fetch(f["url"]), f)
    # attach the source's first category, like the tracker does
    for it in entries.values():
        if "category" not in it and f.get("categories"):
            it["category"] = f["categories"][0]
    return entries


def _fetch_watch(g):
    return watch_entries(g)


def main():
    ap = argparse.ArgumentParser(description="country pack runner")
    ap.add_argument("pack_dir", help="pack folder, e.g. "
                                     "packs/europe/france")
    ap.add_argument("--state-dir", default="",
                    help="default: <pack_dir>/state")
    ap.add_argument("--seed", action="store_true",
                    help="(re)write baselines and report an empty "
                         "diff; also the recovery path for a corrupt "
                         "snapshot")
    ap.add_argument("--only", default="",
                    help="comma-separated source ids (feeds, "
                         "grounds)")
    args = ap.parse_args()

    pack_dir = Path(args.pack_dir)
    pack_name = pack_dir.name
    try:
        pack = json.loads((pack_dir / "pack.json").read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: cannot load pack.json: {e}", file=sys.stderr)
        return 2
    problems = validate_pack(pack)
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        return 2

    all_ids = ([f["id"] for f in pack.get("feeds", [])]
               + [c["id"] for c in pack.get("communities", [])]
               + [g["id"] for g in pack.get("hunting_grounds", [])])
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    if only:
        unknown = sorted(only - set(all_ids))
        if unknown:
            print("error: unknown source ids: " + ", ".join(unknown),
                  file=sys.stderr)
            return 2

    state = Path(args.state_dir) if args.state_dir else pack_dir / "state"
    state.mkdir(parents=True, exist_ok=True)
    lock = tracker.acquire_lock(state)
    if lock is None:
        print("error: another run holds the lock for this state dir",
              file=sys.stderr)
        return 3
    try:
        return _run(args, pack, pack_dir, pack_name, state, only)
    finally:
        lock.unlink(missing_ok=True)


def _run(args, pack, pack_dir, pack_name, state, only):
    snap_dir = state / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    diff = {"new": [], "changed": [], "removed": [], "errors": []}
    totals = {}
    wake_ids = ({f["id"] for f in pack.get("feeds", []) if f.get("wake")}
                | {c["id"] for c in pack.get("communities", [])
                   if c.get("wake")}
                | {g["id"] for g in pack.get("hunting_grounds", [])
                   if g.get("wake")})

    # (source id, entries or None, error, kind)
    results = []
    jobs = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for f in pack.get("feeds", []):
            if only and f["id"] not in only:
                continue
            jobs[f["id"]] = ("feed", pool.submit(_fetch_feed, f))
        for g in pack.get("hunting_grounds", []):
            if not g.get("watch"):
                continue
            if only and g["id"] not in only:
                continue
            jobs[g["id"]] = ("watch", pool.submit(_fetch_watch, g))
        for sid, (kind, fut) in jobs.items():
            try:
                results.append((sid, fut.result(), None, kind))
            except Exception as e:
                results.append((sid, None, str(e)[:200], kind))

    for sid, current, error, kind in results:
        if error is not None:
            diff["errors"].append({"source": sid, "pack": pack_name,
                                   "error": error})
            continue
        if not current:
            diff["errors"].append({
                "source": sid, "pack": pack_name,
                "error": "empty parse; previous snapshot kept"})
            continue
        cap = True
        if kind == "feed":
            src = next(f for f in pack["feeds"] if f["id"] == sid)
            # curated feeds are exempt from the cap, like the
            # tracker's curated lists
            cap = src.get("tier") != "curated"
        diff_source(snap_dir, sid, current, args.seed, pack_name,
                    diff, totals, cap=cap)

    try:
        tracker.write_json_atomic(state / "last-diff.json", diff)
    except OSError as e:
        print(f"error: cannot write state files: {e}",
              file=sys.stderr)
        return 1
    summary = {
        "pack": pack_name,
        "sources_ok": len(totals),
        "sources_failed": [e["source"] for e in diff["errors"]],
        "items_per_source": totals,
        "new_count": len(diff["new"]),
        "changed_count": len(diff["changed"]),
        "removed_count": len(diff["removed"]),
        "wake_new_count": sum(1 for d in diff["new"]
                              if d["source"] in wake_ids),
        "wake_changed_count": sum(1 for d in diff["changed"]
                                  if d["source"] in wake_ids),
    }
    try:
        tracker.write_json_atomic(state / "last-run.json", summary)
    except OSError as e:
        print(f"error: cannot write state files: {e}",
              file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
