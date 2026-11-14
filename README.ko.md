<div align="center">

# 📡 freebie-tracker

**AI 에이전트를 위한 제로 토큰 무료 혜택 레이더.
전 세계 무료 티어 목록과 딜 커뮤니티를 감시하고, 변경 사항을 비교하며,
실제로 받을 가치가 있는 혜택이 있을 때만 에이전트를 깨웁니다.**

[![CI](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml)
[![last-commit](https://img.shields.io/github/last-commit/wiskovic/freebie-tracker)](https://github.com/wiskovic/freebie-tracker/commits/main)
[![repo-size](https://img.shields.io/github/repo-size/wiskovic/freebie-tracker)](https://github.com/wiskovic/freebie-tracker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

*실행 비용은 0입니다: 토큰도, API 키도, LLM 호출도 없습니다.
에이전트는 변경 사항이 가치가 있을 때만 주의를 씁니다.
제로 토큰은 풀러에만 해당합니다; 연결한 에이전트는 혜택을 검증하고
보고할 때 자체 토큰을 사용합니다.*

[English](README.md) | [简体中文](README.zh-CN.md) | 한국어 | [Bahasa Indonesia](README.id.md)

</div>

---

기계 쪽은 일부러 단순하고 싸게 만들었습니다(Python 표준 라이브러리만 사용, API 키 없음, LLM 호출 없음). 판단은 에이전트의 몫입니다. 에이전트는 후보를 제공업체 공식 페이지에서 검증하고, 소유자의 안전 필터를 적용한 뒤, 실제로 받을 가치가 있는 것만 보고합니다.

## 왜 만들었나

무료 티어, AI 크레딧, GPU 보조금, 나눔 코드는 중국의 선별 목록, 한국의 스타트업 커뮤니티, 서구의 개발자 목록, 그리고 몇 시간 만에 사라지는 소셜 게시물에 흩어져 있습니다. 사람이 전부 지켜볼 수는 없지만, 감시 자체의 비용이 거의 0이고 변경 사항이 있을 때만 주의를 쓴다면 에이전트는 할 수 있습니다.

이 프로젝트는 실제로 운영 중인 구성을 일반화한 것입니다. 중국의 선별 목록(lanmao, baipiaoji, jidan), 딜 포럼(LINUX DO, V2EX, NodeSeek), Facebook과 X의 헌터 게시물을 가로지르고, 대부분의 트래커가 놓치는 층, 즉 대형 AI 보조 및 지원 프로그램(한국 AI 바우처, 인도 IndiaAI 컴퓨팅, EU EuroHPC 등)까지 다룹니다. 가장 큰 무료 할당량이 실제로 있는 곳이 바로 그 층입니다.

## 작동 방식

```
sources.json          레지스트리: 피드, 프로그램 페이지, 소셜 사냥터
     |
tracker.py            모든 피드를 가져와 스냅샷을 만들고 지난 실행과 비교
     |
state/last-diff.json  카테고리별로 표시된 신규 / 변경 / 삭제 항목
     |
에이전트 (웨이크 게이트)  깨울 수 있는 소스가 바뀔 때만 실행; 후보를
                      공식 페이지에서 검증하고, 안전 필터를 적용하고,
                      소유자의 인벤토리와 중복을 제거한 뒤,
                      카테고리별로 짧게 보고
```

핵심 장치는 웨이크 규율입니다. 파이어호스 피드(시장 잡담, 일반 소프트웨어 블로그)는 차분만 계산해 저장할 뿐, **절대 혼자서 에이전트를 깨우지 않습니다**. 선별 목록과 딜 전용 포럼만 깨울 수 있습니다. 실제 운영에서는 에이전트 비용이 거의 0에 가까우면서도 중요한 것을 놓치지 않습니다.

## 빠른 시작

```bash
git clone https://github.com/wiskovic/freebie-tracker
cd freebie-tracker
python3 tracker.py --seed   # 첫 실행: 기준 스냅샷 작성
python3 tracker.py          # 이후 실행: 가져와서 비교
cat state/last-diff.json    # 무엇이 바뀌었는지 확인
```

에이전트 플랫폼이 제공하는 스케줄러(cron, 웹훅 폴러, systemd 타이머 등)로 돌리면 됩니다. 4~6시간 간격이 적당합니다. 공개 나눔 코드는 몇 시간 만에 소진될 수 있으므로, `docs/agent-guide.md`의 소셜 레그가 중요합니다.

## 출력 형태

실행하면 요약 한 줄이 출력되고 전체 차분이 `state/last-diff.json`에 기록됩니다.

```json
{"sources_ok": 18, "sources_failed": [], "items_per_source": {"baipiaoji": 131, "lanmao": 341, "jidan": 40, "linuxdo": 25, "v2ex": 50, "lowendtalk": 100, "free-for-dev": 1379, "...": "..."}, "new_count": 22, "changed_count": 1, "removed_count": 22, "wake_new_count": 2, "wake_changed_count": 1}
```

에이전트는 `wake_new_count + wake_changed_count`가 0보다 클 때만 깨어나 검증하고, 필터링하고, 보고합니다. 완성된 보고서 예시는 `examples/report-example.md`에 있습니다.

## 카테고리

모든 소스와 항목에는 카테고리 태그가 붙습니다: `ai`, `gpu`, `cloud`, `vps`, `database`, `dev-tools`, `saas`, `design`, `education`, `gov-programs`, `games`, `other`. 보고서는 카테고리별로 묶이므로, 소유자가 새 VM 혜택만 궁금하다면 그 그룹만 보면 됩니다. 자세한 내용은 `docs/categories.md`를 참고하세요.

## 소스 한눈에 보기

| 층 | 예시 | 방식 |
|---|---|---|
| 선별 목록 (중국) | baipiaoji, lanmao, jidan | 기계 피드 |
| 딜 포럼 | LINUX DO 복리 섹션, V2EX 홍보, LowEndTalk 혜택, LowEndSpirit 무료 혜택 | 기계 피드 |
| 파이어호스 | NodeSeek, Appinn, ghxi, iPlaySoft, Slickdeals, OzBargain, Giveaway of the Day, LowEndBox | 기계 피드, 수동 |
| 개발자 목록 (글로벌) | free-for.dev, free-ai-apis | 기계 피드 |
| 개발자 뉴스 (한국) | GeekNews | 기계 피드 |
| 대형 지원 프로그램 | 한국 AI 바우처(NIPA), K-Startup, IndiaAI, EuroHPC, J-Startup, AI Singapore | 에이전트 페이지 확인 |
| 게이트형 스타트업 프로그램 | AWS Activate, Google Cloud for Startups, Microsoft for Startups, GitHub 학생 팩 | 에이전트 페이지 확인, 게이트 있음 |
| 소셜 사냥터 | X 헌터 계정, 무료 티어와 나눔을 공유하는 틈새 커뮤니티 그룹(Facebook, Discord, 포럼) | 에이전트 레그, 웨이크 시 |

주석이 달린 전체 레지스트리는 `sources.json`, 사람이 읽기 좋은 카탈로그는 `docs/sources.md`에 있습니다.

## 안전 필터 (요약)

목록에 올라온 것은 **단서일 뿐, 전리품이 아닙니다**. 에이전트는 무엇이든 "받을 수 있다"고 보고하기 전에 제공업체 공식 출처에서 검증해야 하며, 다음을 거부합니다.

- 소유자가 제공할 수 없거나 제공하려 하지 않는 신용카드가 필요한 혜택
- 소유자가 통과할 수 없는 실명 인증 또는 KYC 뒤에 있는 혜택
- 계정 재판매, 카풀, 공유 또는 중계 API 크레딧, 토큰 미끼
- 이미 만료된 혜택, 무료로 위장한 유료 할인
- 소유자에게 자격이 없는 지역 제한 혜택

필터는 소유자의 상황으로 매개변수화됩니다(`templates/profile.example.json` 참고). 모든 소유자가 같은 벽에 막힌다고 가정하지 않습니다. 전체 필터와 에이전트 운영 매뉴얼은 `docs/agent-guide.md`에 있습니다.

## 국가 팩

어떤 무료 혜택은 국가마다 다릅니다. 현지 제공자, 현지 커뮤니티, 그리고 현지 언어로 "무료"를 뜻하는 단어가 다르기 때문입니다. 국가 팩은 한 국가의 선별된 사냥 도구 모음을 기계가 읽을 수 있는 형태로 만든 것으로, `packs/<대륙>/<국가>/`에 있습니다. `pack.json`(현지 검색어, 레지스트리와 같은 형태의 피드, 팔로우할 현지 커뮤니티, 에이전트가 직접 도는 사냥터)과 짧은 사람용 README로 구성됩니다. 어떤 에이전트든 JSON을 직접 불러오거나 공유 러너를 실행할 수 있습니다. 러너는 팩의 피드를 당겨 메인 레지스트리와 똑같은 방식으로 차분을 냅니다:

```
python3 packs/pack_runner.py packs/europe/france
```

현재 세 개의 팩이 있습니다. 프랑스(`packs/europe/france/`), 사우디아라비아(`packs/asia/saudi-arabia/`), 한국(`packs/asia/south-korea/`)입니다. 다른 나라용 팩을 만드는 법을 포함한 팩 형식은 `packs/SCHEMA.md`에 문서화되어 있습니다.

## 디렉터리 구조

```
tracker.py              풀러 (표준 라이브러리만 사용)
sources.json            소스 레지스트리 (피드, 페이지, 소셜)
packs/                  국가 팩, 나라별 선별 도구 모음
  pack_runner.py        공유 팩 러너
  SCHEMA.md             팩 저자를 위한 팩 형식
  europe/france/        프랑스 팩 (pack.json + README.md)
  asia/saudi-arabia/    사우디아라비아 팩 (pack.json + README.md)
  asia/south-korea/     한국 팩 (pack.json + README.md)
docs/agent-guide.md     에이전트 운영법: 루프, 필터, 보고
docs/categories.md      카테고리 분류 체계
docs/sources.md         지역별 주석이 달린 소스 카탈로그
examples/               에이전트 보고서 예시
templates/              소유자 인벤토리와 프로필 템플릿
state/                  런타임 스냅샷과 차분 (git 제외)
```

## 운영 상태

기준 배포 환경은 바로 이 코드를 실행합니다. 에이전트가 이 저장소의 체크아웃에서 6시간마다 폴링하고, 스냅샷과 소유자 인벤토리는 git 밖의 비공개 배포 폴더에 보관하며, 발견한 내용을 소유자에게 보고합니다. 이곳의 변경 사항은 배포 전에 실제 스냅샷으로 테스트합니다.

## 면책 조항

이 도구가 찾아낸 것은 무엇이든, 에이전트(또는 소유자)가 제공업체 공식 페이지에서 확인할 때까지 검증되지 않은 단서에 불과합니다. 혜택은 예고 없이 바뀌거나, 만료되거나, 지역 제한이 걸릴 수 있습니다. 제공업체 본인 사이트가 아닌 곳에서는 자격 증명, 코드, 결제 정보를 절대 입력하지 말고, 그런 입력은 소유자의 명시적 지시가 있을 때만 하세요.

## 라이선스

MIT. `LICENSE`를 참고하세요.
