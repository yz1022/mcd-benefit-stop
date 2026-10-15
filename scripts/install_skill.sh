#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
SRC="$ROOT/skills/mcd-benefit-stop"
DEST="${HOME}/.workbuddy/skills/mcd-benefit-stop"
mkdir -p "$DEST/scripts" "$DEST/fixtures" "$DEST/references"
cp "$SRC/SKILL.md" "$DEST/SKILL.md"
cp "$SRC/scripts/"*.py "$DEST/scripts/"
cp "$SRC/fixtures/"*.json "$DEST/fixtures/"
cp "$SRC/references/"*.md "$DEST/references/"
echo "已安装到 $DEST"
echo "请重开一轮 WorkBuddy 对话后再使用。"
