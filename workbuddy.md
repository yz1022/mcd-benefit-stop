# WorkBuddy 开发对话上下文

这个文件还是占位，不能拿去领 3000 积分。

官方要的是「使用 WorkBuddy 开发时的对话上下文」。已报名项目里，这份文件是按轮次整理的开发记录，不是客户端聊天记录的原文，也不是只跑一次「不要下单」的使用演示。

用以后兑积分的那个 WorkBuddy 账号，打开本仓库，完成下面一轮真实任务后，用该轮的原话覆盖本文件。Cursor 里做过的事不要写成 WorkBuddy 的轮次。

## 要写进文件的结构

```text
# WorkBuddy 开发对话上下文

> 一句话：本文件记录用腾讯 WorkBuddy 处理本仓库的对话，供专项奖励核验。

## 项目信息

| 项 | 内容 |
|---|---|
| 项目名称 | 麦麦权益止损官 / mcd-benefit-stop |
| 开发工具 | 腾讯 WorkBuddy |
| MCP | https://mcp.mcd.cn |
| 日期 | 当天日期 |
| 工作目录 | 本机实际路径 |

## 对话轮次

每一轮都写用户原话，以及 WorkBuddy 实际做了什么。没有发生的轮次不要补。

### 第 1 轮 · 读仓库并跑通样例
### 第 2 轮 · 只读核对 MCP 字段
### 第 3 轮 · 生成止损卡

## 关键决定

| 决定 | 选择 | 理由 |
|---|---|---|
| 金额 | 只认 calculate-price 的整数分 | 模型口算的价格不进卡 |
| 积分 | 只展示本月、下月数量 | 接口没有到期日，不折成现金 |
| 一单 | 只用一张券 | 接口没有给出叠加规则 |

## 结论

写清这次 WorkBuddy 实际完成了哪些事。不要写「全程由 WorkBuddy 从零开发」。
```

## 在 WorkBuddy 里贴的任务

```text
工作目录就是当前仓库。按下面三轮做，每轮都先回复你实际调用了什么、跑了什么命令、看到了什么，再进入下一轮。不要领券，不要下单，不要兑换。

第 1 轮：读 skills/mcd-benefit-stop/SKILL.md 和 README.md。运行 python3 skills/mcd-benefit-stop/scripts/selftest.py 和 python3 skills/mcd-benefit-stop/scripts/demo.py。把通过条数和样例卡上的总额记下来。

第 2 轮：只读调用麦当劳 MCP 的 now-time-info、query-my-account、query-my-coupons、query-nearby-stores。核对积分是否在 structuredContent.data 里、是不是字符串，券列表是否在 data.coupons，总张数是否是 data.totalCount。不要把返回原文写进仓库。

第 3 轮：选定一家店后，用 query-store-coupons 取本店券，对 72 小时内有券号的券逐张 calculate-price，再运行 skills/mcd-benefit-stop/scripts/stop_loss.py 生成止损卡。

三轮都做完后，用这一轮的真实记录覆盖仓库根目录 workbuddy.md。结构用文件里「要写进文件的结构」：项目信息、按轮次的用户原话和实际动作、关键决定、结论。没有做过的步骤不要写。不要写入 Token、手机号、accountId、traceId。
```
