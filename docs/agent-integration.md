# Agent integration contract

freebie-tracker is agent-agnostic by construction. The puller (`tracker.py`) reads a registry and a state directory, and writes JSON. Everything an agent platform needs to adopt the system is in this contract; everything else (how the agent is woken, where state lives, whose credentials it holds) is platform detail that this document maps explicitly.

## Inputs

| Input | What it is | Who owns it |
|---|---|---|
| `sources.json` | The source registry: feeds, program pages, social hunting grounds, each with tier, wake flag, categories, region and notes. | The project (canonical copy lives in this repo) |
| Owner profile | The safety-filter parameters of one owner: what signup walls they can pass, blocked providers, wanted categories, country, languages. Template: `templates/profile.example.json`. | Each owner, privately |
| State directory | Snapshots, `last-diff.json`, `last-run.json`. Created by `--seed`, then maintained by every run. | Each deployment |
| Owner inventory | What the owner already holds, so the agent dedupes finds against it. Template: `templates/inventory.example.md`. | Each owner, privately |
| Reported ledger | Everything the agent has already reported, passing or rejected, so nothing is reported twice. Deployment-local file. | Each deployment |

## Outputs

`last-run.json`, one line of truth per run:

```json
{"sources_ok": 17, "sources_failed": [], "items_per_source": {"baipiaoji": 131, "...": "..."}, "new_count": 22, "changed_count": 1, "removed_count": 22, "wake_new_count": 2, "wake_changed_count": 1}
```

`last-diff.json`, the full diff: per source, the new, changed and removed entries, each with title, link, extra text and category tags, plus the wake counts. A source whose parse comes back empty is treated as failed: its previous snapshot is kept and no removals are reported for it.

The wake rule is the whole economy of the system: an agent run is justified only when `wake_new_count + wake_changed_count` is greater than zero. Firehose sources are diffed and stored but never counted toward the wake.

## Waking the agent, per platform

The puller never wakes anyone by itself. A thin wrapper does, and the wrapper is the only platform-specific piece:

1. **Scheduled hook or cron with an exit gate (reference pattern).** A scheduler runs the puller every 4 to 6 hours. The wrapper reads `last-run.json`; if the wake counts are zero, or every source failed, it exits silently. Otherwise it starts the agent with the diff as its brief. This is how the reference deployment on Muse works.
2. **Agent with its own scheduler.** Platforms that let an agent poll on a timer (many local and self-hosted agent runtimes) can fold the wrapper into the agent's own loop: run the puller as a tool, read the counts, stop if zero.
3. **CI schedule.** A hosted CI cron (for example GitHub Actions) can run the puller and publish `last-diff.json` as an artifact or a comment; a separate agent process consumes it. Workable, but the diff leaves the owner's machine, so owners who keep their radar private should prefer patterns 1 or 2.
4. **File watcher.** A long-running agent process can watch the state directory and react when `last-diff.json` changes with wake counts above zero. Simple, but the watcher itself must be supervised.

Whichever pattern is used, the agent's side of the work is identical and is specified in `docs/agent-guide.md`: verify candidates at the official provider, apply the owner's profile filter, dedupe against the inventory and the reported ledger, report briefly per category, and never claim, connect or schedule anything without the owner's explicit instruction.

## What differs and what never does

| Differs per platform | Never differs |
|---|---|
| Scheduler and wake mechanism | Registry format and source semantics |
| Where the state directory lives | Parsers, snapshot and diff behavior |
| How the agent gets credentials (it should not need any for the puller) | The wake rule and firehose discipline |
| Report delivery channel | The safety filter and the report-once rule |

## Country packs

A deployment focused on one country can add that country's pack (`packs/<continent>/<country>/`, format in `packs/SCHEMA.md`) as a second, self-contained input layer beside the registry. The contract keeps the same shape: the pack's feeds run through `packs/pack_runner.py`, which writes the same `last-run.json` and `last-diff.json` shapes into the pack's own state directory, and the same wake rule applies to its summary. The pack's terms, communities, and hunting grounds are agent-leg data, worked exactly like the registry's social sources: read them with the pack's local vocabulary, verify finds at the official provider, and pass them through the same safety filter and report-once ledger.

## Porting checklist

1. Copy the repo; run `python3 tracker.py --state-dir <dir> --seed` once.
2. Write the owner profile and inventory from the templates; keep both outside git.
3. Wire one wake pattern from the list above; test it with a seeded baseline (expected result: silence).
4. Give the agent `docs/agent-guide.md` as its operating brief, plus the paths of the profile, inventory and reported ledger.
5. Let it run a week before judging wake noise; demote a wake flag only on evidence, per source.
6. For a country-specific deployment, adopt the matching country pack as well: seed its runner once, and wire its summary into the same wake pattern.
