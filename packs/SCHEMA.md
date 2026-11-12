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
`terms`, `feeds`, `gdelt_presets`, `hunting_grounds`,
`local_patterns`.

### country

Required: `code` (ISO 3166-1 alpha-2, e.g. `FR`), `name`,
`languages` (non-empty list of ISO 639-1 codes). Nothing else: any
field no code reads is dead data and does not belong in a pack.

### terms

An object of string lists, grouped by role. Groups seen in packs so
far: `core` (the category nouns with the local word for free),
`no_card_markers` (the local phrasing for "no bank card", the
highest-precision trial signal), `credit` (credit-offer phrasings),
`community_phrases` (how the local community itself says free),
`umbrella` (deal vocabulary, useful but retail-polluted),
`negative_markers` (phrasings that mark retail noise). Groups are
vocabulary for the agent leg and for composing GDELT queries; the
runner does not filter by them.

### feeds

Registry-shaped entries, same fields and meanings as `sources.json`:
required `id`, `type` (must be `"feed"`), `format` (any format the
tracker parses: `rss`, `atom`, `json-list`, `md-table`, `html-list`),
`url`, `tier` (`wake`, `firehose`, or `curated`), plus the usual
optional `name`, `categories`, `wake`, `notes`, `item_url_pattern`,
`list_key`. The runner pulls these with the tracker's parsers, caps
non-curated feeds at the tracker's item cap with continuity, and
diffs them like the main registry.

### gdelt_presets

GDELT is a free, keyless news index; a preset is one standing query
for the agent's news layer. Required: `id`, `query` (a full GDELT
query string, with the country and language filters written into
it, e.g. `sourcecountry:FR sourcelang:fra`). Optional: `timespan`
(default `1m`; widen a preset to `3m` in pack.json for a first
sweep), `maxrecords` (default 25), `wake` (default false). The
runner calls presets serially with at least 6 seconds between
calls, because GDELT allows roughly one request per 5 seconds per
IP. An empty answer is valid and keeps the preset's snapshot.

### hunting_grounds

The agent leg's targets: places an agent reads the way it reads the
main registry's social sources. Required: `id`, `kind` (one of
`listing`, `site`, `directory`, `community`), `name`, `url`, `how`
(how the agent works the ground and verifies a find), `cadence`
(how often it is worth reading, in words). Optional: `wake`
(default false) and `watch`.

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

Every `id` in a pack, across all three layers, must match
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
corrupt snapshot), `--skip-gdelt`, `--only <ids>` (unknown ids are
refused). Exit codes: 0 ok, 1 final state write failed, 2 invalid
pack or unknown ids, 3 another run holds the state dir's lock.
Runs of different packs from one machine should be sequential: the
GDELT spacing is per process, and GDELT's limit is per IP.

## Authoring rules

A pack entry earns its place the same way a registry source does:
a find from it must be worth acting on, monitoring, and claiming
for the pack's intended user. Verify terms and feeds live before
writing them down, and date any density claim in its `notes`
("checked YYYY-MM-DD"), because feeds drift. Keep the README a
faithful cover of pack.json: if the two disagree, the pack is
wrong somewhere, and an auditor will find it.
