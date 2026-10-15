# -*- coding: utf-8 -*-
"""止损卡自测。改完逻辑必跑。"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from stop_loss import (
    build_report,
    fen_of,
    ingest,
    parse_range_end,
    render_html,
    render_text,
    yuan_text,
)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "demo_case.json"
PASSED = []
FAILED = []


def check(name, condition):
    if condition:
        PASSED.append(name)
        print("PASS  " + name)
    else:
        FAILED.append(name)
        print("FAIL  " + name)


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def main():
    check("分到元", yuan_text(5420) == "54.20" and yuan_text(610) == "6.10" and yuan_text(0) == "0.00")
    check("拒绝带小数的金额", fen_of("14.0") is None and fen_of(1400) == 1400)
    end = parse_range_end("2026-10-05 10:30:00-2026-10-09 23:59:59")
    check("有效期区间取结束时间", end == datetime(2026, 10, 9, 23, 59, 59))

    case = load()
    report = build_report(case)
    again = build_report(case)
    check("同一输入同一输出", report == again)
    check("72 小时头条是 54.20 元", report["headline_fen"] == 5420)
    check("积分和商城售价不进头条", report["points"]["this_month"] == 420 and report["points"]["mall_count"] == 1)
    check("积分没有到期日", report["points"]["expire_date"] is None)
    suggestion = report["suggestion"]
    check(
        "今晚只选挽回最多的一单",
        suggestion["coupon_ids"] == ["DEMO-BOARD"]
        and suggestion["payable_fen"] == 2500
        and suggestion["recovered_fen"] == 2300
        and suggestion["product_name"] == "板烧鸡腿堡套餐",
    )
    check("报价等于核价而不是原价减一个猜测", suggestion["payable_fen"] == 2500)
    sooner = report["sooner_smaller"]
    check(
        "更早但挽回更少的券被单独标出",
        sooner["title"] == "中可乐兑换券" and sooner["recovered_fen"] == 900 and sooner["hours"] == 12,
    )
    check("7 天内更晚的券分开统计", report["later_7d_fen"] == 400)
    check("未核价不进金额", report["unpriced_count"] == 1)
    check("没有有效期不进金额", report["unknown_expiry_count"] == 1)
    check("已过期不参与推荐", report["expired_count"] == 1 and "DEMO-EXPIRED" not in suggestion["coupon_ids"])
    check("卡包和本店张数分开", report["wallet_count"] == 11 and report["store_count"] == 9)

    text = render_text(report)
    check("文本包含头条和实付", "¥54.20" in text and "¥25.00" in text and "¥23.00" in text)
    check("文本声明样例和下单边界", "样例数据" in text and "未确认不下单" in text)
    html = render_html(report)
    check("页面包含同样的金额", "¥54.20" in html and "¥25.00" in html and "样例数据" in html)

    avoided = build_report(case, avoid=["板烧"])
    check(
        "避开关键词后改选下一张",
        avoided["suggestion"]["coupon_id"] == "DEMO-COLA" and avoided["suggestion"]["recovered_fen"] == 900,
    )

    empty = {
        "sample": False,
        "now": "2026-10-15 14:00:00",
        "store_name": "示例门店",
        "store_coupons": [],
        "my_coupons": [],
        "account": {"currentMonthExpirePoint": 15},
    }
    empty_report = build_report(empty)
    check("没有券时不编造建议", empty_report["suggestion"] is None and empty_report["headline_fen"] == 0)
    check("Month 拼写也能读到本月积分", empty_report["points"]["this_month"] == 15)
    check("空结果如实说明", "没有已核价" in render_text(empty_report))

    now = datetime(2026, 10, 15, 14, 0, 0)
    edge = {
        "now": now.strftime("%Y-%m-%d %H:%M:%S"),
        "store_coupons": [
            {
                "title": "刚好 72 小时",
                "couponId": "EDGE-72",
                "tradeDateTime": "2026-10-01 00:00:00-" + (now + timedelta(hours=72)).strftime("%Y-%m-%d %H:%M:%S"),
                "products": [{"productCode": "E1", "productName": "刚好 72 小时"}],
                "calculatePrice": {"productOriginalPrice": 1000, "price": 700, "discount": 300},
            },
            {
                "title": "超过 72 小时",
                "couponId": "EDGE-OVER",
                "valid_to": (now + timedelta(hours=72, seconds=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "products": [{"productCode": "E2", "productName": "超过 72 小时"}],
                "calculatePrice": {"productOriginalPrice": 1000, "price": 100, "discount": 900},
            },
        ],
        "my_coupons": [],
        "account": {},
    }
    edge_report = build_report(edge)
    check("72 小时整计入头条，超出 1 秒不算", edge_report["headline_fen"] == 300 and edge_report["later_7d_fen"] == 900)

    bad = {
        "now": "2026-10-15 14:00:00",
        "store_coupons": [
            {
                "title": "金额对不上",
                "couponId": "BAD",
                "valid_to": "2026-10-16 14:00:00",
                "products": [{"productCode": "B", "productName": "金额对不上"}],
                "calculatePrice": {"productOriginalPrice": 2000, "price": 1500, "discount": 100},
            },
            {
                "title": "没有券编号",
                "valid_to": "2026-10-16 14:00:00",
                "products": [{"productCode": "N", "productName": "没有券编号"}],
                "calculatePrice": {"productOriginalPrice": 2000, "price": 1000, "discount": 1000},
            },
        ],
        "account": {},
    }
    bad_report = build_report(bad)
    check("核价自相矛盾或缺少券编号时不计入", bad_report["headline_fen"] == 0 and bad_report["suggestion"] is None)
    check("矛盾张数被记下来", bad_report["inconsistent_count"] == 1)

    derived = {
        "now": "2026-10-15 14:00:00",
        "store_coupons": [
            {
                "title": "只给了原价和应付",
                "couponId": "DERIVED",
                "valid_to": "2026-10-16 14:00:00",
                "products": [{"productCode": "D", "productName": "只给了原价和应付"}],
                "calculatePrice": {"productOriginalPrice": 3000, "price": 1200},
            }
        ],
        "account": {"expireDate": "2026-10-31", "currentMouthExpirePoint": 10},
    }
    derived_report = build_report(derived)
    check(
        "缺少 discount 时用原价减应付",
        derived_report["headline_fen"] == 1800 and derived_report["suggestion"]["payable_fen"] == 1200,
    )
    check("有到期日也不把积分折成现金", "不折进" in render_text(derived_report) and derived_report["headline_fen"] == 1800)

    raw = ingest({
        "sample": True,
        "now-time-info": {"datetime": "2026-10-15 14:00:00"},
        "query-store-coupons": {
            "coupons": [
                {
                    "title": "原始券",
                    "couponId": "RAW-1",
                    "tradeDateTime": "2026-10-01 00:00:00-2026-10-16 14:00:00",
                    "products": [{"productCode": "R", "productName": "原始券"}],
                }
            ]
        },
        "quotes": {"RAW-1": {"productOriginalPrice": 1100, "price": 800, "discount": 300}},
        "query-my-account": {"availablePoint": 3, "currentMouthExpirePoint": 2, "nextMouthExpirePoint": 1},
        "query-my-coupons": {"list": [{"title": "原始券"}, {"title": "只在卡包"}]},
        "mall-points-products": {"products": [{"spuId": "M", "point": 9999, "price": 50000}]},
    })
    raw_report = build_report(raw)
    check(
        "MCP 原始结果能归一",
        raw_report["headline_fen"] == 300
        and raw_report["points"]["this_month"] == 2
        and raw_report["wallet_count"] == 2
        and raw_report["suggestion"]["coupon_id"] == "RAW-1",
    )
    check("两张券不会叠进同一单", len(raw_report["suggestion"]["coupon_ids"]) == 1)

    print("")
    print("%s passed, %s failed" % (len(PASSED), len(FAILED)))
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
