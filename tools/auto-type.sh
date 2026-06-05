#!/bin/bash
# auto-type.sh - 快捷自动输入工具
# 用法: auto-type.sh <窗口名> <间隔秒数> <内容> [次数]

WINDOW="${1:?用法: $0 <窗口名> <间隔秒数> <内容> [次数]}"
INTERVAL="${2:?请指定间隔秒数}"
CONTENT="${3:?请指定输入内容}"
COUNT="${4:-0}"  # 0=无限循环

WID=$(xdotool search --name "$WINDOW" 2>/dev/null | tail -1)
if [ -z "$WID" ]; then
    echo "❌ 未找到窗口: $WINDOW"
    exit 1
fi

echo "🎯 目标窗口: $WID ($WINDOW)"
echo "⏱️  间隔: ${INTERVAL}秒"
echo "📝 内容: $CONTENT"
echo "🔢 次数: $([ "$COUNT" -eq 0 ] && echo "无限" || echo "$COUNT")"
echo "---"
echo "按 Ctrl+C 停止"

i=0
while true; do
    i=$((i + 1))

    # 判断是按键还是文本
    if [[ "$CONTENT" =~ ^(Return|Enter|Tab|Escape|BackSpace|Delete|space|Up|Down|Left|Right|ctrl\+|alt\+|shift\+|F[0-9]+)$ ]]; then
        xdotool key --window "$WID" "$CONTENT" 2>/dev/null
    else
        xdotool type --window "$WID" --delay 50 "$CONTENT" 2>/dev/null
        xdotool key --window "$WID" Return 2>/dev/null
    fi

    echo "[$(date +%H:%M:%S)] #$i 已发送"

    [ "$COUNT" -gt 0 ] && [ "$i" -ge "$COUNT" ] && break

    sleep "$INTERVAL"
done

echo "✅ 完成，共发送 $i 次"
