# Contributing

The highest-value contribution to this project is a **source**: a place where real free offers surface early and often. Code contributions are welcome too. Both are judged by one standard: does it make the radar catch more real finds without making it noisier?

## Suggest or add a source

Open an issue with the **Suggest a source** template, or send a pull request that adds the source to `sources.json` (and a line in `docs/sources.md`).

A good source is:

- **Public.** No login needed to read it (feeds), or an official public page (programs).
- **Structured enough to diff.** Feeds must fit an existing parser format in `tracker.py` (`json-tools`, `md-table`, `md-list`, `rss`, `jina-linuxdo`). Pages and social sources are read by the agent leg instead.
- **Proven.** It has surfaced at least one real, claimable offer before. Link the offer in your issue or PR.
- **Alive.** Updated by someone other than us, on a rhythm that makes polling worthwhile.

Set `wake` honestly: only curated lists and deal-specific forums may wake the agent. Everything else is firehose, however interesting it is. Tag `region` and `categories` from the taxonomy in `sources.json`, and write the one-line `notes` that tells the next agent what the source is and what usually fails the safety filter in it.

Before opening the PR, run the source once against a scratch state dir and paste the resulting counts:

```bash
python3 tracker.py --only your-source-id --state-dir /tmp/ft-check
```

## Code rules

- **Standard library only.** No new dependencies, ever. If a feature needs one, it does not belong in the puller.
- **One bad source never kills a run.** Isolate failures per source and record them in the summary.
- **An empty parse is a failure**, never a mass removal. Keep the previous snapshot.
- **Snapshots and state files are written atomically** (temp file plus rename).
- Keep the puller dumb: judgment belongs to the agent and `docs/agent-guide.md`, not to the script.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Parser changes need a fixture test in `tests/test_parsers.py`. CI runs the same suite on every push and pull request.
