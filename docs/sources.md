# Source catalog

The machine registry is `sources.json`; this file is the human-readable version, with the reasoning per region. Sources are grouped by how an agent consumes them.

## Machine feeds, curated (wake the agent)

- **baipiaoji** (CN, `ai`): machine-readable JSON of AI free quotas at baipiaoji.com/limits.json. Its editorial rule is the same as ours: only entries traceable to official provider sources.
- **lanmao** (CN, `ai`): a large markdown table of AI free-quota offers, updated daily, with claim thresholds and dates. The single richest AI-credit source we know. Many entries are China-shaped or real-name walled; the filter decides per owner.
- **jidan** (CN, `ai`, `saas`): curated free-credit postings as RSS.
- **free-for.dev** (global, mixed): the classic developer free-tier list, maintained on GitHub. A change here usually means a tier was born, changed, or died. Entries take their category from the section they sit in.

## Machine feeds, forums (wake the agent)

- **LINUX DO welfare** (CN): the freebie section of a large developer community, read via the Jina reader. Giveaways, credit drops and trial announcements surface here early.
- **V2EX promotions** (CN): promotions board RSS. Mixed quality; relays, carpools and resales are common and fail the filter.
- **GeekNews** (KR): Korean developer news. Government support calls, AI subsidy announcements and startup credit programs surface here in Korean before they are picked up in English.

## Machine feeds, firehose (never wake alone)

- **NodeSeek** (CN, hosting community): mostly marketplace buying and selling. Useful context on wake, useless as a trigger.
- **Appinn, ghxi, iPlaySoft** (CN software blogs): software deals and license giveaways, read on wake.

## Agent-checked pages, government programs

These do not change by the hour; an agent reads them on a slow rhythm (weekly, or when a feed hints a new call opened). They are where the largest free allocations live.

- **Korea, NIPA AI Voucher (MSIT)**: vouchers up to KRW 200M for SMEs and mid-sized firms adopting AI solutions, government covering up to 80 percent of project cost. Annual cycle, announced around Feb to Mar, applied through NIPA together with a registered supplier. Sibling tracks worth watching: AX One-Stop Voucher (AI + cloud + data in one voucher), Data Voucher, and K-Cloud GPU support programs.
- **Korea, K-Startup portal**: the single registration point for Korean government startup programs. The K-Startup Grand Challenge is explicitly open to foreign teams.
- **Korea, Bizinfo**: cross-ministry aggregator of Korean support-program announcements.
- **India, IndiaAI Mission**: the compute pillar subsidizes GPU access for startups and researchers through empanelled providers.
- **Japan, J-Startup (METI)**: selected startups receive preferential support; a signal source for Japanese program openings.
- **EU, EuroHPC JU**: access calls for European supercomputers, including AI Factories allocations for startups and SMEs.
- **Singapore, AI Singapore**: 100 Experiments co-funding and related national programs.

Eligibility warning: most government programs require a local company, a local team, or a local partner. The agent reports them with the eligibility stated plainly; whether the owner can use a program is the owner's call, never assumed.

## Agent-checked pages, gated startup programs (reference)

- **AWS Activate**, **Google Cloud for Startups**, **Microsoft for Startups**: large credit programs gated behind applications and card verification. Listed so the agent can answer "what about X" accurately, and clearly marked gated so they are never reported as open freebies to an owner who cannot pass the wall.
- **GitHub Student Developer Pack**: a big bundle for verified students; partner offers rotate, so it earns a periodic page check.

## Social hunting grounds (agent leg)

- **X hunter accounts** (17 in `sources.json`): individuals who habitually post free tiers, credits and giveaways, mostly from the Chinese freebie scene. One account is flagged gray (bait in the past): strictest filter. X offers no free machine feed for these; reading them needs the paid API, public search, or the owner's logged-in session with explicit permission.
- **Vietnamese VPS Facebook groups** (5 in `sources.json`): providers drop public first-come-first-served codes here. A verified case: an InterData 11.11 giveaway (3 free VPS codes) posted in one of these groups was gone within a day. Latency is the whole game, which is why the social leg runs on every wake.

## Adding a source

A good source is: public, updated by someone other than us, structured enough to diff (for feeds), and proven to surface real offers at least once. Add feeds to `sources.json` with a parser format that exists in `tracker.py`, set `wake` honestly (curated and deal-specific only), tag region and categories, and write the one-line note that tells the next agent what the source is and what usually fails the filter in it.
