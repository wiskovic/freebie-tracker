# Country pack schema

A country pack is one country's filtered hunting kit for this
project, in machine-readable form. Packs live in the main repository
at:

    packs/<continent>/<country>/

Each pack folder holds two files:

- `pack.json`, the pack itself: structured data any AI agent or tool
  can load and act on.
- `README.md`, the human cover: the same material in prose, for a
  person deciding whether the pack fits them.

A pack folder may also hold `GUESSES.md`, a third file that
records every point where the author had to choose because the
schema did not answer the question, with what was chosen and why,
dated. It is documentation only: the runner and linter never read
it, and it is never required. Its guesses are the raw material for
the next schema revision.

One shared runner executes every pack's machine layers:

    python3 packs/pack_runner.py packs/<continent>/<country>

Continents are lowercase English directory names (`europe`, `asia`,
`africa`, `north-america`, `south-america`, `oceania`); country
folders are the lowercase English country name (`france`,
`saudi-arabia`). The runner validates a pack before running it and
refuses an invalid pack whole (exit 2), with the same id and format
rules as the main registry.

## pack.json blocks

Top level: `version` (integer), `about` (one short paragraph: the
country's freebie shape in two or three sentences), `country`,
`terms`, `feeds`, `communities`, `hunting_grounds`,
`local_patterns`.

### country

Required: `code` (ISO 3166-1 alpha-2, e.g. `FR`), `name`,
`languages` (non-empty list of ISO 639-1 codes). Nothing else: any
field no code reads is dead data and does not belong in a pack.

List every language the agent must read to search and verify the
pack's sources, not only the country's official language(s).
Example: Saudi Arabia lists `["ar", "en"]` because the communities
mix Arabic posts with English tool names and product pages, while
France lists `["fr"]` only because its sources are French. Keep
the list to languages actually used in the pack's sources.

### terms

An object of string lists, grouped by role. Groups seen in packs so
far: `core` (the category nouns with the local word for free),
`no_card_markers` (the local phrasing for "no bank card", the
highest-precision trial signal), `credit` (credit-offer phrasings),
`community_phrases` (how the local community itself says free),
`umbrella` (deal vocabulary, useful but retail-polluted),
`negative_markers` (phrasings that mark retail noise). Groups are
vocabulary for the agent leg: they are how the agent searches the
pack's communities and hunting grounds in the local language; the
runner does not filter by them.

Find a country's `no_card_markers` from live provider pages, not
by translating English: read signup and FAQ pages in the local
language and take the 1-3 phrasings actually used there for "no
credit card required" / "no payment method" / "no fees", most
precise first, keeping spelling variants people really type (e.g.
Saudi `بدون بطاقة ائتمانية`, `بدون بطاقة`, `بدون رسوم`, with both
`مجاناً` and `مجانا` kept in community phrases). If no local
phrasing exists, say so in GUESSES.md instead of inventing one.

### feeds

Registry-shaped entries, same fields and meanings as `sources.json`:
required `id`, `type` (must be `"feed"`), `format` (any format the
tracker parses: `rss`, `atom`, `json-list`, `md-table`, `html-list`),
`url`, `tier` (`wake`, `firehose`, `curated`, or `forum`, the same
feed-tier vocabulary as `sources.json`, so an entry copied from the
main registry validates as-is), plus the usual
optional `name`, `categories`, `wake`, `notes`, `item_url_pattern`,
`list_key`. The runner pulls these with the tracker's parsers, caps
non-curated feeds at the tracker's item cap with continuity, and
diffs them like the main registry.

`feeds` may be an empty list (`"feeds": []`) when no stable
machine feed for the country exists. Do not invent a feed to fill
it, and do not fall back to a news feed: packs deliberately carry
no news-index layer. In that case the machine layer is a watched
hunting ground (a `watch` block on a server-rendered listing),
and the pack's README must say so in its "Machine feeds" section
with the check date.

### communities

The grassroots layer, and the pack's center of gravity: specific
people and groups who post finds where news coverage never
reaches. Each entry names one source an agent follows and reads
the way it reads the main registry's social sources. Required:
`id`, `platform` (one of `x`, `discord`, `telegram`, `facebook`,
`forum`, `other`), `name`, `url` (the profile, server, channel,
or group address), `focus` (what surfaces there and why it earns
attention, in one or two sentences), `cadence`. Optional: `wake`
(default false).

`cadence` uses one of: `daily`, `weekly`, `monthly`, `quarterly`,
`on wake`, or `on wake, or weekly`. `on wake` means read it only
when another source in the pack wakes the agent; `on wake, or
weekly` means read it on wake, and at least weekly even without a
wake. Do not invent other cadence words; if none fits, pick the
closest and explain the real rhythm in the entry's `how` or
`focus` text. The same vocabulary applies to hunting grounds.

Communities are agent-leg data: the runner never pulls them.
Verify each one live before writing it down, under the same
admission test as every other layer: what it posts must be worth
acting on, monitoring, and claiming.

Worked example of a community entry:

```json
{
  "id": "xx-hunter-example",
  "platform": "x",
  "name": "@examplehunter",
  "url": "https://x.com/examplehunter",
  "focus": "Posts local cloud credit giveaways and free VPS trials, usually within hours of launch.",
  "cadence": "daily"
}
```

### hunting_grounds

The agent leg's targets: places an agent reads the way it reads the
main registry's social sources. Required: `id`, `kind` (one of
`listing`, `site`, `directory`, `community`), `name`, `url`, `how`
(how the agent works the ground and verifies a find), `cadence`
(the fixed vocabulary defined under Communities above). Optional:
`wake` (default false) and `watch`.

`watch` is for grounds whose listing page is server-rendered HTML:
the runner then diffs the page's matching links between runs.
Fields: `link_pattern`, a regular expression matched against each
href on the page (matched separately, never embedded in the
extraction, so patterns with their own groups are safe). A ground
whose listing is JavaScript-rendered gets no `watch` block; say so
in its `how` text instead, like the France pack's DISBOARD ground.

Worked example of a watched ground:

```json
{
  "id": "xx-board-hosts",
  "kind": "listing",
  "name": "ExampleBoard hosting offers, local filter",
  "url": "https://exampleboard.org/offers?lang=xx",
  "how": "Read the listing, open newly surfaced hosts, verify any offer at the host's own site before reporting it.",
  "cadence": "on wake, or weekly",
  "watch": {"link_pattern": "exampleboard\\.org/offer/\\d+"}
}
```

Worked example of a waking feed (a pack feed may wake the agent,
exactly like a registry wake feed):

```json
{
  "id": "xx-deals",
  "type": "feed",
  "format": "rss",
  "url": "https://example.org/feed",
  "tier": "wake",
  "wake": true,
  "categories": ["vps", "cloud"],
  "notes": "Small local board whose offers are usually claimable."
}
```

### local_patterns

A short list of the country's structural facts that change how an
agent hunts there (where offers actually surface, which marker
means claimable, what the local dead ends are). Facts, not rejected
candidates: a pack never carries a checked-and-rejected list; that
audit trail belongs to whoever researched the pack, outside it.

## Ids and wake

Every `id` in a pack, across all blocks, must match
`^[a-z0-9][a-z0-9_-]*$` and be unique within the pack. Ids prefix
with the country code (`fr-`, `sa-`) by convention. Wake accounting
follows the main system: the run summary counts new and changed
items from sources with `wake: true`, in any layer.

## Runner contract

State lives in `<pack_dir>/state` by default (git-ignored), or where
`--state-dir` points: per-source snapshots under `snapshots/`, the
diff in `last-diff.json`, the summary in `last-run.json`, in the
same shapes the main tracker writes, with every diff entry also
carrying the pack's folder name in a `pack` field. Options:
`--seed` (write baselines, empty diff; also the recovery path for a
corrupt snapshot), `--only <ids>` (unknown ids are refused;
community ids are known ids, but they are agent-leg data, so
selecting one runs no machine source). Exit codes: 0 ok, 1 final
state write failed, 2 invalid pack or unknown ids, 3 another run
holds the state dir's lock.

## Outcome log (for deployments)

A deployment that runs a pack keeps one append-only outcome log
per pack, outside git, beside its other deployment records. One
line per item the pack surfaced and the agent judged or acted on:

    YYYY-MM-DD | <source id> | <item title or link> | <verdict> | <short note>

Verdicts: `claimed`, `claimable` (verified at the provider,
waiting on the owner), `noise`, `expired`, `blocked` (card,
region, or verification wall). The log is the pack's evidence
base: it powers the report-once discipline (an item in the log is
never reported again) and the periodic verdict on whether the
pack earns its place, per claimable find rather than per raw
signal.

## Authoring rules

A pack is built grassroots-first. Claimable freebies surface in
communities (hunters on social platforms, local forums, chat
groups) long before, and usually instead of, news coverage, so a
pack's weight sits in its communities, hunting grounds, and local
terms. A pack deliberately carries no news-index layer: news
presets were removed from this format in November 2026 on exactly
this evidence, because a news index can only report what
journalism covered, and freebie opportunities are grassroots
events.

A pack entry earns its place the same way a registry source does:
a find from it must be worth acting on, monitoring, and claiming
for the pack's intended user. Verify terms and feeds live before
writing them down, and date any density claim in its `notes`
("checked YYYY-MM-DD"), because feeds drift. Keep the README a
faithful cover of pack.json: if the two disagree, the pack is
wrong somewhere, and an auditor will find it. Write the README in
English, the repository's base language; local search terms keep
their native spelling, accents included, exactly as in pack.json.

### Research protocol

How a pack is researched, in order. This protocol is distilled
from the France harvest and the Saudi adoption test; follow it so
two authors produce the same quality of pack.

1. Map the country's grassroots surfaces first: search live, in
   the local language, for where free tiers, trials, and credits
   actually surface (hunter accounts, local forums, chat groups,
   provider Discords, community boards). News coverage is not a
   surface. Date every structural claim you will later write into
   `about` or `local_patterns`.
2. Build the term groups from live material, never from
   translation: core nouns from real offer pages, no-card markers
   from provider signup and FAQ pages (see Terms), community
   phrases in the spellings people actually type, negative
   markers from the dominant local retail meaning of "free".
3. Test every candidate source live before judging it: pull the
   feed, open the profile or page, read recent items. A density
   claim needs a counted sample and a check date.
4. Sort each admitted source into the block that matches how it
   is consumed: a pullable feed, a community the agent follows, a
   ground the agent works. A server-rendered listing gets a
   `watch` block with a pattern matched against each href;
   a JavaScript-rendered one gets none, and its `how` says so.
5. Record every rejection, with its reason, in research notes
   outside the pack; a pack never carries a checked-and-rejected
   list. Record every question the schema does not answer in the
   pack's GUESSES.md, with the choice made and why, dated.
6. Finish mechanically, not by feel: the pack lints clean, the
   conformance tests pass, and the machine layer seed-runs with
   no failures. A pack that has not passed all three is a draft,
   not a pack.

### Editorial gate

The admission test as criteria. A source enters a pack only if
every applicable point holds; when one fails, the source is
rejected or the pack text carries the constraint openly.

- Claimable shape: what the source surfaces can be acted on,
  monitored, and claimed by the pack's intended user. Registry
  categories include `education` and `gov-programs`: a real free
  allocation that is claimed by applying (a bootcamp, a national
  programme) passes this point.
- Verified live: the author opened the source during this
  research round and saw the claimed content. A visibly dormant
  source (no posts for a year or more) is refused.
- Not retail noise: a source whose dominant output is price
  tracking, consumer discounts, free delivery, or paid-plan
  add-ons (free SSL, free support, free migration on a paid
  plan) is refused. That dominance is also where the pack's
  negative markers come from.
- No invented layers: no news feed to fill the machine layer,
  and no feed at all when none is stable. An empty block with a
  dated explanation beats a padded one.
- Eligibility honesty: when a source's offers mostly require a
  local ID, phone number, or residency, that constraint is
  written into the entry's `focus` or `how`, or into
  `local_patterns`, so the deployment's safety filter can act on
  it.
- Right block: a specific provider offer with an enrolment
  status that can change is a hunting ground, not a local
  pattern; patterns are structural facts only.
