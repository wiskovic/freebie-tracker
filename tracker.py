#!/usr/bin/env python3
"""freebie-tracker puller (zero-token).

Pulls every `feed` source registered in sources.json, stores a snapshot
per source under state/snapshots/, and diffs against the previous
snapshot: new, changed and removed entries land in state/last-diff.json,
a run summary in state/last-run.json.

Pure Python standard library. No API key, no LLM, no accounts. It is the
dumb, cheap half of the system on purpose: an AI agent reads the diff,
verifies candidates against official provider pages, applies the owner's
safety filter and reports. See docs/agent-guide.md.

Design notes (learned in production):
- Sources are tiered. Only wake=true sources count toward the wake
  counters in the summary; an agent scheduler should wake the agent only
  when wake_new_count + wake_changed_count > 0. Firehose sources are
  diffed and stored but never wake the agent alone (token economy).
- One failing source never kills a run. Failures are listed in the
  summary and in the diff's "errors".
- An empty parse counts as a failure, never as "everything was
  removed": the previous snapshot is kept, so a source that changes
  its format cannot burn the baseline or fire a false wake.
- Responses are capped at 8 MB, snapshots and state files are written
  atomically (temp file plus rename), and sources are fetched in
  parallel so a full run stays fast even when a few sources hang.
- A first run (or --seed) only writes baselines and reports no diff.
- A "changed" entry means its title, link or extra text differs from
  the snapshot; any of the three fires it.
- HTTP 429 and 5xx and connection errors get one retry (429 honors a
  numeric Retry-After, capped at 120 s; the others wait 5 s).
- A corrupt snapshot is a source failure, never a silent reseed: the
  file is left untouched and the source is skipped for that run.
- A lock file in the state dir keeps overlapping runs from stepping
  on each other's snapshots; a lock older than 30 minutes is stale.

Usage:
    python3 tracker.py                 # pull + diff
    python3 tracker.py --seed          # (re)write baselines, empty diff
    python3 tracker.py --only baipiaoji,lanmao
    python3 tracker.py --state-dir /tmp/ft-state
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
MAX_FEED_ITEMS = 120  # cap per feed source; curated lists are exempt
MAX_BYTES = 8 * 1024 * 1024  # refuse absurdly large responses
FETCH_WORKERS = 6  # sources are fetched and parsed in parallel

# Keyword map from a markdown-list section title to a category.
SECTION_CATEGORY = [
    (r"artificial intelligence|machine learning|\bai\b", "ai"),
    (r"gpu|compute", "gpu"),
    (r"database|storage|backup", "database"),
    (r"vps|virtual|hosting|server", "vps"),
    (r"cloud|paas|iaas|serverless", "cloud"),
    (r"education|learn|student|course", "education"),
    (r"design|media|photo|video", "design"),
    (r"game", "games"),
    (r"dev|code|ci/cd|api|analytics|monitoring|security|domain|email", "dev-tools"),
]


def fetch(url, timeout=25):
    for attempt in (1, 2):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError(f"response over {MAX_BYTES} bytes")
            return data
        except urllib.error.HTTPError as e:
            retryable = e.code == 429 or 500 <= e.code < 600
            if not retryable or attempt == 2:
                raise
            delay = 20 if e.code == 429 else 5
            if e.code == 429 and e.headers is not None:
                ra = e.headers.get("Retry-After", "")
                if ra.isdigit():
                    delay = min(int(ra), 120)
            time.sleep(delay)
        except urllib.error.URLError:
            if attempt == 2:
                raise
            time.sleep(5)


def write_json_atomic(path, obj):
    """Write JSON via a temp file plus rename, so a process killed
    mid-write can never leave a corrupt snapshot behind."""
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    os.replace(tmp, path)


def entry(title, link="", extra=""):
    # Coerce defensively: a source that serves a null or a number where
    # a string belongs must not take the whole source down with it.
    title = "" if title is None else str(title)
    link = "" if link is None else str(link)
    extra = "" if extra is None else str(extra)
    return {"title": title.strip(), "link": link.strip(),
            "extra": extra.strip()[:400]}


# ---------------- parsers: each returns {key: entry} ----------------

def parse_json_tools(raw, src):
    """JSON list of tools (baipiaoji shape: {"tools": [{slug,name,url,
    category,quota}]}). Configure another list key via src['list_key']."""
    data = json.loads(raw)
    out = {}
    for t in data.get(src.get("list_key", "tools"), []):
        if not isinstance(t, dict):
            continue
        slug = t.get("slug") or t.get("id") or t.get("name", "")
        if not slug:
            continue
        extra = " :: ".join(str(t.get(k, "")) for k in
                            ("category", "quota", "description")).strip(" :")
        out[str(slug)] = entry(t.get("name", slug), t.get("url", ""), extra)
    return out


def parse_md_table(raw, src):
    """Pipe-table markdown (lanmao shape). Rows that contain a URL are
    entries; if the source sets item_url_pattern, only matching URLs
    count. Name = first cell, extra = next cells."""
    text = raw.decode("utf-8", "replace")
    pattern = src.get("item_url_pattern")
    out = {}
    for line in text.splitlines():
        if "|" not in line:
            continue
        urls = re.findall(r"https?://[^\s)\]]+", line)
        if pattern:
            urls = [u for u in urls if re.match(pattern, u)]
        if not urls:
            continue
        parts = [re.sub(r"\[|\]", "", p).strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        name = parts[0] if parts else urls[0]
        # A first cell written as a markdown link arrives here as
        # "Name(https://...)" once brackets are stripped; keep just
        # the name so diff titles stay readable.
        m = re.match(r"^(.*?)\(https?://[^)]*\)\s*$", name)
        if m and m.group(1).strip():
            name = m.group(1).strip()
        # Key by the full URL: unique per offer page. (An earlier
        # version keyed by the URL's last path segment, which collided
        # whenever two hosts shared a final segment.)
        out[urls[0]] = entry(name, urls[0], " :: ".join(parts[1:4]))
    return out


def parse_md_list(raw, src):
    """Sectioned markdown link list (free-for.dev shape). Bullets like
    '* [Name](url) - description' under '## Section' headers. Each entry
    inherits a category guessed from its section title."""
    text = raw.decode("utf-8", "replace")
    out = {}
    section = ""
    for line in text.splitlines():
        h = re.match(r"^#{1,3}\s+(.*)", line)
        if h:
            section = h.group(1).strip()
            continue
        m = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)\s*[-–:]?\s*(.*)", line)
        if not m:
            continue
        name, url, desc = m.group(1), m.group(2), m.group(3)
        cat = ""
        for pat, c in SECTION_CATEGORY:
            if re.search(pat, section, re.I):
                cat = c
                break
        e = entry(name, url, (section + " :: " + desc) if section else desc)
        if cat:
            e["category"] = cat
        out[url] = e
    return out


def _rss_regex(text):
    out = {}
    for m in re.finditer(r"<item>(.*?)</item>", text, re.S):
        blk = m.group(1)
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", blk, re.S)
        l = re.search(r"<link>(.*?)</link>", blk, re.S)
        g = re.search(r"<guid[^>]*>(.*?)</guid>", blk, re.S)
        if not t:
            continue
        link = (l.group(1) if l else (g.group(1) if g else "")).strip()
        key = link or hashlib.md5(t.group(1).encode()).hexdigest()
        out[key] = entry(re.sub(r"<[^>]+>", "", t.group(1)), link)
    return out


def parse_rss(raw, src):
    text = raw.decode("utf-8", "replace")
    out = {}
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return _rss_regex(text)
    items = root.findall(".//item")
    if items:
        for it in items:
            title = it.findtext("title", "")
            link = it.findtext("link", "") or it.findtext("guid", "")
            if title:
                out[link or hashlib.md5(title.encode()).hexdigest()] = \
                    entry(title, link)
        return out
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for e in root.findall(".//atom:entry", ns):
        title = e.findtext("atom:title", "", ns)
        link = ""
        for ln in e.findall("atom:link", ns):
            if ln.get("rel") in (None, "alternate"):
                link = ln.get("href", "")
                break
        if title:
            out[link or hashlib.md5(title.encode()).hexdigest()] = \
                entry(title, link)
    return out or _rss_regex(text)


def parse_jina_linuxdo(raw, src):
    """The Jina reader returns the LINUX DO feed as markdown whose items
    look like '### [title](https://linux.do/t/topic/NNNN)'."""
    text = raw.decode("utf-8", "replace")
    out = {}
    for m in re.finditer(r"^###\s+\[(.*?)\]\((https://linux\.do/t/topic/\d+)\)",
                         text, re.M):
        out[m.group(2)] = entry(m.group(1), m.group(2))
    return out


PARSERS = {
    "json-tools": parse_json_tools,
    "md-table": parse_md_table,
    "md-list": parse_md_list,
    "rss": parse_rss,
    "jina-linuxdo": parse_jina_linuxdo,
}


ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
LOCK_STALE_SECONDS = 1800


def acquire_lock(state):
    """Take the run lock for a state dir; return the lock path, or None
    when another fresh run already holds it. A lock older than
    LOCK_STALE_SECONDS is treated as abandoned and replaced."""
    lock = state / "run.lock"
    for _ in range(2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
            except OSError:
                continue
            if age < LOCK_STALE_SECONDS:
                return None
            lock.unlink(missing_ok=True)
            continue
        os.write(fd, f"{os.getpid()} {int(time.time())}".encode())
        os.close(fd)
        return lock
    return None


def main():
    ap = argparse.ArgumentParser(description="freebie-tracker puller")
    ap.add_argument("--sources", default=str(BASE / "sources.json"))
    ap.add_argument("--state-dir", default=str(BASE / "state"))
    ap.add_argument("--only", default="", help="comma-separated source ids")
    ap.add_argument("--seed", action="store_true",
                    help="(re)write baselines and report an empty diff")
    args = ap.parse_args()

    state = Path(args.state_dir)
    state.mkdir(parents=True, exist_ok=True)
    lock = acquire_lock(state)
    if lock is None:
        print("error: another run holds the lock for this state dir",
              file=sys.stderr)
        return 3
    try:
        return _run(args, state)
    finally:
        lock.unlink(missing_ok=True)


def _run(args, state):
    registry = json.loads(Path(args.sources).read_text())
    sources = [s for s in registry["sources"] if s.get("type") == "feed"]
    # Source ids become snapshot file names; refuse anything that could
    # wander out of the snapshots dir.
    bad = [s["id"] for s in sources if not ID_RE.match(str(s["id"]))]
    if bad:
        print(f"error: unsafe source id(s): {', '.join(bad)}",
              file=sys.stderr)
        return 2
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        unknown = wanted - {s["id"] for s in sources}
        if unknown:
            print(f"error: unknown source id(s): "
                  f"{', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        sources = [s for s in sources if s["id"] in wanted]

    snap_dir = state / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)

    diff = {"new": [], "changed": [], "removed": [], "errors": []}
    totals = {}
    wake_ids = {s["id"] for s in sources if s.get("wake")}

    def pull_one(src):
        """Fetch and parse one source; return (src, entries, error)."""
        parser = PARSERS.get(src.get("format", ""))
        if parser is None:
            return src, None, "unknown format"
        try:
            return src, parser(fetch(src["url"]), src), None
        except Exception as e:  # one bad source never kills the run
            return src, None, str(e)[:200]

    # Fetch in parallel (worst case stays well inside a scheduler's
    # timeout), then diff and write in registry order so the output is
    # deterministic.
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        results = list(pool.map(pull_one, sources))

    for src, current, error in results:
        sid = src["id"]
        if error is not None:
            diff["errors"].append({"source": sid, "error": error})
            continue
        if not current:
            # An empty parse almost always means the source changed its
            # format or served a block page, not that every offer died.
            # Treat it as a failure and KEEP the old snapshot: recording
            # hundreds of fake removals would burn the baseline and fire
            # a false wake.
            diff["errors"].append({
                "source": sid,
                "error": "empty parse; previous snapshot kept"})
            continue
        snap_path = snap_dir / f"{sid}.json"
        old = {}
        corrupt = False
        if snap_path.exists():
            try:
                old = json.loads(snap_path.read_text())
            except json.JSONDecodeError:
                corrupt = True
        if corrupt and not args.seed:
            # A corrupt snapshot is a failure, never a silent reseed:
            # skipping keeps the damage visible and the file untouched.
            # An explicit --seed is the operator's recovery path.
            diff["errors"].append({
                "source": sid,
                "error": "corrupt snapshot; source skipped, "
                         "snapshot left untouched"})
            continue
        if src.get("tier") != "curated" and len(current) > MAX_FEED_ITEMS:
            # Cap with continuity: entries already tracked keep their
            # slots, so the window edge cannot churn fake new/removed
            # pairs between runs.
            kept = {k: v for k, v in current.items() if k in old}
            rest = {k: v for k, v in current.items() if k not in old}
            room = max(0, MAX_FEED_ITEMS - len(kept))
            current = {**kept, **dict(list(rest.items())[:room])}
        # attach source categories (a parser may set a finer one)
        for it in current.values():
            if "category" not in it and src.get("categories"):
                it["category"] = src["categories"][0]
        totals[sid] = len(current)

        def save_snapshot():
            try:
                write_json_atomic(snap_path, current)
                return True
            except OSError as e:
                # A failed write must not abort the rest of the run.
                # The diff entries stay (they will repeat next run,
                # since the baseline was not advanced), the source is
                # reported as failed, and the run continues.
                diff["errors"].append({
                    "source": sid,
                    "error": f"snapshot write failed: {e}"[:200]})
                totals.pop(sid, None)
                return False

        if not old or args.seed:
            save_snapshot()
            continue
        for key, it in current.items():
            if key not in old:
                diff["new"].append({"source": sid, **it})
            elif (it.get("title") != old[key].get("title")
                    or it.get("link") != old[key].get("link")
                    or it.get("extra", "") != old[key].get("extra", "")):
                diff["changed"].append({"source": sid, **it})
        for key in old:
            if key not in current:
                diff["removed"].append({"source": sid, "key": key})
        save_snapshot()

    try:
        write_json_atomic(state / "last-diff.json", diff)
    except OSError as e:
        print(f"error: cannot write last-diff.json: {e}", file=sys.stderr)
        return 1
    summary = {
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
        write_json_atomic(state / "last-run.json", summary)
    except OSError as e:
        print(f"error: cannot write last-run.json: {e}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
