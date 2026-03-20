#!/bin/bash

SKILL=${1:-""}

if [ -z "$SKILL" ]; then
  echo "Usage: curl -fsSL https://raw.githubusercontent.com/jayounglee92/my-claude-skill/main/install.sh | bash -s <skill>"
  echo ""
  echo "Available skills:"
  echo "  work-tracker"
  echo "  keycloak-auth-generator"
  echo "  fe-sdd-tdd"
  exit 1
fi

mkdir -p ~/.claude/skills

npx degit jayounglee92/my-claude-skill/$SKILL ~/.claude/skills/$SKILL --force

if [ "$SKILL" = "work-tracker" ]; then
  mkdir -p ~/.claude/commands
  echo "출근 기록. 오늘의 Git HEAD를 스냅샷하고 세션 마커를 설정해줘." > ~/.claude/commands/clockin.md
  echo "퇴근 기록. 오늘 하루 세션 컨텍스트를 수집하고 일간 요약을 생성해줘." > ~/.claude/commands/clockout.md
  echo "월간 보고서를 생성해줘." > ~/.claude/commands/recap.md
  echo "Claude Code를 재시작하면 /clockin, /clockout, /recap이 자동완성 목록에 나타납니다."
fi

echo "$SKILL 설치 완료 -> ~/.claude/skills/$SKILL"
