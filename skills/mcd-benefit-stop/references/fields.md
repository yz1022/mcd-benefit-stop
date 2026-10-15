# 字段对照

`build_report` 读取的 case，以及 `ingest()` 能接的 MCP 结果。

## case

| 字段 | 来源 | 说明 |
|---|---|---|
| `now` | `now-time-info` 的 `structuredContent.datetime` 或 `data.formatted` | 按北京时间理解，毫秒会被丢掉 |
| `store_name` | `query-nearby-stores` | 只用于展示 |
| `store_coupons[]` | `query-store-coupons` | 本店可用券 |
| `store_coupons[].couponId` | 同上 | 没有编号的券不进入金额 |
| `store_coupons[].tradeDateTime` | 同上 | `开始-结束`，取结束时间 |
| `store_coupons[].products[].productCode` | 同上 | 传给 `calculate-price` |
| `store_coupons[].calculatePrice.price` | `calculate-price` | 应付，单位分 |
| `store_coupons[].calculatePrice.discount` | `calculate-price` | 优惠，单位分 |
| `store_coupons[].calculatePrice.productOriginalPrice` | `calculate-price` | 原价，单位分 |
| `my_coupons[]` | `query-my-coupons` 的 `data.coupons` | 只计张数。有 `totalCount` 时用总张数，不用当前页长度 |
| `account.currentMouthExpirePoint` | `query-my-account` 的 `data` | 本月将过期积分，实测是字符串，也可以是小数。也接受 `currentMonthExpirePoint` |
| `account.nextMouthExpirePoint` | `query-my-account` 的 `data` | 下月将过期积分。没有到期日，不折现 |
| `account.availablePoint` | `query-my-account` 的 `data` | 可用积分 |
| `mall_products[]` | `mall-points-products` 的 `data` 数组 | `point`、`price` 是字符串。`downTime` 是商品下架时间，不是积分到期日 |

## 不做什么

- 不把 `mall-points-products.downTime` 当成用户积分的到期日。
- 不把 `query-my-coupons` 里没有 `couponId` 的券拿去核价。
- 不把带小数点的金额字符串当成「分」。
