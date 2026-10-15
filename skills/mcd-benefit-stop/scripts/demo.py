# -*- coding: utf-8 -*-
"""离线跑通止损卡。不需要 MCP Token。"""

import argparse
import json
from pathlib import Path

from stop_loss import build_report, render_html, render_text

ROOT_MARK = "CONTEST_DECLARATION.md"


def repo_root():
    for parent in Path(__file__).resolve().parents:
        if (parent / ROOT_MARK).exists():
            return parent
    return None


def main():
    parser = argparse.ArgumentParser(description="用样例数据生成麦麦权益止损卡")
    parser.add_argument("--case", default="", help="case JSON 路径，默认使用仓库样例")
    parser.add_argument("--out", default="", help="HTML 输出路径")
    args = parser.parse_args()
    if args.case:
        case_path = Path(args.case)
    else:
        case_path = Path(__file__).resolve().parent.parent / "fixtures" / "demo_case.json"
    case = json.loads(case_path.read_text(encoding="utf-8"))
    report = build_report(case)
    print(render_text(report))
    if args.out:
        out = Path(args.out)
    else:
        root = repo_root()
        out = (root / "docs" / "card-demo.html") if root else None
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_html(report), encoding="utf-8")
        print("\nHTML 已写入 " + str(out))


if __name__ == "__main__":
    main()
