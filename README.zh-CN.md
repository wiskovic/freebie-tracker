<div align="center">

# 📡 freebie-tracker

**为 AI 智能体而建的零 token 免费资源雷达。
监视全球免费额度清单与优惠社区，计算变化差异，
只在发现真正值得领取的东西时才唤醒你的智能体。**

[![CI](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml)
[![last-commit](https://img.shields.io/github/last-commit/wiskovic/freebie-tracker)](https://github.com/wiskovic/freebie-tracker/commits/main)
[![repo-size](https://img.shields.io/github/repo-size/wiskovic/freebie-tracker)](https://github.com/wiskovic/freebie-tracker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

*运行成本为零：无 token、无 API 密钥、不调用大模型。
智能体只在差异值得时才花注意力。
零 token 仅指拉取器本身；你接入的智能体在核实和报告发现时，
仍会消耗它自己的 token。*

[English](README.md) | 简体中文 | [한국어](README.ko.md) | [Bahasa Indonesia](README.id.md)

</div>

---

机器部分刻意做得又笨又便宜（纯 Python 标准库，无需 API 密钥，不调用大模型），判断部分交给智能体。智能体随后到服务商官方页面核实候选条目，套用主人的安全过滤条件，只报告真正值得领取的东西。

## 为什么

免费额度、AI 额度、GPU 补贴和赠送码，散落在中国精选清单、韩国创业社区、西方开发者列表，以及几小时内就消失的社交帖子里。人盯不过来，智能体可以，前提是"盯"本身几乎不花钱，只在差异非空时才花注意力。

本项目把一套正在生产环境运行的配置通用化：横跨中国精选清单（lanmao、baipiaoji、jidan）、优惠论坛（LINUX DO、V2EX、NodeSeek）和 Facebook、X 上的猎手帖子，并补上多数追踪器漏掉的一层，大型 AI 补贴与扶持计划（韩国 AI Voucher、印度 IndiaAI 算力、欧盟 EuroHPC 等），那里才是最大额免费资源的所在地。

## 工作原理

```
sources.json          注册表：订阅源、计划页面、社交猎场
     |
tracker.py            拉取每个订阅源，存快照，与上次运行做差异比较
     |
state/last-diff.json  新增 / 变更 / 消失的条目，按类别标记
     |
智能体（唤醒门控）     只在可唤醒来源有变化时运行；逐条到官方
                      页面核实，套用安全过滤，与主人的库存
                      去重，最后按类别简要报告
```

核心技巧是唤醒纪律：信息洪流类来源（市场闲聊、综合软件博客）只做差异比较并存档，**绝不单独唤醒智能体**。只有精选清单和优惠专版论坛可以唤醒。生产环境中，这让智能体的成本接近于零，同时不漏掉真正重要的东西。

## 快速开始

```bash
git clone https://github.com/wiskovic/freebie-tracker
cd freebie-tracker
python3 tracker.py --seed   # 首次运行：写下基线快照
python3 tracker.py          # 之后运行：拉取并比较差异
cat state/last-diff.json    # 看看变了什么
```

用你的智能体平台自带的调度方式即可（cron、webhook 轮询、systemd 定时器）。4 到 6 小时一轮效果很好；公开赠送码可能几小时内失效，所以 `docs/agent-guide.md` 里的社交腿很重要。

## 输出长什么样

每次运行打印一行摘要，并把完整差异写进 `state/last-diff.json`：

```json
{"sources_ok": 18, "sources_failed": [], "items_per_source": {"baipiaoji": 131, "lanmao": 341, "jidan": 40, "linuxdo": 25, "v2ex": 50, "lowendtalk": 100, "free-for-dev": 1379, "...": "..."}, "new_count": 22, "changed_count": 1, "removed_count": 22, "wake_new_count": 2, "wake_changed_count": 1}
```

智能体只因为 `wake_new_count + wake_changed_count` 大于零才醒来，然后核实、过滤、报告。成品报告示例见 `examples/report-example.md`。

## 分类

每个来源和条目都打上类别标签：`ai`、`gpu`、`cloud`、`vps`、`database`、`dev-tools`、`saas`、`design`、`education`、`gov-programs`、`games`、`other`。报告按类别分组，主人只关心新出的虚拟机优惠时，就只看那一组。详见 `docs/categories.md`。

## 来源一览

| 层 | 例子 | 方式 |
|---|---|---|
| 精选清单（中国） | baipiaoji、lanmao、jidan | 机器订阅源 |
| 优惠论坛 | LINUX DO 福利版、V2EX 推广、LowEndTalk 优惠版、LowEndSpirit 免费版 | 机器订阅源 |
| 信息洪流 | NodeSeek、Appinn、果核剥壳、异次元软件、Slickdeals、OzBargain、Giveaway of the Day、LowEndBox | 机器订阅源，被动 |
| 开发者列表（全球） | free-for.dev、free-ai-apis | 机器订阅源 |
| 开发者新闻（韩国） | GeekNews | 机器订阅源 |
| 大型扶持计划 | 韩国 AI Voucher（NIPA）、K-Startup、IndiaAI、EuroHPC、J-Startup、AI Singapore | 智能体查页面 |
| 门槛型创业计划 | AWS Activate、Google Cloud for Startups、Microsoft for Startups、GitHub 学生包 | 智能体查页面，有门槛 |
| 社交猎场 | X 猎手账号、分享免费额度与赠送的小众社群（Facebook、Discord、论坛等） | 智能体腿，唤醒时查 |

完整注册表（含备注）在 `sources.json`，人类可读目录在 `docs/sources.md`。

## 安全过滤（概要）

清单上的条目只是**线索，不是战利品**。智能体在把任何东西报告为"可领取"之前，必须到服务商官方来源核实，并拒绝：

- 需要主人无法或不愿提供的信用卡的优惠
- 卡在主人过不了的实名或 KYC 验证后面的优惠
- 账号转卖、拼车、共享或中转的 API 额度、代币诱饵
- 已过期，或把付费折扣包装成免费的东西
- 主人不符合资格的区域限定优惠

过滤条件按主人的情况参数化（见 `templates/profile.example.json`），不假设每个主人面对同样的墙。完整过滤规则和智能体操作手册在 `docs/agent-guide.md`。

## 国家包

有些免费资源是按国家区分的：本地服务商、本地社区，以及当地语言里表示"免费"的词。国家包是一个国家经过筛选的狩猎工具包，机器可读，位于 `packs/<大洲>/<国家>/`：一个 `pack.json`（本地搜索词、与注册表同构的订阅源、值得关注的本地社区、智能体亲自巡猎的场所）加上一份简短的人类可读 README。任何智能体都可以直接加载这份 JSON，或者运行共享运行器；运行器会拉取包内的订阅源，并像主注册表一样计算差异：

```
python3 packs/pack_runner.py packs/europe/france
```

目前已有两个国家包：法国（`packs/europe/france/`）和沙特阿拉伯（`packs/asia/saudi-arabia/`）。包的格式，包括如何为另一个国家编写国家包，记录在 `packs/SCHEMA.md`。

## 目录结构

```
tracker.py              拉取器（仅标准库）
sources.json            来源注册表（订阅源、页面、社交）
packs/                  国家包，每个国家一套筛选后的工具包
  pack_runner.py        共享的包运行器
  SCHEMA.md             包格式说明，给包作者
  europe/france/        法国包（pack.json + README.md）
docs/agent-guide.md     智能体如何运行这套系统：循环、过滤、报告
docs/categories.md      分类体系
docs/sources.md         来源目录与各地区备注
examples/               一份智能体报告示例
templates/              主人库存与档案模板
state/                  运行时快照与差异（不进 git）
```

## 生产状态

参考部署运行的就是这份代码：智能体每 6 小时从本仓库的检出目录轮询一次，快照和主人库存放在 git 之外的私有部署目录里，发现成果直接报告给主人。这里的每次改动，发布前都先在真实快照上测过。

## 免责声明

本工具浮出的任何东西，在智能体（或主人）到服务商官方页面核实之前，都只是未经证实的线索。优惠会毫无通知地变化、过期或区域锁定。不要在服务商自己的网站之外的任何地方输入凭据、兑换码或支付信息，且只在主人明确指示时才这么做。

## 许可证

MIT，见 `LICENSE`。
