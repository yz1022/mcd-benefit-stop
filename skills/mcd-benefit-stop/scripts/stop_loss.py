# -*- coding: utf-8 -*-
"""72 小时权益止损卡。

金额只来自 calculate-price 的「分」。积分没有到期日时不折进头条金额。
每一单只使用一张券。
"""

import json
import re
from datetime import datetime

_RANGE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})"
    r"\s*-\s*"
    r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})"
)
_DT = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}:\d{2}))?")


def parse_dt(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "null":
        return None
    matched = _DT.search(text)
    if not matched:
        return None
    clock = matched.group(2) or "00:00:00"
    return datetime.strptime(matched.group(1) + " " + clock, "%Y-%m-%d %H:%M:%S")


def parse_range_end(value):
    if value is None:
        return None
    matched = _RANGE.search(str(value))
    if not matched:
        return parse_dt(value)
    return parse_dt(matched.group(2))


def fen_of(value):
    """calculate-price 的金额是整数分。带小数的字符串无法判断单位，直接放弃。"""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text or not re.fullmatch(r"-?\d+", text):
            return None
        return int(text)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value == int(value):
        return int(value)
    return None


def yuan_text(fen):
    fen = int(fen)
    sign = "-" if fen < 0 else ""
    fen = abs(fen)
    return sign + str(fen // 100) + "." + ("%02d" % (fen % 100))


def hours_text(hours):
    if abs(hours - round(hours)) < 1e-6:
        return str(int(round(hours)))
    return "%.1f" % hours


def _unwrap(value):
    if isinstance(value, dict) and isinstance(value.get("content"), list):
        for block in value["content"]:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    return json.loads(block.get("text") or "")
                except (TypeError, ValueError):
                    return value
    return value


def _as_list(value):
    value = _unwrap(value)
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("coupons", "list", "data", "items", "records", "products"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _first(mapping, keys):
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _hours_between(now, end):
    return (end - now).total_seconds() / 3600.0


def _bucket(hours):
    if hours <= 0:
        return "expired"
    if hours <= 72:
        return "h72"
    if hours <= 168:
        return "d7"
    return "later"


def _price_block(raw):
    block = raw.get("calculatePrice") or raw.get("calculate_price") or {}
    if not isinstance(block, dict):
        block = {}
    payable = fen_of(block.get("price"))
    discount = fen_of(block.get("discount"))
    original = fen_of(_first(block, ("productOriginalPrice", "originalPrice", "product_original_price")))
    inconsistent = False
    if payable is not None and original is not None and discount is not None:
        if original - payable != discount:
            inconsistent = True
    elif discount is None and payable is not None and original is not None:
        discount = original - payable
    priced = payable is not None and discount is not None and discount >= 0 and not inconsistent
    return payable, discount, original, priced, inconsistent


def normalize_coupon(raw, now):
    end = parse_dt(_first(raw, ("valid_to", "validTo")))
    if end is None:
        end = parse_range_end(_first(raw, ("tradeDateTime", "trade_date_time")))
    products = raw.get("products") if isinstance(raw.get("products"), list) else []
    product = products[0] if products and isinstance(products[0], dict) else {}
    payable, discount, original, priced, inconsistent = _price_block(raw)
    hours = _hours_between(now, end) if end is not None else None
    title = _first(raw, ("title", "couponName", "name")) or "未命名优惠"
    product_name = _first(product, ("productName", "product_name", "name")) or title
    return {
        "coupon_id": _first(raw, ("couponId", "coupon_id")) or "",
        "coupon_code": _first(raw, ("couponCode", "coupon_code")) or "",
        "title": str(title),
        "product_name": str(product_name),
        "product_code": _first(product, ("productCode", "product_code", "code")) or "",
        "hours": hours,
        "bucket": "unknown" if hours is None else _bucket(hours),
        "payable_fen": payable,
        "discount_fen": discount,
        "original_fen": original,
        "priced": priced,
        "inconsistent": inconsistent,
    }


def ingest(payloads):
    """把若干 MCP 工具结果收成 build_report 能读的 case。"""
    payloads = payloads or {}
    now_payload = _unwrap(payloads.get("now-time-info")) or {}
    now = payloads.get("now") or _first(now_payload, ("datetime", "time", "now"))
    store_raw = _as_list(payloads.get("query-store-coupons") or payloads.get("store_coupons"))
    quotes = payloads.get("quotes") if isinstance(payloads.get("quotes"), dict) else {}
    store_coupons = []
    for raw in store_raw:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        coupon_id = _first(item, ("couponId", "coupon_id")) or ""
        if "calculatePrice" not in item and coupon_id in quotes:
            item["calculatePrice"] = quotes[coupon_id]
        store_coupons.append(item)
    account = _unwrap(payloads.get("query-my-account") or payloads.get("account") or {})
    if not isinstance(account, dict):
        account = {}
    mall = _as_list(payloads.get("mall-points-products") or payloads.get("mall_products"))
    return {
        "sample": bool(payloads.get("sample", False)),
        "now": now,
        "store_name": payloads.get("store_name") or "",
        "store_coupons": store_coupons,
        "my_coupons": _as_list(payloads.get("query-my-coupons") or payloads.get("my_coupons")),
        "account": account,
        "mall_products": mall,
    }


def _point_number(account, keys):
    value = _first(account, keys)
    if value is None or isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value) if isinstance(value, float) and value == int(value) else value
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"-?\d+", text):
            return int(text)
        if re.fullmatch(r"-?\d+\.\d+", text):
            number = float(text)
            return int(number) if number == int(number) else number
    return 0


def build_report(case, avoid=None):
    case = case or {}
    now = parse_dt(case.get("now"))
    if now is None:
        raise ValueError("case.now 缺失或无法解析")
    avoid = [str(word) for word in (avoid or []) if str(word).strip()]
    coupons = []
    for raw in case.get("store_coupons") or []:
        if isinstance(raw, dict):
            coupons.append(normalize_coupon(raw, now))

    headline = [c for c in coupons if c["bucket"] == "h72" and c["priced"] and c["coupon_id"]]
    later = [c for c in coupons if c["bucket"] == "d7" and c["priced"] and c["coupon_id"]]
    eligible = list(headline)
    if avoid:
        eligible = [
            c for c in eligible
            if not any(word in (c["title"] + c["product_name"]) for word in avoid)
        ]
    eligible.sort(key=lambda c: (-c["discount_fen"], c["hours"], c["coupon_id"]))
    suggestion = None
    sooner = None
    if eligible:
        best = eligible[0]
        suggestion = {
            "title": best["title"],
            "product_name": best["product_name"],
            "coupon_id": best["coupon_id"],
            "coupon_ids": [best["coupon_id"]],
            "payable_fen": best["payable_fen"],
            "recovered_fen": best["discount_fen"],
            "hours": best["hours"],
        }
        earlier = [
            c for c in eligible
            if c["coupon_id"] != best["coupon_id"]
            and c["hours"] < best["hours"]
            and c["discount_fen"] < best["discount_fen"]
        ]
        earlier.sort(key=lambda c: (c["hours"], c["coupon_id"]))
        if earlier:
            item = earlier[0]
            sooner = {
                "title": item["title"],
                "recovered_fen": item["discount_fen"],
                "hours": item["hours"],
            }

    account = case.get("account") if isinstance(case.get("account"), dict) else {}
    expire_date = None
    for key in ("expireDate", "expire_date", "expiringPointDate"):
        if account.get(key):
            expire_date = str(account[key])
            break
    mall = [item for item in (case.get("mall_products") or []) if isinstance(item, dict)]
    report = {
        "sample": bool(case.get("sample")),
        "now": now.strftime("%Y-%m-%d %H:%M:%S"),
        "store_name": case.get("store_name") or "当前门店",
        "headline_fen": sum(c["discount_fen"] for c in headline),
        "later_7d_fen": sum(c["discount_fen"] for c in later),
        "unpriced_count": sum(1 for c in coupons if c["bucket"] == "h72" and not c["priced"]),
        "unknown_expiry_count": sum(1 for c in coupons if c["bucket"] == "unknown"),
        "expired_count": sum(1 for c in coupons if c["bucket"] == "expired"),
        "inconsistent_count": sum(1 for c in coupons if c["inconsistent"]),
        "wallet_count": len(case.get("my_coupons") or []),
        "store_count": len(case.get("store_coupons") or []),
        "points": {
            "available": _point_number(account, ("availablePoint", "availablePoints", "available")),
            "this_month": _point_number(
                account,
                ("currentMouthExpirePoint", "currentMonthExpirePoint", "expiring_this_month"),
            ),
            "next_month": _point_number(
                account,
                ("nextMouthExpirePoint", "nextMonthExpirePoint", "expiring_next_month"),
            ),
            "expire_date": expire_date,
            "mall_count": len(mall),
        },
        "suggestion": suggestion,
        "sooner_smaller": sooner,
    }
    return report


def render_text(report):
    lines = []
    if report["sample"]:
        lines.append("样例数据，不是实时账户。")
    lines.append("麦麦权益止损官")
    lines.append("未来 72 小时将作废    ¥" + yuan_text(report["headline_fen"]))
    suggestion = report["suggestion"]
    if suggestion is None:
        lines.append("今晚建议              没有已核价、且会在 72 小时内作废的优惠")
    else:
        lines.append("今晚建议              " + suggestion["product_name"])
        lines.append("实付                  ¥" + yuan_text(suggestion["payable_fen"]))
        lines.append("这一单挽回            ¥" + yuan_text(suggestion["recovered_fen"]))
    sooner = report["sooner_smaller"]
    if sooner is not None:
        lines.append(
            "更早到期但挽回更少    %s，约 %s 小时后作废，挽回 ¥%s"
            % (sooner["title"], hours_text(sooner["hours"]), yuan_text(sooner["recovered_fen"]))
        )
    lines.append("7 天内更晚作废        ¥" + yuan_text(report["later_7d_fen"]))
    points = report["points"]
    if points["expire_date"]:
        point_line = "%s（到期日 %s，仍不折进上面的金额）" % (points["this_month"], points["expire_date"])
    else:
        point_line = "%s（接口没有到期日，不计入上面的金额）" % points["this_month"]
    lines.append("本月将过期积分        " + point_line)
    lines.append("卡包 %s 张，本店返回 %s 张" % (report["wallet_count"], report["store_count"]))
    if report["unpriced_count"]:
        lines.append("未核价                %s 张，不计入金额" % report["unpriced_count"])
    if report["unknown_expiry_count"]:
        lines.append("未标明有效期          %s 张，不计入金额" % report["unknown_expiry_count"])
    if report["expired_count"]:
        lines.append("已经过期              %s 张，不参与推荐" % report["expired_count"])
    lines.append("未确认不下单。价格来自 calculate-price。")
    return "\n".join(lines)


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(report):
    rows = []

    def add(label, value):
        rows.append(
            "<div class=\"row\"><span>%s</span><b>%s</b></div>" % (_esc(label), _esc(value))
        )

    suggestion = report["suggestion"]
    if suggestion is None:
        add("今晚建议", "没有已核价、且会在 72 小时内作废的优惠")
    else:
        add("今晚建议", suggestion["product_name"])
        add("实付", "¥" + yuan_text(suggestion["payable_fen"]))
        add("这一单挽回", "¥" + yuan_text(suggestion["recovered_fen"]))
    sooner = report["sooner_smaller"]
    if sooner is not None:
        add(
            "更早但挽回更少",
            "%s · %s 小时 · ¥%s" % (sooner["title"], hours_text(sooner["hours"]), yuan_text(sooner["recovered_fen"])),
        )
    add("7 天内更晚作废", "¥" + yuan_text(report["later_7d_fen"]))
    points = report["points"]
    if points["expire_date"]:
        point_value = "%s 分 · 到期日 %s" % (points["this_month"], points["expire_date"])
    else:
        point_value = "%s 分 · 无到期日" % points["this_month"]
    add("本月将过期积分", point_value)
    add("券的覆盖", "卡包 %s 张 / 本店 %s 张" % (report["wallet_count"], report["store_count"]))
    banner = ""
    if report["sample"]:
        banner = "<div class=\"banner\">样例数据，不是实时账户</div>"
    row_html = "".join(rows)
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>麦麦权益止损官</title>
<style>
  html, body { margin: 0; }
  body { box-sizing: border-box; width: 100%%; min-height: 100vh; padding: 16px; overflow-x: hidden;
    display: flex; align-items: center; justify-content: center;
    background: #f3eee6; color: #1d1a17;
    font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif; }
  .card { width: 100%%; max-width: 440px; min-width: 0; box-sizing: border-box; background: #fff; border-radius: 20px; overflow: hidden;
    box-shadow: 0 18px 50px rgba(70, 32, 16, 0.12); }
  .banner { background: #6f2d22; color: #fff; font-size: 13px; padding: 8px 18px; }
  .top { background: #c42318; color: #fff; padding: 22px 22px 18px; }
  .kicker { font-size: 14px; opacity: 0.92; }
  .yuan { font-size: 58px; line-height: 1; font-weight: 720; margin: 8px 0 6px; letter-spacing: -1px; }
  .store { font-size: 13px; opacity: 0.9; }
  .rows { padding: 6px 22px 8px; }
  .row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 13px 0;
    border-bottom: 1px solid #f1e7dc; font-size: 15px; }
  .row span { flex: 0 0 auto; }
  .row b { flex: 1 1 auto; min-width: 0; font-weight: 650; text-align: right; overflow-wrap: anywhere; }
  .note { padding: 12px 22px 20px; color: #6d645c; font-size: 12px; line-height: 1.55; }
  @media (max-width: 520px) {
    .row { flex-direction: column; gap: 4px; }
    .row b { text-align: left; }
  }
</style>
</head>
<body>
  <article class="card">
    %s
    <header class="top">
      <div class="kicker">未来 72 小时将作废</div>
      <div class="yuan">¥%s</div>
      <div class="store">%s · %s</div>
    </header>
    <div class="rows">%s</div>
    <p class="note">只统计已经核价、且能在本店使用的券。积分没有到期日，不折进这笔金额。未确认不下单。非麦当劳官方产品。</p>
  </article>
</body>
</html>
""" % (
        banner,
        yuan_text(report["headline_fen"]),
        _esc(report["store_name"]),
        _esc(report["now"]),
        row_html,
    )
