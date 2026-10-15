# MCP 集成说明

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| 服务名称 | `mcd-mcp` |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权 | 请求头 `Authorization: Bearer ${MCD_MCP_TOKEN}` |
| 配置示例 | [`mcp-config.example.json`](mcp-config.example.json)，只含环境变量占位符 |
| 限流 | 每个 Token 每分钟 600 次，超出返回 429 |

Token 在 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 用手机号激活。本仓库不保存、不代理、不转发 Token。

## 2. 实际使用的 Tool

| Tool | 用途 | 关键字段 | 是否改数据 |
|---|---|---|---|
| `now-time-info` | 查询时间，作为 72 小时窗口的起点 | `datetime` | 否 |
| `query-nearby-stores` | 选门店 | `storeCode` / `storeName` | 否 |
| `query-store-coupons` | 本店本渠道可用券，止损计算的主数据 | `couponId` / `couponCode` / `tradeDateTime` / `products[].productCode` | 否 |
| `query-my-coupons` | 卡包张数对照 | 券名、有效期、渠道标签；常无 `couponId` | 否 |
| `query-my-account` | 积分余额和将过期数量 | `availablePoint` / `currentMouthExpirePoint` / `nextMouthExpirePoint` | 否 |
| `mall-points-products` | 看积分商城在售什么 | `spuId` / `point` / `price` / `downTime` / `status` | 否 |
| `calculate-price` | 单券核价，金额单位是分 | `productOriginalPrice` / `price` / `discount` | 否 |
| `create-order` | 用户明确确认后才创建订单 | 支付链接 | 是，默认不调用 |

`query-my-account` 的字段名里 `Mouth` 是接口实际拼写，归一化时同时接受 `Month`。

未默认调用的写操作：`auto-bind-coupons`、`mall-create-order`、`cancel-order`、`draw-lottery`、`party-order-create`、`delivery-create-address`。用户亲口要求领券时，才可以调用 `auto-bind-coupons`，并在调用前复述。

## 3. 调用顺序

```text
现在 / 门店 / 不要什么
        │
        ├─ now-time-info
        ├─ query-nearby-stores          用户选定 storeCode
        ├─ query-store-coupons          本店可用券
        ├─ query-my-coupons             只用于对照张数
        ├─ query-my-account             本月 / 下月将过期积分
        ├─ mall-points-products         仅展示，不兑换
        └─ calculate-price × N          每张 72 小时内的券单独试算
                │
        skills/mcd-benefit-stop/scripts/stop_loss.py
                │
        止损卡：72 小时金额、今晚一单、更早但挽回更少的券
                │
        用户确认之后，才允许 create-order
```

Agent 把工具结果整理成 `case` JSON，再运行：

```bash
python3 skills/mcd-benefit-stop/scripts/demo.py --case /tmp/mcd-case.json --out /tmp/mcd-card.html
```

`ingest()` 能直接收上述工具的 JSON。字段对照见 [`skills/mcd-benefit-stop/references/fields.md`](skills/mcd-benefit-stop/references/fields.md)。

## 4. 金额规则

- `calculate-price` 的 `price`、`discount`、`productOriginalPrice` 按分换算。
- 三个字段都在、且 `原价 - 应付 != 优惠` 时，这张券标为矛盾，不进入头条，也不进入推荐。
- 只有原价和应付、没有 `discount` 时，优惠按二者之差计算。
- 带小数的金额字符串无法判断是元还是分，直接放弃，不当成核价成功。
- 头条金额是 72 小时内、有券编号、核价成功的 `discount` 之和。
- 积分数量单独展示。没有到期日时，不乘任何汇率，不加入头条。

## 5. 业务价值

1. 把「快过期」收成一个已经核价的金额，而不是一张券名清单。
2. 本店可用券和卡包张数分开，避免把这家店用不了的券算进今晚的单。
3. 只推荐挽回最多的一单，同时指出更早到期但挽回更少的那张，方便用户自己取舍。
4. 积分缺少到期日时保持原样，不制造一个现金损失数字。

## 6. 核验

- [`fixtures/demo_case.json`](skills/mcd-benefit-stop/fixtures/demo_case.json) 是手工样例，顶部和页面都标了「样例数据」。
- 真实 Token 不在仓库里。`probe_mcp.py` 的输出目录 `fixtures/live/` 已被 `.gitignore` 排除。
- 复现：`python3 skills/mcd-benefit-stop/scripts/selftest.py`，期望 `29 passed, 0 failed`。
