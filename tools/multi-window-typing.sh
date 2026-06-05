#!/bin/bash
# multi-window-typing.sh
# 轻量级多窗口自动键盘输入脚本
# 依赖: xdotool (已预装于Kali)

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    echo -e "${CYAN}用法:${NC}"
    echo "  $0 list                     - 列出所有可见窗口"
    echo "  $0 type <窗口名> <文本>      - 向指定窗口输入文本"
    echo "  $0 key <窗口名> <按键>       - 向指定窗口发送按键"
    echo "  $0 batch <配置文件>          - 批量执行多窗口输入"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 list"
    echo "  $0 type 'kali@kali' 'ls -la'"
    echo "  $0 key 'Firefox' 'ctrl+t'"
    echo "  $0 batch tasks.txt"
}

# 列出所有可见窗口
list_windows() {
    echo -e "${GREEN}=== 可见窗口列表 ===${NC}"
    printf "%-12s %-30s %s\n" "WINDOW_ID" "CLASS" "TITLE"
    printf "%-12s %-30s %s\n" "--------" "-----" "-----"
    xdotool search --onlyvisible --name "" 2>/dev/null | while read -r wid; do
        class=$(xdotool getwindowclassname "$wid" 2>/dev/null || echo "N/A")
        title=$(xdotool getwindowname "$wid" 2>/dev/null || echo "N/A")
        printf "%-12s %-30s %s\n" "$wid" "${class:0:30}" "${title:0:50}"
    done
}

# 向指定窗口输入文本
type_to_window() {
    local window_name="$1"
    local text="$2"
    local delay="${3:-50}"  # 默认每个字符间隔50ms

    local wid
    wid=$(xdotool search --onlyvisible --name "$window_name" 2>/dev/null | head -1)

    if [ -z "$wid" ]; then
        echo -e "${RED}错误: 未找到匹配 '${window_name}' 的窗口${NC}"
        return 1
    fi

    echo -e "${GREEN}找到窗口 ID: $wid${NC}"
    xdotool windowactivate --sync "$wid"
    sleep 0.3
    xdotool type --window "$wid" --delay "$delay" "$text"
    xdotool key --window "$wid" Return
    echo -e "${GREEN}✓ 已发送文本到窗口${NC}"
}

# 向指定窗口发送按键
send_key_to_window() {
    local window_name="$1"
    local key="$2"

    local wid
    wid=$(xdotool search --onlyvisible --name "$window_name" 2>/dev/null | head -1)

    if [ -z "$wid" ]; then
        echo -e "${RED}错误: 未找到匹配 '${window_name}' 的窗口${NC}"
        return 1
    fi

    echo -e "${GREEN}找到窗口 ID: $wid${NC}"
    xdotool windowactivate --sync "$wid"
    sleep 0.2
    xdotool key --window "$wid" "$key"
    echo -e "${GREEN}✓ 已发送按键 '${key}'${NC}"
}

# 批量执行任务 (配置文件格式: 每行一个任务，字段用 | 分隔)
# 格式: 窗口名|命令|类型(type/key)|延迟(ms)
batch_execute() {
    local config_file="$1"

    if [ ! -f "$config_file" ]; then
        echo -e "${RED}错误: 配置文件 '${config_file}' 不存在${NC}"
        return 1
    fi

    echo -e "${CYAN}=== 批量执行模式 ===${NC}"
    local count=0
    while IFS='|' read -r window_name content action delay; do
        # 跳过注释和空行
        [[ "$window_name" =~ ^#.*$ || -z "$window_name" ]] && continue

        count=$((count + 1))
        echo -e "\n${YELLOW}[任务 $count] 目标: $window_name | 动作: $action${NC}"

        case "$action" in
            type)
                type_to_window "$window_name" "$content" "${delay:-50}"
                ;;
            key)
                send_key_to_window "$window_name" "$content"
                ;;
            *)
                echo -e "${RED}未知动作: $action${NC}"
                ;;
        esac

        sleep 0.5  # 任务间隔
    done < "$config_file"

    echo -e "\n${GREEN}=== 批量执行完成，共 $count 个任务 ===${NC}"
}

# 主逻辑
case "${1:-help}" in
    list)
        list_windows
        ;;
    type)
        [ $# -lt 3 ] && { echo -e "${RED}参数不足${NC}"; usage; exit 1; }
        type_to_window "$2" "$3" "${4:-50}"
        ;;
    key)
        [ $# -lt 3 ] && { echo -e "${RED}参数不足${NC}"; usage; exit 1; }
        send_key_to_window "$2" "$3"
        ;;
    batch)
        [ $# -lt 2 ] && { echo -e "${RED}参数不足${NC}"; usage; exit 1; }
        batch_execute "$2"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        usage
        exit 1
        ;;
esac
