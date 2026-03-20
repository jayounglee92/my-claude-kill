---
name: work-tracker
description: "Daily clock-in/out tracking and monthly work report generator. Provides three commands: /clockin, /clockout, /recap. Automatically collects Claude Code session JSONL, Git diff, and Auto Memory to build daily summaries, then aggregates them into a 4-column table report (goals/results/strengths/improvements). Trigger this skill when the user mentions 'clockin', 'clockout', 'recap', 'monthly report', 'monthly summary', or any Korean equivalents like '출근', '퇴근', '월간 보고서', '업무 요약', '저번 달 정리', '업무 리스트', '피드백 작성'. Also trigger on natural language like '출근 찍어줘', '퇴근할게', '이번 달 뭐 했는지 정리해줘'. Always trigger — do not skip."
---

# Work Tracker

Automatically capture daily work context and generate monthly reports.

**All output (daily summaries, reports, user-facing messages) must be written in Korean.** The skill instructions here are in English for parsing accuracy, but every artifact the user sees should be in Korean.

## Command routing

| Command | Triggers | Action |
|---------|----------|--------|
| `/clockin` | "출근", "clockin", "출근 찍어" | Record clock-in time, snapshot Git HEADs, set session marker |
| `/clockout` | "퇴근", "clockout", "퇴근할게" | Auto-collect day's context → generate daily summary → save |
| `/recap` | "월간 보고서", "저번 달 정리", "이번 달 업무" | Aggregate daily summaries → user selects tasks → generate final report → export |

When the user's message matches any trigger above, execute the corresponding workflow.

---

## Prerequisites: Config file

On first run, if `~/.claude/work-tracker-config.yaml` does not exist, interactively ask the user to create it.

Required settings:
1. Repository list (path + service name)
2. Git author email
3. Daily summary storage location (default: local)

```yaml
# ~/.claude/work-tracker-config.yaml
repositories:
  - path: ~/projects/my-service-a    # example
    service_name: 서비스A              # example — replace with actual name
  - path: ~/projects/my-service-b    # example
    service_name: 서비스B              # example — replace with actual name

git_author: "user@company.com"

claude_projects_dir: ~/.claude/projects

daily_storage:
  local: true
  local_path: ~/.claude/work-logs/
  notion:
    enabled: false
    database_id: ""
  obsidian:
    enabled: false
    vault_path: ""
    folder: work-logs
  confluence:
    enabled: false
    base_url: ""
    space_key: ""
    parent_page_id: ""

monthly_report:
  template: default
  export_default: local

file_management:
  archive_after_months: 2
  delete_archive_after_months: 0
  keep_monthly_reports: true

auto_update_claude_md: true
```

If the config already exists, load it. If repos have changed, notify the user and suggest updating.

---

## `/clockin` workflow

### Step 1: Load config
Read `~/.claude/work-tracker-config.yaml`. If missing, run interactive setup.

### Step 1.5: Check for missed clockout

Before recording today's clockin, check `~/.claude/work-logs/today.yaml`. If it exists and `clockout_time` is null, a previous clockout was missed.

**Recovery flow:**
1. Notify the user: "어제 퇴근(clockout)을 안 찍으셨네요."
2. Ask: "어제 퇴근 시간이 언제였나요? (예: 18:30, 또는 Enter로 자동 추정)"
3. If user enters a time → use that as clockout_time
4. If user presses Enter → estimate clockout_time from the last session JSONL timestamp or last Git commit time of that day
5. Run the full `/clockout` workflow for the missed day (collect context, generate summary, save)
6. Then proceed with today's clockin as normal

This ensures no workday is lost even if the user forgets to clockout.

### Step 2: Record clock-in time + Git HEAD snapshots

Save to `~/.claude/work-logs/today.yaml`:

```yaml
clockin_time: "2025-03-20T09:15:00+09:00"
clockout_time: null
planned_tasks: ""
git_snapshots:
  my-service-a: "abc1234def"
  my-service-b: "567890abc"
```

Run `git rev-parse HEAD` in each repo to capture current HEAD.
If the user included a note (e.g., `/clockin 오늘은 로그인 페이지 작업 예정`), store in `planned_tasks`.

### Step 3: Snapshot existing session list

```bash
ls ~/.claude/projects/*/ 2>/dev/null | grep ".jsonl" > ~/.claude/work-logs/clockin_sessions.txt
```

This allows `/clockout` to filter only sessions created after clock-in.

### Step 4: Auto file cleanup

Run archive logic per `file_management.archive_after_months`. See `references/file_management.md`.

### Step 5: Confirm to user (in Korean)

```
✅ 출근 기록됨 (09:15)
📂 추적 중인 레포: my-service-a, my-service-b
📝 오늘 계획: 로그인 페이지 작업 예정

하루 동안 자유롭게 작업하세요.
터미널 여러 개 열고 닫아도 전부 추적됩니다.
퇴근할 때 /clockout 해주세요!
```

---

## `/clockout` workflow

### Step 1: Load config + today.yaml

Read clockin_time and git_snapshots from `~/.claude/work-logs/today.yaml`.
If today.yaml is missing (clockout without clockin), assume clockin_time = today 00:00.

### Step 2: Auto-collect context

Collect from 4 sources in order. Graceful fallback if any source fails.

**Source 1: Session JSONL (priority 1 — richest)**

Find `.jsonl` files under `~/.claude/projects/` created/modified after clockin.
Compare with `clockin_sessions.txt` to filter only today's new sessions.

Extract from each JSONL:
- `type: "message"` → user requests (full), assistant responses (first 500 chars)
- `type: "tool_use"` → tool name, target file, timestamp
- Session start/end timestamps for timeline

Fall back to Session Memory (summary.md) if JSONL parsing fails.

**Source 2: Git diff (priority 2 — most reliable)**

```bash
git log --oneline <clockin_head>..HEAD --author="<git_author>"
git diff --stat <clockin_head>..HEAD
```

If glab CLI available:
```bash
glab mr list --author=@me --per-page=10
```

**Source 3: Auto Memory changes (priority 3)**

Read `.md` files under `~/.claude/projects/*/memory/` modified after clockin.

**Source 4: User manual notes (supplementary)**

If user included notes with `/clockout`, include them.
Otherwise ask: "코드 외 업무가 있었나요? (미팅, 코드리뷰 등) 없으면 Enter"

### Step 3: Generate daily summary (in Korean)

Synthesize all context into this markdown format. Every entry must include timestamps from session JSONL and Git commit times.

```markdown
# YYYY-MM-DD (요일) 업무 요약

## 근무 시간
HH:MM ~ HH:MM (N시간 M분)

## 타임라인

| 시간 | 서비스 | 작업 내용 |
|------|--------|---------|
| 09:15 ~ 10:42 | [서비스A] | 로그인 페이지 레이아웃 구현 |
| 10:42 ~ 11:30 | [서비스A] | 소셜 로그인 API 연동 |
| 11:30 ~ 12:00 | — | 코드리뷰: my-service-b MR !142 |
| 13:00 ~ 14:20 | [서비스B] | 검색 필터 버그 수정 |
| 14:20 ~ 16:45 | [서비스A] | 폼 유효성 검증 및 에러 핸들링 |
| 16:45 ~ 18:00 | [서비스A] | Claude와 SSR 이슈 디버깅 |

## 오늘 한 일

### [서비스A] my-service-a (09:15 ~ 16:45)
- 로그인 페이지 리뉴얼 구현
  - 09:15 ~ 10:42 | 레이아웃 및 반응형 대응
  - 10:42 ~ 11:30 | 소셜 로그인 API 연동
  - 14:20 ~ 16:45 | 폼 유효성 검증, 에러 핸들링
  - 커밋 7건, +324 / -45 lines
  - MR !147 생성 (리뷰 대기중)
- Claude와 논의한 내용: (16:45 ~ 18:00)
  - SSR 환경에서 dynamic import 적용 방법 논의

### [서비스B] my-service-b (13:00 ~ 14:20)
- 검색 필터 버그 수정
  - 13:00 ~ 14:20 | flexbox gap → margin으로 변경
  - 커밋 2건, +12 / -8 lines

### 코드 외 업무
- 11:30 ~ 12:00 | 코드리뷰: my-service-b MR !142

## 내일 할 일 / 미해결
- (unresolved issues from sessions, TODOs)
```

**Timestamp extraction:**
- **Session time**: From `timestamp` field in each JSONL entry.
- **Commit time**: `git log --format="%H|%ad" --date=format:"%H:%M"`
- **Service mapping**: Match edited file paths to repo directories.
- **Overlap handling**: If two sessions overlap, assign by file edit volume.

**Generation rules:**
- Group commits into task-level summaries — never list individual commit messages
- Never include code content (security). Only describe what was changed at file level
- Summarize Claude discussions in 2-3 lines from session JSONL
- All timestamps in HH:MM format
- Fall back to Git commit times if JSONL timestamps unavailable

### Step 4: Save

```
📤 오늘의 업무 요약을 어디에 저장할까요?
  1. 로컬 (기본) → ~/.claude/work-logs/YYYY/MM/YYYY-MM-DD.md
  2. Notion
  3. Obsidian
  4. Confluence
  5. 모두 (로컬 + 설정된 외부)
```

If default configured, save automatically and show result. Always save locally.

### Step 5: Update CLAUDE.md (optional)

If `auto_update_claude_md: true`, update each repo's CLAUDE.md:

```markdown
## Recent work (auto-updated by work-tracker)
- YYYY-MM-DD: one-line work summary
- YYYY-MM-DD: one-line work summary
```

Keep last 5 days only. Auto-remove older entries.

### Step 6: Update today.yaml

Record clockout_time. File preserved until next clockin.

---

## `/recap` workflow

### Step 1: Determine target period

`/recap` supports multiple argument formats for flexibility:

| Input | Interpretation |
|-------|---------------|
| `/recap` | Previous month (default). In March → February |
| `/recap 2025-02` | Specific month: February 2025 |
| `/recap 이번달` or `/recap this` | Current month (so far) |
| `/recap 2025-01 2025-03` | Range: January through March 2025 |
| `/recap q1` or `/recap 1분기` | Q1 of current year (Jan–Mar) |
| `/recap 2025-h1` or `/recap 상반기` | First half of current year (Jan–Jun) |

**Parsing rules:**
- Single YYYY-MM → that month only
- Two YYYY-MM values → inclusive range
- Korean natural language: "이번달" = current month, "저번달" = previous month, "3달" or "최근 3개월" = last 3 months
- Quarter: "q1"/"1분기" = Jan–Mar, "q2"/"2분기" = Apr–Jun, etc.
- Half: "h1"/"상반기" = Jan–Jun, "h2"/"하반기" = Jul–Dec
- If the range spans multiple months, aggregate all daily summaries across those months

**When current month is requested:** Only include days up to today. Warn the user: "이번 달은 아직 진행 중이에요. 오늘(N일)까지의 데이터로 생성합니다."

### Step 2: Load daily summaries

Read all `.md` files from `~/.claude/work-logs/YYYY/MM/`. Use `archive.md` if present.

### Step 3: Aggregate tasks by service

Analyze daily summaries to:
1. Group by service (repo)
2. Merge multi-day work on same branch/MR into single task
3. Tally duration, commit count, MR numbers per task
4. Classify non-code work separately

Output format (Korean):
```
## YYYY년 MM월 업무 리스트

### [서비스명] 레포명 (N일 작업, M커밋)
1. ✅ 태스크 제목
   - 기간: M/D ~ M/D (N일)
   - 커밋 N건, MR !번호 머지
   - 주요 결정: ...
2. 🔧 진행 중인 태스크
   - ...

### 코드 외 업무
- 코드리뷰: N건
- 미팅: 목록
```

### Step 4: User selects tasks

Show numbered task list. User picks which to include:
```
📋 보고할 태스크를 선택하세요 (쉼표로 구분, 'all' 전체 선택):
> 선택:
```

### Step 5: Generate final report (in Korean)

**Template resolution:**
1. `--template=path` flag → that file
2. Config `monthly_report.template` as file path → that file
3. Neither → default 4-column table (see `references/report_format.md`)

**Default format:**
```markdown
# YYYY년 MM월 업무 피드백

| 목표 | 핵심결과 | 잘한 점 | 부족한 점 및 보완계획 |
|------|---------|--------|-------------------|
| [서비스명] 상위 목표 | 구체적 구현 내용 | 성과/좋은 결정 | 미해결 이슈/다음 액션 |
```

**Column data sources:**
- **목표**: Infer from task group purpose. Use branch names, MR titles.
- **핵심결과**: Aggregate daily "오늘 한 일" sections. List specific implementations.
- **잘한 점**: Productivity gains, good decisions, proactive improvements. Include decision processes from sessions.
- **부족한 점 및 보완계획**: From "미해결" sections, debugging struggles, test gaps. Propose concrete actions.

One row per service.

### Step 6: Export

```
📤 어디로 보낼까요?
  1. Notion → "YYYY년 MM월 나의 업무 리스트" + "YYYY년 MM월 나의 피드백"
  2. Obsidian → {vault}/monthly-reports/
  3. Confluence → designated space
  4. 로컬 파일 → ~/.claude/work-logs/reports/
  5. 클립보드
```

Always produce 2 documents:
- **업무 리스트**: Full task list (all tasks)
- **피드백**: Final report (selected tasks only)

---

## Data source priority

Priority order for `/clockout`. Fall back to next on failure.

1. **Session JSONL** — Richest. Full conversations, tool usage, file edits. Persists on disk regardless of terminal count.
2. **Git diff** — Most reliable. Hard facts about code changes. Session-independent.
3. **Auto Memory** — Claude's self-saved insights. Architecture decisions, debugging notes.
4. **Session Memory** — Per-session auto-summaries. JSONL fallback.
5. **MR/Branch** — Code review, merge status. Collaboration context.
6. **Manual notes** — Non-code work only. For what can't be auto-collected.

---

## Security and sensitive data protection

This skill handles Git history, session conversations, and code changes that may contain sensitive data. Follow these rules strictly.

### Never collect

Never read, store, or include in any summary:

- **Secrets/credentials**: API keys, tokens, passwords, certificates, private keys
  - Patterns: `password`, `secret`, `token`, `api_key`, `apikey`, `api-key`, `private_key`, `credential`, `auth_token`, `access_key`, `bearer`
- **Environment variable files**: `.env`, `.env.local`, `.env.production`, `.env.*` contents
- **Certificate/key files**: `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore` contents
- **PII**: National ID numbers, phone numbers, email addresses, physical addresses, card numbers
- **Internal infrastructure**: Internal IPs, database connection strings, server hostnames, VPN info

### Git diff security

1. Collect **commit messages only** — never code diff content
2. Record only **file names and line counts** (not content)
3. Commits touching `.env*`, `*secret*`, `*credential*`, `*password*` files → summarize as "설정 파일 변경" and mask filename
4. Use only `git diff --stat`. Never `git diff` with content.

### Session JSONL security

1. **Strip code blocks** from assistant responses → replace with "[코드 블록 — 보안상 생략]"
2. User messages containing secret patterns → replace entire message with "[민감 정보 포함 — 스킵됨]"
3. Never collect file content from Write/Edit tool inputs — record only path and tool name
4. Bash commands containing secret patterns → replace with "[민감 명령어 — 스킵됨]"

### External export security

Before sending to Notion, Confluence, Obsidian, etc.:
1. Final scan for secret patterns
2. Convert absolute paths to repo-relative (`~/projects/repo/src/file.tsx` → `src/file.tsx`)
3. Mask internal IPs/domains with `[내부주소]`
4. Ask user to confirm: "외부로 전송합니다. 민감 정보가 없는지 확인해주세요."

### Local storage security

1. File permissions: `chmod 600` (owner-only)
2. No code content or secrets even in local files
3. Same rules apply during archive

### Sensitive data regex patterns

```
# Secrets (case-insensitive)
(password|passwd|secret|token|api[_-]?key|private[_-]?key|credential|auth[_-]?token|access[_-]?key|bearer|client[_-]?secret)[\s]*[=:"']

# Env files
\.(env|env\..+)$

# Key/cert files
\.(pem|key|p12|pfx|jks|keystore|cer|crt)$

# Internal network
(10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)

# DB connection strings
(mongodb|postgres|mysql|redis|amqp):\/\/[^\s]+
```

---

## Reference files

| File | When to read |
|------|-------------|
| `references/report_format.md` | When generating default-format report in `/recap` |
| `references/file_management.md` | When running auto file cleanup in `/clockin` |
| `templates/default.md` | When a report template is needed |
