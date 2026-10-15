# -*- coding: utf-8 -*-
"""只读探测麦当劳 MCP 的字段。没有 Token 时直接退出。

探测结果写到 fixtures/live/，该目录已在 .gitignore 中。
不要把 Token、手机号、地址提交进仓库。
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

URL = os.environ.get("MCD_MCP_URL", "https://mcp.mcd.cn")
TOKEN = os.environ.get("MCD_MCP_TOKEN", "").strip()
OUT = Path(__file__).resolve().parent.parent / "fixtures" / "live"
SECRET_KEY = re.compile(r"token|authorization|phone|mobile|address|account|user.?id|trace", re.I)
READ_ONLY = ("now-time-info", "query-my-account", "query-my-coupons", "mall-points-products")


def redact(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if SECRET_KEY.search(str(key)):
                cleaned[key] = "[已脱敏]"
            else:
                cleaned[key] = redact(item)
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and len(value) > 24 and TOKEN and TOKEN in value:
        return "[已脱敏]"
    return value


def post(payload, session_id):
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + TOKEN,
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    request = urllib.request.Request(URL, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, response.headers.get("Mcp-Session-Id"), body


def main():
    if not TOKEN:
        print("未设置 MCD_MCP_TOKEN，跳过实时探测。")
        print("样例数据在 skills/mcd-benefit-stop/fixtures/demo_case.json")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    status, session_id, body = post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "mcd-benefit-stop", "version": "0.1.0"},
            },
        },
        None,
    )
    (OUT / "initialize.json").write_text(
        json.dumps({"status": status, "body": redact(body[:4000])}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if session_id:
        post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id)
    for index, name in enumerate(READ_ONLY, start=2):
        arguments = {"page": "1", "pageSize": "20"} if name == "query-my-coupons" else {}
        try:
            status, _, body = post(
                {"jsonrpc": "2.0", "id": index, "method": "tools/call", "params": {"name": name, "arguments": arguments}},
                session_id,
            )
            payload = {"status": status, "body": body[:20000]}
        except Exception as exc:
            payload = {"error": exc.__class__.__name__}
        (OUT / (name + ".json")).write_text(
            json.dumps(redact(payload), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(name + " -> fixtures/live/" + name + ".json")
    print("探测只调用了只读工具，没有领券、下单或兑换。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
