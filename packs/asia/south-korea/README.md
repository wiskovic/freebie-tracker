# South Korea country pack

South Korea's freebie surface is split between government AI and startup programmes and domestic cloud providers that advertise credits in Korean. Cloud credits often require payment-method registration, while DashCloud and Dothome offer card-free hosting with mobile-phone or identity verification. Grassroots finds concentrate in large IT forums such as Clien, where retail deal noise is heavy and free digital offers appear as occasional posts.

The pack is written for an agent that reads Korean and English: the government and hosting sources are Korean-language, while Upstage's live pricing page and some product names are English.

## Machine feeds

None. No stable Korean machine feed for freebies was found during the 2026-11-14 research round, so `feeds` is empty rather than padded with a news feed. The machine layer is the watched NIPA business-announcement listing instead:

- NIPA business announcements: https://www.nipa.kr/home/2-2

The listing is server-rendered and its latest items use relative `/home/2-2/<number>` hrefs; the watch pattern is anchored to those relative links. At check time the page exposed ten links and included current AI, GPU, and startup-support notices.

## Communities

- **클리앙 알뜰구매** (forum, daily): https://www.clien.net/service/board/jirum

Korea's largest general IT forum. Its 알뜰구매 board carries occasional limited-time free digital licenses, app giveaways, and provider promotions alongside heavy retail discount noise. The companion 유용한사이트 and 팁과강좌 boards also surface free tools, but the deal board is the highest-signal entry point. Direct datacenter requests return a block page, so read it through a reader or browser and verify every offer at the provider.

## Hunting grounds

- **NIPA business announcements** (listing, weekly, watch): https://www.nipa.kr/home/2-2

  Read the latest announcements, open any AI, GPU, cloud-voucher, or startup-support item, and verify eligibility and deadlines on the NIPA detail page and the operator's site. This is the pack's machine layer; the watch pattern matches relative `/home/2-2/<id>` links.

- **DashCloud Free plan** (site, monthly): https://dashcloud.kr/pricing

  The Free plan was lifetime free with no payment information, 256MB RAM, 1GB persistent storage, 10GB monthly traffic, and one project. Signup requires one-time mobile-phone verification, and paid plans were still pending general release, so recheck the open-beta terms before claiming.

- **Dothome free hosting** (site, monthly): https://www.dothome.co.kr/web/free/index.php

  Dothome's free hosting stays free only while an extension application is filed every 6 months; miss the renewal window and the account is blocked, data is held for 14 days, and recovery can carry fees (provider's free-hosting page, checked 2026-11-14). Read the signup agreement for current limits; real-name or identity verification may be requested.

- **NAVER Cloud new-signup credit** (site, monthly): https://www.ncloud.com/main/creditEvent

  The offer was 100,000 KRW in discount credit valid for three months, and registration of a payment method was required before applying. Credits cannot be used on already-free products or marketplace products.

- **KakaoCloud new-signup credit** (site, monthly): https://kakaocloud.com/business/support/new

  The new-signup programme offered 300,000 KRW in credit for applications within three months of signup. Payment-method registration and approval are part of the stated application steps; check the FAQ for exceptions before treating it as card-free.

- **Upstage document-agent API free runs** (site, monthly): https://www.upstage.ai/pricing/api

  Each agent included 10 free runs with no credit card required when checked. Usage beyond the allowance is metered, so confirm the current free-run terms for the product being used.

- **K-Startup open business announcements** (listing, weekly): https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do

  Read the open-announcement listing and open items through the site's go_view action. Detail links are JavaScript calls rather than hrefs, so this ground has no watch block. Verify eligibility, deadline, and application path on K-Startup and the programme operator's page.

## Vocabulary

Local search terms, grouped by role. The README must carry every term verbatim; the linter enforces this.

- **core**: `무료 호스팅`, `무료호스팅`, `무료 크레딧`, `무료 체험`, `평생 무료`, `무료 플랜`, `무료 서버`, `GPU 지원`, `AI 바우처`, `클라우드 바우처`, `스타트업 지원`
- **no_card_markers**: `결제 정보 없이`, `결제 정보 없음`, `no credit card required`
- **credit**: `무료 크레딧`, `할인 크레딧`, `크레딧 지원`, `100,000 원의 할인 크레딧`, `30만원 상당의 크레딧`
- **community_phrases**: `무료배포`, `정보공유`, `무료로 시작`, `0원`
- **umbrella**: `핫딜`, `할인`, `이벤트`, `쿠폰`, `공구`, `특가`
- **negative_markers**: `무료배송`, `쿠팡`

`무료배송` and `쿠팡` dominate Korean deal boards and are the clearest retail-noise markers. `핫딜`, `할인`, and `특가` are umbrella vocabulary: useful for finding limited-time offers, but too broad to treat as a freebie signal by themselves.

## Local patterns

- Cloud credits are the main domestic freebie shape: NAVER Cloud and KakaoCloud both advertised new-signup credits when checked on 2026-11-14, and both required payment-method registration.
- Card-free hosting exists but is identity-gated: DashCloud requires one-time mobile-phone verification for its lifetime Free plan, and Dothome may request real-name or identity verification at signup.
- Government support is application-based and Korean-language: NIPA and K-Startup publish AI, GPU, cloud-voucher, and startup programmes with eligibility rules that can require a Korean business or resident status.
- K-Startup detail links use `javascript:go_view(...)`, so its listing is readable but not watchable; NIPA's `/home/2-2` listing uses relative hrefs and is the pack's machine watch.
- Clien's 알뜰구매 board is the most accessible large IT forum for free digital offers, but retail discounts dominate. Direct access worked when re-checked on 2026-11-14; a browser or reader is the fallback if a block page appears.
- Search Naver first for Korean offers: Google and Bing returned stale or unrelated results during research, while Naver surfaced current provider and community pages.
- No stable Korean machine feed for freebies was found; the machine layer is the NIPA listing watch, checked 2026-11-14.

## Verification notes

- All provider and programme terms above were checked on 2026-11-14.
- NIPA's listing yielded ten current items at check time, including `2026년「첨단 GPU 활용 지원 사업」 베타서비스 참여자 모집 공모 안내 (산학연 지원)`.
- The two cloud-credit grounds are claimable but card-walled; they are included with that constraint stated openly rather than treated as no-card offers.
- DashCloud and Dothome are card-free but phone- or identity-gated. Check each signup flow before promising a claim.
- Clien's board was read through a reader during research; on re-check on 2026-11-14 it also answered direct requests, so treat a browser or reader as a fallback rather than a requirement.
- No checked-and-rejected list is carried here; see `GUESSES.md` for authoring choices and the reasons behind them.

## Run

```sh
python3 packs/lint_packs.py packs/asia/south-korea
python3 packs/pack_runner.py packs/asia/south-korea --seed
python3 packs/pack_runner.py packs/asia/south-korea
python3 -m unittest discover -s tests -v
```
