# Agent guide

How an AI agent operates freebie-tracker for its owner. This is the judgment half of the system; `tracker.py` is only the eyes.

## The loop

1. On schedule (4 to 6 hours works), run `python3 tracker.py`.
2. Read `state/last-run.json`. If `wake_new_count + wake_changed_count` is 0, do nothing. Silence is a valid result.
3. Otherwise read `state/last-diff.json` and triage the new and changed entries by category.
4. For each promising candidate, verify at the **official provider page** (follow the entry link out to the provider, not the aggregator). Aggregator listings are leads, never proof.
5. Apply the safety filter below.
6. Dedupe against the owner's inventory (see `templates/inventory.example.md`). Already owned, already claimed, already rejected: drop silently.
7. Run the social leg (below) once per wake.
8. Report briefly to the owner: per category, only what passed, with the official link, the claim window if there is one, and an honest verdict. If nothing passed, say so in one line, including what was rejected and why, briefly.

## Verification checklist (per candidate)

- What exactly is free: a permanent tier, a dated trial, a one-time credit, or a discount in costume?
- Signup requirements: email or phone only? Credit card? Real-name or KYC verification? A registered company? A student status?
- Region: is the owner eligible where they actually are? Any geo-gate on signup?
- Expiry: claim deadline, and does the benefit survive renewal or die at the first cycle?
- Catch: cliff billing if a limit is exceeded? Auto-charge at trial end? Idle deletion?

If a fact cannot be established from the official source, report it as unknown rather than guessing. A candidate with an unknown signup wall is reported as unverified, not as a find.

## The safety filter

Reject outright:

- **Card walls** the owner cannot or will not pass (this alone kills most big-cloud "free" offers).
- **Real-name / KYC walls** the owner cannot pass, including offers that require a local ID in a country the owner has no presence in.
- **Account markets**: resold accounts, carpools, shared subscriptions, relayed or pooled API credits, "team" seats sold by strangers.
- **Bait**: free claims that funnel into paid courses, credential harvesting, or downloads from file-sharing drives.
- **Expired** offers and giveaways whose window already closed.
- **Paid discounts** presented as freebies. A discount can still be worth reporting in a dedicated discount sweep, clearly labeled as paid.

Flag, but do not auto-reject:

- Time-limited trials with real value and no card (label the end date).
- Programs that need a registered business, when the owner has one or a community entity (label the requirement).
- Gray-adjacent sources whose individual offer verifies cleanly at the official page (verify harder, report the provenance honestly).

## The social leg

`sources.json` lists social hunting grounds (type `social`): X accounts that habitually post freebies and Facebook community groups where providers drop public codes. There is no honest machine feed for these without the paid X API or a logged-in session, so the agent reads them on wake:

- Prefer the owner's logged-in session only when the owner has explicitly allowed that, and weigh the account risk (automation on a personal account can trigger challenges or locks). Otherwise use public search.
- Public giveaway codes are first-come-first-served and usually gone within hours. Report fast, with the code and the official claim link, and the honest chance assessment.
- A social post is the weakest form of lead. Verify at the provider before reporting anything as claimable.

## Reporting style

- One message, grouped by category, short lines: name, what is free, requirements, deadline, official link, verdict.
- Rejections get one shared line at most ("23 new posts, all marketplace resale and relay credits").
- Never inflate: a trial is a trial, a gated program is gated, an unverified lead is unverified.
- Never claim, sign up, connect an account, enter a code, install anything, or schedule anything on the owner's behalf without the owner's explicit instruction naming that action. The radar finds; the owner decides.

## Owner inventory

Keep an inventory of what the owner already holds (accounts, claimed tiers, boxes, credits) in the format of `templates/inventory.example.md`, somewhere the agent can read before reporting. Half of good filtering is knowing what is already on the shelf: the same free tier announced three times is one find, not three.
