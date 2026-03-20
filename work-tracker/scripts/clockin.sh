#!/bin/bash
# clockin.sh — 출근 기록 스크립트
# Usage: bash clockin.sh <config_path> [planned_tasks]

set -euo pipefail

CONFIG_PATH="${1:-$HOME/.claude/work-tracker-config.yaml}"
PLANNED_TASKS="${2:-}"
WORK_LOGS_DIR="$HOME/.claude/work-logs"
TODAY_FILE="$WORK_LOGS_DIR/today.yaml"
SESSIONS_FILE="$WORK_LOGS_DIR/clockin_sessions.txt"

# 디렉토리 생성
mkdir -p "$WORK_LOGS_DIR"

# 현재 시간
CLOCKIN_TIME=$(date -Iseconds)
CLOCKIN_DISPLAY=$(date +"%H:%M")

# Git HEAD 스냅샷 수집
# config에서 레포 목록을 읽어야 하지만, 여기서는 인자로 받거나
# Claude가 config를 파싱해서 레포 경로를 전달하는 방식으로 사용
# 이 스크립트는 Claude가 호출할 때 레포 경로를 환경변수로 전달받음

echo "clockin_time: \"$CLOCKIN_TIME\"" > "$TODAY_FILE"
echo "clockout_time: null" >> "$TODAY_FILE"
echo "planned_tasks: \"$PLANNED_TASKS\"" >> "$TODAY_FILE"
echo "git_snapshots:" >> "$TODAY_FILE"

# REPOS 환경변수가 설정되어 있으면 (콜론으로 구분된 경로 목록)
if [ -n "${REPOS:-}" ]; then
  IFS=':' read -ra REPO_ARRAY <<< "$REPOS"
  for repo in "${REPO_ARRAY[@]}"; do
    if [ -d "$repo/.git" ]; then
      REPO_NAME=$(basename "$repo")
      HEAD_HASH=$(cd "$repo" && git rev-parse HEAD 2>/dev/null || echo "unknown")
      echo "  $REPO_NAME: \"$HEAD_HASH\"" >> "$TODAY_FILE"
    fi
  done
fi

# 기존 세션 목록 스냅샷
CLAUDE_PROJECTS="$HOME/.claude/projects"
if [ -d "$CLAUDE_PROJECTS" ]; then
  find "$CLAUDE_PROJECTS" -name "*.jsonl" -type f 2>/dev/null > "$SESSIONS_FILE"
else
  touch "$SESSIONS_FILE"
fi

echo "$CLOCKIN_DISPLAY"
