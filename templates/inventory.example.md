# Owner inventory (example)

Copy this file somewhere your agent can read it, rename it to
`inventory.md`, and keep it current. The agent dedupes every candidate
against this list before reporting: already owned is not a find.

| Name | Category | Status | Notes |
|---|---|---|---|
| Example Cloud | cloud | claimed | Free tier, 1 project, claimed 2026-01-15 |
| Example GPU platform | gpu | active | 30 GPU hours per week, quota refreshes Fridays |
| Example DB | database | claimed | Empty project, nothing stored yet |
| Example program | gov-programs | waitlist | Position 176, no action until a slot opens |
| Example trial | ai | expires 2027-10-05 | Auto-charges at trial end unless cancelled |

Status vocabulary: `claimed` (account exists, unused), `active` (in use),
`waitlist`, `expires YYYY-MM-DD` (needs a decision before that date),
`rejected` (owner said no; never report it again as new).
