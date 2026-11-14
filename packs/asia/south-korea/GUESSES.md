> Provenance: this file was written by the outside agent that authored this pack in the 2026-11-14 step-6 recipe test, and is kept as the pack's authoring record. The pack was then verified claim by claim by the repository supervisor; two claims the verification contradicted (Dothome's renewal condition and Clien's access) were corrected in pack.json and README.md. The original text below is unchanged.

# Authoring guesses: South Korea

Research and authoring were done on 2026-11-14. This file records the points where the schema and repository documentation did not settle the choice, what was chosen, and why. It is documentation only; the runner and linter do not read it.

- **Language list includes English.** `country.languages` is `["ko", "en"]`. Most sources are Korean, but Upstage's live pricing page and several product names are English, and the schema says to list every language the agent must read to search and verify the pack's sources.

- **Empty feeds, NIPA as the machine watch.** `feeds` is `[]` and the machine layer is the NIPA `/home/2-2` listing. The schema permits an empty feed block when no stable machine feed exists, but it does not say which listing to watch. NIPA was chosen over K-Startup because NIPA's listing exposes stable relative numeric hrefs and yields current programme notices, while K-Startup's detail links are `javascript:go_view(...)` calls.

- **Anchored relative watch pattern.** The NIPA `link_pattern` is `^/home/2-2/\d+`. The schema says the pattern is matched against each href, and NIPA emits relative hrefs, so an absolute-URL pattern would match nothing. If NIPA changes to absolute hrefs, the pattern will need an update.

- **Clien admitted through reader access.** The community is Clien's 알뜰구매 board. Direct datacenter requests return a block page, but the board was live and readable through a reader on 2026-11-14, and the board showed current free-digital-offer posts. The schema requires live verification but does not say whether indirect reader access counts; it was treated as verified with the access constraint written into `focus` and `local_patterns`.

- **One community URL despite multiple useful boards.** Clien's 알뜰구매 is the single `url`, although `유용한사이트` and `팁과강좌` also produce relevant finds. The schema allows only one URL per community entry, so the highest-signal deal board was chosen and the other boards are named in `focus`. A future schema could allow multiple board URLs.

- **Cadence values are judgment calls.** NIPA and K-Startup are `weekly`; the provider offer pages are `monthly`; Clien is `daily`. The schema fixes the vocabulary but gives no guidance for government listings or slow-moving pricing pages. These values reflect the observed update rhythm and the risk of missing a short application window.

- **Card-walled credits are included.** NAVER Cloud and KakaoCloud are free-credit offers that require payment-method registration. The schema does not exclude card-walled offers, and the pack is a hunting kit rather than a no-card-only list, so both were included with the card requirement stated in `how` and `local_patterns`. If the intended user must never register a payment method, these two grounds should be removed.

- **DashCloud's open beta is included.** DashCloud says the Free plan is lifetime free while paid plans are still pending release. It was included because the free plan is live and claimable, but the beta status is written into `how` because limits and terms may change.

- **English no-card marker kept.** `no_card_markers` includes `no credit card required` alongside the Korean `결제 정보 없이` and `결제 정보 없음`. The schema asks for local phrasing from live provider pages; Upstage's live pricing page uses this English phrase for the Korean market, so it was kept rather than translated.

- **A brand name is used as a negative marker.** `negative_markers` includes `쿠팡` alongside `무료배송`. The schema asks for phrasings that mark retail noise, and Korean deal boards are dominated by Coupang and free-delivery posts. A brand marker is broader than a phrase and may need revisiting if it suppresses legitimate Coupang-hosted offers.

- **K-Startup has no watch block.** The listing HTML is server-rendered, but its detail links are `javascript:go_view(...)` rather than hrefs. The schema says a JavaScript-rendered listing gets no watch block and its `how` must explain why, so no watch was added even though the listing itself returns HTML.
