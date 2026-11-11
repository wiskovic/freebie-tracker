# Categories

Every source in `sources.json` carries one or more categories, and every diff entry inherits one. Reports group finds by category so the owner can read only the slices they care about.

| Category | Covers | A real find looks like |
|---|---|---|
| `ai` | AI API credits, free tokens, model tiers, coding agents | A permanent free tier or a large no-card credit on an official provider |
| `gpu` | GPU compute, training/inference allocations | Free GPU hours from a platform or a government compute program |
| `cloud` | Cloud platforms, PaaS, serverless, app hosting | An ongoing free tier with no card, or startup credits the owner can actually unlock |
| `vps` | VPS, VMs, dedicated boxes, cloud desktops | A free or giveaway box claimable with email signup |
| `database` | Databases, storage, backups, queues | An ongoing free tier sized for real use |
| `dev-tools` | CI/CD, domains, monitoring, email, analytics, security tools | A free tier from the official vendor, not a reseller |
| `saas` | General software and productivity offers | License giveaways and lifetime offers from the vendor |
| `design` | Design, image, video and media tools | Free plans or giveaway licenses for creative work |
| `education` | Courses, student packs, learning platforms | Verified student bundles or genuinely free courses |
| `gov-programs` | Government subsidies, vouchers, compute access | An open call the owner (or their company) is eligible to apply to |
| `games` | Free games and entertainment | Kept for owners who want it; off by default in the original deployment |
| `other` | Everything else worth one look | Judged case by case |

Notes:

- A source's first category is the default for its entries; the markdown-list parser overrides it per entry from the section the entry sits in.
- `gov-programs` is deliberately separate from `cloud` and `gpu`: subsidy calls have application windows and eligibility paperwork, and burying them among product free tiers makes agents miss deadlines.
- Categories describe the offer, not the source's country. Region is its own field in `sources.json`.
