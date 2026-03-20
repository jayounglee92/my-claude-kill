#!/bin/bash
# collect_git_diff.sh — clockin HEAD와 현재 HEAD의 차이를 수집
# Usage: bash collect_git_diff.sh <repo_path> <clockin_head> <git_author>
#
# Output: JSON 형식으로 stdout에 출력

set -euo pipefail

REPO_PATH="${1:?repo_path required}"
CLOCKIN_HEAD="${2:?clockin_head required}"
GIT_AUTHOR="${3:?git_author required}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo '{"error": "Not a git repository: '"$REPO_PATH"'"}'
  exit 0
fi

cd "$REPO_PATH"
REPO_NAME=$(basename "$REPO_PATH")
CURRENT_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# clockin HEAD가 unknown이면 오늘 커밋 전부 수집
if [ "$CLOCKIN_HEAD" = "unknown" ] || [ "$CLOCKIN_HEAD" = "" ]; then
  RANGE="--since='12 hours ago'"
  DIFF_RANGE=""
else
  RANGE="$CLOCKIN_HEAD..HEAD"
  DIFF_RANGE="$CLOCKIN_HEAD..HEAD"
fi

# 커밋 로그
if [ -n "$DIFF_RANGE" ]; then
  COMMITS=$(git log --oneline "$DIFF_RANGE" --author="$GIT_AUTHOR" 2>/dev/null || echo "")
  COMMIT_COUNT=$(echo "$COMMITS" | grep -c '.' 2>/dev/null || echo "0")
  DIFF_STAT=$(git diff --stat "$DIFF_RANGE" 2>/dev/null || echo "")
else
  COMMITS=$(git log --oneline --since='12 hours ago' --author="$GIT_AUTHOR" 2>/dev/null || echo "")
  COMMIT_COUNT=$(echo "$COMMITS" | grep -c '.' 2>/dev/null || echo "0")
  DIFF_STAT=""
fi

# 현재 브랜치
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# 변경된 파일 목록 (이름만, 내용 절대 X)
# 보안: git diff (내용 포함)는 절대 사용하지 않는다. --name-only 또는 --stat만 사용.
if [ -n "$DIFF_RANGE" ]; then
  CHANGED_FILES=$(git diff --name-only "$DIFF_RANGE" 2>/dev/null || echo "")
else
  CHANGED_FILES=""
fi

# 보안: 민감 파일 마스킹 (.env*, *.key, *.pem 등)
CHANGED_FILES=$(echo "$CHANGED_FILES" | sed \
  -e 's|.*\.env.*|[민감 설정 파일]|g' \
  -e 's|.*\.pem$|[민감 인증서 파일]|g' \
  -e 's|.*\.key$|[민감 키 파일]|g' \
  -e 's|.*\.p12$|[민감 인증서 파일]|g' \
  -e 's|.*\.pfx$|[민감 인증서 파일]|g' \
  -e 's|.*secret.*|[민감 설정 파일]|g' \
  -e 's|.*credential.*|[민감 설정 파일]|g' \
  -e 's|.*password.*|[민감 설정 파일]|g' \
  | sort -u)

# JSON 출력 (jq 없이 수동 생성)
cat <<EOF
{
  "repo_name": "$REPO_NAME",
  "repo_path": "$REPO_PATH",
  "clockin_head": "$CLOCKIN_HEAD",
  "current_head": "$CURRENT_HEAD",
  "current_branch": "$CURRENT_BRANCH",
  "commit_count": $COMMIT_COUNT,
  "commits": $(echo "$COMMITS" | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
print(json.dumps(lines))
" 2>/dev/null || echo '[]'),
  "diff_stat": $(echo "$DIFF_STAT" | python3 -c "
import sys, json
print(json.dumps(sys.stdin.read().strip()))
" 2>/dev/null || echo '""'),
  "changed_files": $(echo "$CHANGED_FILES" | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
print(json.dumps(lines))
" 2>/dev/null || echo '[]')
}
EOF
