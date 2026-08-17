#!/usr/bin/env bash
# ida-start.sh — 启动 IDA Pro MCP HTTP 服务 (Linux 版)
# 等价于 Windows 版的 ida-reverse/scripts/start.ps1

set -euo pipefail

# ─── 配置（根据你的实际安装修改） ─────────────────────────────────────────────────────

IDADIR="${IDADIR:-/opt/idapro}"
MCP_PORT="${IDA_MCP_PORT:-13337}"

# idalib-mcp 可执行文件路径（pip install 后通常在 PATH 中）
MCP_SERVER_CMD="${IDA_MCP_SERVER:-ida-pro-mcp}"

# ─── 检查 ─────────────────────────────────────────────────────────────────────────

if [[ ! -d "$IDADIR" ]]; then
    echo "ERR: IDADIR 不存在: $IDADIR"
    echo "请设置环境变量 IDADIR 指向 IDA Pro 安装目录"
    exit 1
fi

if ! command -v "$MCP_SERVER_CMD" &>/dev/null; then
    echo "ERR: $MCP_SERVER_CMD 未找到"
    echo "请先运行: pip3 install git+https://github.com/mrexodia/ida-pro-mcp.git"
    exit 1
fi

# ─── 杀掉旧进程 ───────────────────────────────────────────────────────────────────

pkill -f "ida-pro-mcp" 2>/dev/null || true
sleep 1

# ─── 启动服务 ──────────────────────────────────────────────────────────────────────

echo "INFO: 启动 IDA MCP HTTP 服务 (port $MCP_PORT) ..."
export IDADIR

nohup "$MCP_SERVER_CMD" --port "$MCP_PORT" > /tmp/ida-mcp.log 2>&1 &
MCP_PID=$!

# ─── 等待就绪 ──────────────────────────────────────────────────────────────────────

TIMEOUT=45
ELAPSED=0

while [[ $ELAPSED -lt $TIMEOUT ]]; do
    if nc -z 127.0.0.1 "$MCP_PORT" 2>/dev/null; then
        echo "OK: IDA MCP 服务已就绪 (PID=$MCP_PID, port=$MCP_PORT)"
        exit 0
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "ERR: 超时 ${TIMEOUT}s，服务未就绪"
echo "查看日志: /tmp/ida-mcp.log"
exit 1
