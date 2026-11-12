# freebie-tracker

[![CI](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [简体中文](README.zh-CN.md)

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

## What the output looks like

A run prints one summary line and writes the full diff to `state/last-diff.json`:

```json
{"sources_ok": 14, "sources_failed": [], "items_per_source": {"baipiaoji": 131, "lanmao": 341, "jidan": 40, "linuxdo": 25, "v2ex": 50, "lowendtalk": 100, "nodeseek": 20, "free-for-dev": 1379, "geeknews": 20, "...": "..."}, "new_count": 22, "changed_count": 1, "removed_count": 22, "wake_new_count": 2, "wake_changed_count": 1}
```

```json
{"new": [
  {"source": "v2ex", "category": "saas", "title": "[share] open-source tool, lecture video to PDF, fully local, no API key", "link": "https://www.v2ex.com/t/1256309"},
  {"source": "lowendtalk", "category": "vps", "title": "Giveaway: 100x free VPS for a year", "link": "https://lowendtalk.com/discussion/221872/..."}
 ],
 "changed": [
  {"source": "baipiaoji", "category": "ai", "title": "Exa", "extra": "search :: $20 signup credit + $10/month"}
 ],
 "removed": [], "errors": []}
```

The agent wakes only because `wake_new_count + wake_changed_count` is above zero, then verifies, filters and reports. A sample finished report is in `examples/report-example.md`.

## Categories

Every source and entry is tagged: `ai`, `gpu`, `cloud`, `vps`, `database`, `dev-tools`, `saas`, `design`, `education`, `gov-programs`, `games`, `other`. Reports group finds by category so the owner sees, for example, only the new VM offers when that is what they care about. See `docs/categories.md`.

## Sources at a glance

| Layer | Examples | How |
|---|---|---|
| Curated lists (CN) | baipiaoji limits.json, lanmao offers, jidan | machine feed |
| Deal forums | LINUX DO welfare, V2EX promotions, LowEndTalk offers | machine feed |
| Firehose | NodeSeek, Appinn, ghxi, iPlaySoft, Slickdeals, OzBargain | machine feed, passive |
| Developer lists (global) | free-for.dev | machine feed |
| Developer news (KR) | GeekNews | machine feed |
| Government programs | KR AI Voucher (NIPA/MSIT), K-Startup, IndiaAI, EuroHPC, J-Startup, AI Singapore | agent page checks |
| Gated startup programs | AWS Activate, Google Cloud for Startups, Microsoft for Startups, GitHub Student Pack | agent page checks, gated |
| Social hunting grounds | X hunter accounts, niche community groups (Facebook, Discord, forums) that share free tiers and giveaways | agent leg, on wake |

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
templates/              owner inventory and profile templates
state/                  runtime snapshots and diffs (git-ignored)
```

## For agent platforms

Any agent that can run a shell command on a schedule can operate this: run the puller, read `state/last-run.json`, and wake the reasoning agent only when `wake_new_count + wake_changed_count > 0`. The puller itself needs no credentials and makes no LLM calls, so the standing cost of the radar is effectively zero.

**Production status:** the reference deployment runs this exact code. Its agent polls every 6 hours from a checkout of this repository, keeps its snapshots and owner inventory in a private deployment folder outside git, and reports finds to its owner. Changes here are tested against the live snapshots before they ship.

## Disclaimer

Everything this tool surfaces is an unverified lead until an agent (or the owner) checks the official provider page. Offers change, expire and get region-locked without notice. Never enter credentials, codes or payment data anywhere except the provider's own site, and only on the owner's explicit instruction.

## License

MIT. See `LICENSE`.
