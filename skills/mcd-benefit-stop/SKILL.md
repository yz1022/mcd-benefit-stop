---
name: mcd-benefit-stop
description: 麦麦权益止损官。用户想知道麦当劳优惠、券或积分还有多久作废、72 小时内会损失多少、今晚哪一单能挽回最多时使用。通过麦当劳 MCP 读取本店可用券和积分，并用 calculate-price 的核价结果生成止损卡。默认不下单。
---

# 麦麦权益止损官

## 解决什么问题

卡包里的券和本店今晚能用的券不是同一份名单。积分接口给得出「本月将过期多少」，给不出具体日期。模型如果自己把这些数加成一个现金损失，很容易报错。

分工：

- MCP 取本店券、卡包张数、积分和核价。
- `scripts/stop_loss.py` 计算 72 小时金额，并选出挽回最多的一单。
- 你负责把止损卡讲成人话。未确认前不调用 `create-order`。

不要自己口算价格，也不要把积分乘一个汇率后加进头条金额。

## 何时使用

- 「72 小时内我有多少麦当劳优惠会作废？」
- 「今晚哪一单能把快到期的券挽回最多？不要下单。」
- 「本月将过期的积分有多少？没有日期就别折成现金。」
- 「到店吃，不要甜品，只看这家店能用的券。」

## 工作流

### 1. 先问缺的信息

就餐方式和门店必须有。用户没说「不要什么」就留空，不要为了填表多问一轮。预算不是必填项。

### 2. 只读取数

按这个顺序调用：

1. `now-time-info`
2. `query-nearby-stores`，让用户选定门店
3. `query-store-coupons`，这是能核价的券
4. `query-my-coupons`，只用来数卡包有多少张
5. `query-my-account`
6. `mall-points-products`，只展示，不兑换
7. 对 72 小时内、且有 `couponId` 的每张券单独调用 `calculate-price`

`calculate-price` 的金额是分。`query-my-account` 里本月将过期积分的字段名是 `currentMouthExpirePoint`，下月是 `nextMouthExpirePoint`。

不要调用 `auto-bind-coupons`、`mall-create-order`、`draw-lottery`、`party-order-create`、`delivery-create-address`。用户明确说「先把能领的券领了」时，先复述再调用 `auto-bind-coupons`，然后重新查本店券。

### 3. 交给脚本

把工具结果写成 JSON，字段见 [`references/fields.md`](references/fields.md)。然后运行：

```bash
python3 scripts/demo.py --case /tmp/mcd-case.json --out /tmp/mcd-card.html
```

脚本和 `SKILL.md` 同级放在 `scripts/`。离线样例：

```bash
python3 scripts/demo.py
python3 scripts/selftest.py
```

用户说「不要甜品」这类限制时，把关键词传给 `build_report(case, avoid=["甜品"])`。

### 4. 怎么讲

用脚本输出，不要改金额。至少说清四件事：

- 未来 72 小时将作废的已核价优惠
- 今晚建议的那一单、实付、挽回
- 如果有更早到期但挽回更少的券，单独说出来
- 本月将过期积分。没有到期日时，明确说不计入上面的金额

卡包张数和本店返回张数不一样时，要说出来。

### 5. 下单

只有用户明确选定方案并同意下单时，才调用 `create-order`。下单前再跑一次 `calculate-price`，把实付、门店和餐品复述一遍。价格变了就停下来，不要沿用旧卡。

## 硬性约束

- 没核价的券可以计数，不能进金额。
- 没有有效期就写「未标明有效期」，不要猜剩余时间。
- 核价三个字段互相矛盾时，丢弃这张券。
- 一单只用一张券。
- 不提供医疗或营养建议。
- 餐品、价格和供应状态以麦当劳官方渠道实时结果为准。

## 资源

- [`scripts/stop_loss.py`](scripts/stop_loss.py)
- [`scripts/selftest.py`](scripts/selftest.py)
- [`scripts/demo.py`](scripts/demo.py)
- [`fixtures/demo_case.json`](fixtures/demo_case.json)
- [`references/fields.md`](references/fields.md)
