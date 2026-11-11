# freebie-tracker

**A free-stuff radar built for AI agents.** A small zero-dependency puller watches curated free-tier lists, deal forums and government program portals across several countries, diffs what changed, and wakes an AI agent only when something new appears. The agent verifies candidates against official provider pages, applies the owner's safety filter, and reports what is actually worth claiming.

Built to be run by an agent on behalf of its owner: the machine half is dumb and cheap (pure Python standard library, no API keys, no LLM calls), the judgment half is the agent's.

## Why

Free tiers, AI credits, GPU subsidies and giveaway codes are scattered across curated lists in China, startup communities in Korea, developer lists in the West, and social posts that vanish in hours. A human cannot watch all of it. An agent can, if the watching itself costs almost nothing and the agent only spends attention when the diff is non-empty.

This project generalizes a production setup that hunts free tiers across Chinese curated lists (lanmao, baipiaoji, jidan), deal forums (LINUX DO, V2EX, NodeSeek), and Facebook/X hunter posts, and adds the layer most trackers miss: **government AI subsidy programs** (Korea's AI Voucher, India's IndiaAI compute, EU EuroHPC access, and more), where the largest free allocations actually live.

## How it works

```
sources.json          registry: feeds, program pages, social hunting grounds
     |
tracker.py            pulls every feed, snapshots it, diffs vs last run
     |
state/last-diff.json  new / changed / removed entries, per category
     |
agent (wake-gated)    runs only when wake sources changed; verifies each
                      candidate at the official provider page, applies
                      the safety filter, dedupes vs the owner's
                      inventory, and reports briefly per category
```

Wake discipline is the core trick: firehose feeds (marketplace chatter, general software blogs) are diffed and stored but **never wake the agent alone**. Only curated lists and deal-specific forums do. In production this keeps agent cost near zero while missing nothing that matters.

## Quickstart

```bash
git clone https://github.com/wiskovic/freebie-tracker
cd freebie-tracker
python3 tracker.py --seed   # first run: write baselines
python3 tracker.py          # later runs: pull and diff
cat state/last-diff.json    # what changed
```

Schedule it however your agent platform schedules things (cron, a webhook poller, a systemd timer). A 4 to 6 hour rhythm works well; public giveaway codes can die within hours, so the social leg in `docs/agent-guide.md` matters for those.

## Categories

Every source and entry is tagged: `ai`, `gpu`, `cloud`, `vps`, `database`, `dev-tools`, `saas`, `design`, `education`, `gov-programs`, `games`, `other`. Reports group finds by category so the owner sees, for example, only the new VM offers when that is what they care about. See `docs/categories.md`.

## Sources at a glance

| Layer | Examples | How |
|---|---|---|
| Curated lists (CN) | baipiaoji limits.json, lanmao offers, jidan | machine feed |
| Deal forums (CN) | LINUX DO welfare, V2EX promotions | machine feed |
| Firehose (CN) | NodeSeek, Appinn, ghxi, iPlaySoft | machine feed, passive |
| Developer lists (global) | free-for.dev | machine feed |
| Developer news (KR) | GeekNews | machine feed |
| Government programs | KR AI Voucher (NIPA/MSIT), K-Startup, IndiaAI, EuroHPC, J-Startup, AI Singapore | agent page checks |
| Gated startup programs | AWS Activate, Google Cloud for Startups, Microsoft for Startups, GitHub Student Pack | agent page checks, gated |
| Social hunting grounds | X hunter accounts, Vietnamese VPS Facebook groups | agent leg, on wake |

Full registry with notes: `sources.json`. Human-readable catalog: `docs/sources.md`.

## The safety filter (summary)

A listing is a **lead, not a find**. Before an agent reports anything as claimable it must verify at the official provider source and reject:

- offers that need a credit card the owner cannot or will not provide
- offers behind real-name / KYC verification the owner cannot pass
- account resales, carpools, shared or relayed API credits, token bait
- expired offers and paid discounts dressed as freebies
- region-locked offers the owner is not eligible for

Full filter and the agent operating manual: `docs/agent-guide.md`.

## Layout

```
tracker.py              the puller (stdlib only)
sources.json            source registry (feeds, pages, social)
docs/agent-guide.md     how an AI agent runs this: loop, filter, reporting
docs/categories.md      category taxonomy
docs/sources.md         source catalog with per-region notes
examples/               a sample agent report
templates/              owner inventory template for dedupe
state/                  runtime snapshots and diffs (git-ignored)
```

## For agent platforms

Any agent that can run a shell command on a schedule can operate this: run the puller, read `state/last-run.json`, and wake the reasoning agent only when `wake_new_count + wake_changed_count > 0`. The puller itself needs no credentials and makes no LLM calls, so the standing cost of the radar is effectively zero.

## Disclaimer

Everything this tool surfaces is an unverified lead until an agent (or the owner) checks the official provider page. Offers change, expire and get region-locked without notice. Never enter credentials, codes or payment data anywhere except the provider's own site, and only on the owner's explicit instruction.

## License

MIT. See `LICENSE`.
