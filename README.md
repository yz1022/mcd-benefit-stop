# 麦麦权益止损官

未来 72 小时里，已经核过价、并且这家店能用的优惠，一共会作废多少。今晚哪一单挽回最多。

麦当劳程序员创意开发大赛参赛作品，由参赛者独立开发，非麦当劳官方产品。Python 3.9+，只用标准库。

![止损卡](docs/card-desktop.png)

手机宽度下的同一张卡：[`docs/card-mobile.png`](docs/card-mobile.png)。页面源文件是 [`docs/card-demo.html`](docs/card-demo.html)，标了「样例数据」。

## 它回答的问题

| 问题 | 做法 |
|---|---|
| 这一单怎么点最便宜 | 组合优化：菜单、券、凑单放在一起算总价 |
| 未来 72 小时，已核价的优惠会作废多少；今晚哪一单挽回最多 | 本项目：只加总本店、72 小时内、`calculate-price` 核过的优惠，并单独标出更早到期但挽回更少的那张 |

积分只展示本月、下月将过期的数量。接口没有到期日时，不乘汇率，不进上面的金额。

## 目标用户

- 卡包里有券，但不知道这家店今晚实际能用哪几张的人
- 被「即将到期」推着下单，又想先看到实付和挽回金额的人
- 想知道本月有多少积分将过期，同时不想把积分折成一个没依据的现金数的人

## 样例里的 ¥54.20

下面这张卡来自 `python3 skills/mcd-benefit-stop/scripts/demo.py`，时间固定在 `2026-10-15 14:00:00`。数字是手工样例，不是某个真实账户。

```text
样例数据，不是实时账户。
麦麦权益止损官
未来 72 小时将作废    ¥54.20
今晚建议              板烧鸡腿堡套餐
实付                  ¥25.00
这一单挽回            ¥23.00
更早到期但挽回更少    中可乐兑换券，约 12 小时后作废，挽回 ¥9.00
7 天内更晚作废        ¥4.00
本月将过期积分        420（接口没有到期日，不计入上面的金额）
下月将过期积分        80（同样不计入上面的金额）
卡包 11 张，本店返回 9 张
未核价                1 张，不计入金额
未标明有效期          1 张，不计入金额
已经过期              1 张，不参与推荐
未确认不下单。价格来自 calculate-price。
```

¥54.20 是下面五张券的核价优惠之和。同一单只用一张券，所以今晚建议取挽回最多的板烧，中可乐虽然更早到期，但只单独标出来。

| 样例券 | 有效期截止 | 核价优惠 | 归到哪一行 |
|---|---|---:|---|
| 板烧鸡腿堡套餐 | 10-17 06:00 | ¥23.00 | 72 小时总额，也是今晚建议。实付 ¥25.00 |
| 中可乐兑换券 | 10-16 02:00 | ¥9.00 | 72 小时总额，并标成「更早到期但挽回更少」 |
| 猪柳蛋套餐 | 10-17 21:00 | ¥8.10 | 72 小时总额 |
| 中薯条 | 10-18 02:00 | ¥8.00 | 72 小时总额 |
| 麦旋风 | 10-16 08:00 | ¥6.10 | 72 小时总额 |
| 周日甜筒 | 10-21 14:00 | ¥4.00 | 7 天内更晚作废，不进 ¥54.20 |
| 未核价甜品 | 72 小时内 | 无核价 | 只计数 |
| 有效期缺失券 | 无 | 有核价也不用 | 只计数 |
| 已过期小食 | 已过截止 | 不参与 | 只计数 |

23.00 + 9.00 + 8.10 + 8.00 + 6.10 = 54.20。卡包 11 张里有 2 张本店列表没有返回，所以本店是 9 张。

## 它做什么

取数用麦当劳 MCP，加总用脚本，讲解用对话。金额以 `calculate-price` 返回的整数「分」为准。

1. `query-store-coupons` 取本店、本渠道真正能用的券，含券编号和有效期。
2. `query-my-coupons` 只做张数对照。卡包里的券不一定带券编号，也不一定这家店能用。
3. 每张候选券单独调用 `calculate-price`。
4. 把 72 小时内、已经核价、优惠大于 0 的金额加总，选出挽回金额最大的一单。
5. `query-my-account` 展示本月、下月将过期积分。字段在 `structuredContent.data` 里，值是字符串。

默认不领券、不兑换、不下单。用户明确确认之后，才可以调用 `create-order`。

调用顺序、字段和金额规则写在 [`MCP_INTEGRATION.md`](MCP_INTEGRATION.md)。

## 安装

### 1. 准备 Token

在 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 用手机号登录并激活 Token。Token 只放在本机环境变量或客户端配置里，不要提交进仓库，也不要贴到 Issue、群聊或截图里。

### 2. 接上 MCP

WorkBuddy 里按 [`mcp-config.example.json`](mcp-config.example.json) 添加连接，把 `${MCD_MCP_TOKEN}` 换成你自己的 Token 后再保存。替换后的文件不要提交。

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer ${MCD_MCP_TOKEN}"
      }
    }
  }
}
```

### 3. 安装 Skill

```bash
git clone https://github.com/yz1022/mcd-benefit-stop.git
cd mcd-benefit-stop
bash scripts/install_skill.sh
```

脚本把 `skills/mcd-benefit-stop` 复制到 `~/.workbuddy/skills/mcd-benefit-stop`。Windows 把同一目录复制到 `%USERPROFILE%\.workbuddy\skills\mcd-benefit-stop`，并保持 `SKILL.md` 和 `scripts/` 同级。

装好后重开一轮对话，直接说：

> 我账户里 72 小时内会作废多少麦当劳优惠？这家店今晚哪一单挽回最多？不要下单。

## 不连 MCP 也能看结果

```bash
python3 skills/mcd-benefit-stop/scripts/demo.py
python3 skills/mcd-benefit-stop/scripts/selftest.py
```

`demo.py` 读 [`fixtures/demo_case.json`](skills/mcd-benefit-stop/fixtures/demo_case.json)，写出上面的文字和 `docs/card-demo.html`。`selftest.py` 当前是 37 项断言。

有 Token 之后可以只读探测字段，结果写到被 git 忽略的 `fixtures/live/`：

```bash
export MCD_MCP_TOKEN="你的 Token"
python3 skills/mcd-benefit-stop/scripts/probe_mcp.py
```

这条命令不会领券、下单或兑换。

## 使用示例

样例回复里的金额沿用上一节的手工数据，用来说明卡片长什么样。连上 MCP 之后，数字换成你这家店当时的核价结果。

**1. 先看会作废多少**

> 未来 72 小时我有多少麦当劳优惠会作废？今晚哪一单挽回最多？不要下单。

回复先给总额和今晚一单的实付、挽回，再单列更早但挽回更少的券。未确认前不下单。

**2. 排除不想吃的**

> 到店吃，不要甜品。只看这家店真正能用的券。

甜品字样的券不进入今晚建议。72 小时总额仍按本店已核价的券计算。

**3. 积分不要折现**

> 本月将过期的积分有多少？没有到期日就不要折成现金。

只报 `currentMouthExpirePoint` 和 `nextMouthExpirePoint`。接口没给到期日时，回复里写明不计入金额。`Mouth` 是接口字段的实际拼写。

## 目录

```text
.
├── README.md
├── CONTEST_DECLARATION.md          参赛声明，官方原文
├── MCP_INTEGRATION.md              Server、Tool、调用顺序、金额规则
├── mcp-config.example.json         只有环境变量占位符
├── workbuddy.md
├── LICENSE
├── docs/
│   ├── card-demo.html              样例止损卡
│   ├── card-desktop.png
│   ├── card-mobile.png
│   └── ISSUE.md                    报名 Issue 的标题和正文
└── skills/mcd-benefit-stop/
    ├── SKILL.md                    对话时加载的技能说明
    ├── scripts/
    │   ├── stop_loss.py            分桶、加总、选出一单、渲染卡片
    │   ├── demo.py
    │   ├── selftest.py
    │   └── probe_mcp.py            只读探测，输出不进 git
    ├── fixtures/demo_case.json
    └── references/fields.md
```

## 边界

- 同一单只用一张券。接口没有给出叠加规则时，不把几张券的优惠加在同一单上。
- 核价结果自相矛盾，或券没有编号，这张券不进入金额，也不进入推荐。
- 核价后优惠为 0 的券不进入 72 小时总额。
- 没有有效期的券只计数，不编一个剩余天数。
- 已经过期的券不参与推荐。
- 积分商城的 `downTime` 是商品下架时间，不是用户积分的到期日。
- 价格是查询那一刻的核价结果。餐品、价格和供应以麦当劳官方渠道的实时结果为准。

## 参赛材料

| 官方要求 | 本仓库 |
|---|---|
| 项目介绍、安装、使用示例、目标用户 | 本文件 |
| 参赛声明，原文不改 | [`CONTEST_DECLARATION.md`](CONTEST_DECLARATION.md) |
| MCP Server、Tool、调用流程、业务价值 | [`MCP_INTEGRATION.md`](MCP_INTEGRATION.md) |
| 脱敏配置 | [`mcp-config.example.json`](mcp-config.example.json) |
| 源代码 | [`skills/mcd-benefit-stop/scripts/stop_loss.py`](skills/mcd-benefit-stop/scripts/stop_loss.py) |
| WorkBuddy 开发对话上下文 | [`workbuddy.md`](workbuddy.md) |

## 许可

[MIT](LICENSE)。
