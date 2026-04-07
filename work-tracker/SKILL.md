---
name: work-tracker
description: "일간 출퇴근 기록 및 월간 업무 보고서 생성기. /clockin, /clockout, /recap 세 가지 커맨드를 제공한다. Claude Code 세션 JSONL, Git diff, Auto Memory를 자동 수집하여 일간 요약을 작성하고, 이를 4열 테이블(목표/핵심결과/잘한 점/부족한 점 및 보완계획) 보고서로 집계한다. 다음 키워드가 언급되면 이 스킬을 트리거할 것: 'clockin', 'clockout', 'recap', 'monthly report', 'monthly summary', '출근', '퇴근', '월간 보고서', '업무 요약', '저번 달 정리', '업무 리스트', '피드백 작성'. 자연어 표현도 트리거: '출근 찍어줘', '퇴근할게', '이번 달 뭐 했는지 정리해줘'. 항상 트리거할 것 — 건너뛰지 말 것."
---

# Work Tracker

Automatically capture daily work context and generate monthly reports.

**All output (daily summaries, reports, user-facing messages) must be written in Korean.** The skill instructions here are in English for parsing accuracy, but every artifact the user sees should be in Korean.

## Command routing

| Command       | Triggers                                                                                | Action                                                                          |
| ------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `/clockin`    | "출근", "clockin", "출근 찍어"                                                          | Record clock-in time, snapshot Git HEADs, set session marker                    |
| `/clockout`   | "퇴근", "clockout", "퇴근할게"                                                          | Auto-collect day's context → generate daily summary → save                      |
| `/recap`      | "월간 보고서", "저번 달 정리", "이번 달 업무"                                           | Aggregate daily summaries → user selects tasks → generate final report → export |
| config update | "work-tracker 설정 변경", "노션 말고 옵시디언으로", "레포 추가해줘", "저장 위치 바꿔줘" | Parse intent → update config file → confirm change                              |

When the user's message matches any trigger above, execute the corresponding workflow.

### Config update workflow

Triggered by natural language requests to change settings. Examples:

- "노션 말고 이제 옵시디언으로 쓸거야"
- "레포 하나 더 추가해줘"
- "저장 위치 ~/Dropbox/work-logs 로 바꿔줘"
- "외부 전송 다 꺼줘"

**Steps:**

1. Load `~/.claude/work-tracker-config.yaml`
2. Parse the user's intent and identify which field(s) to change
3. Show a before/after diff of the change and ask for confirmation:

```
다음과 같이 변경할게요.

  변경 전: notion.enabled: true
  변경 후: notion.enabled: false
           obsidian.enabled: true
           obsidian.vault_path: ~/Documents/MyVault

확인하시겠어요? [y/n]
```

4. On confirmation, write the updated config
5. If the new integration (e.g. Obsidian) needs additional info not yet in the config, ask for it before writing:

```
Obsidian 볼트 경로를 입력해주세요. (예: ~/Documents/MyVault)
>
```

6. Confirm the result:

```
✅ 설정이 업데이트되었습니다.
다음 /clockout 부터 Obsidian에 자동 저장됩니다.
```

---

## Prerequisites: Config file

On first run, if `~/.claude/work-tracker-config.yaml` does not exist, run the interactive setup below **step by step**. Ask each question, wait for the user's answer, then proceed to the next step.

### Interactive setup flow

#### Step 1: Repository base directory

Ask the user:

```
[1/2] 레포지토리가 모여 있는 상위 폴더 경로를 입력해주세요.
(예: ~/projects, ~/repos, ~/workspace)
>
```

After the user enters the path:

1. Expand `~` to the absolute home path and verify the directory exists. If it does not exist, tell the user and ask again.
2. Scan the directory for subdirectories that contain a `.git` folder (depth 1 only — do not recurse into nested repos).
3. Present the found repos as a **numbered multi-select list**:

```
다음 레포지토리를 발견했습니다. 추적할 레포를 선택해주세요.
(번호를 쉼표로 구분, 예: 1,3,4 / 'all'로 전체 선택)

  1. my-service-a
  2. my-service-b
  3. infra-scripts
  4. design-system

> 선택:
```

4. For each selected repo, ask its **service name** (Korean label used in reports):

```
'my-service-a'의 서비스 이름을 입력해주세요. (Enter = 폴더명 그대로 사용)
>
```

5. If no `.git` subdirectories are found in the entered path, inform the user:

```
해당 경로에서 Git 레포지토리를 찾지 못했습니다.
직접 레포 경로를 입력하시겠어요? (예: ~/projects/my-repo) [y/n]
```

If yes, accept a comma-separated list of individual repo paths and repeat step 4 for each.

#### Step 2: Git author email (auto-detect, no user prompt)

Run `git config --global user.email` silently and store the result as `git_author` in the config. Do not ask the user anything. If the command fails or returns empty, leave `git_author` as an empty string — the git log step will still work without it.

#### Step 3: Daily summary storage location

Ask the user:

```
[2/4] 일간 요약을 저장할 위치를 선택해주세요.

  1. ~/.claude/work-logs/  (기본값, 권장)
  2. 직접 입력

> 선택 (Enter = 1번):
```

- If the user presses Enter or selects `1` → use `~/.claude/work-logs/`
- If the user selects `2` → prompt:

```
저장 경로를 입력해주세요. (절대경로 또는 ~ 사용 가능)
>
```

Validate that the path can be created (parent directory exists or can be made). If invalid, show an error and re-prompt.

#### Step 3: External integrations (auto-send on clockout)

Explain to the user first:

```
[3/3] 퇴근(clockout) 시 일간 요약을 자동으로 전송할 곳을 선택해주세요.
선택한 곳에는 /clockout 할 때마다 자동으로 전송됩니다.
로컬 저장은 항상 기본으로 포함됩니다.

  1. Notion        — 지정한 데이터베이스에 페이지로 자동 생성
  2. Obsidian      — 지정한 볼트 폴더에 마크다운 파일로 저장
  3. Confluence    — 지정한 스페이스에 페이지로 자동 생성
  4. 기타 (직접 입력) — 저장할 폴더 경로를 직접 지정
  5. 없음          — 로컬만 저장

(번호를 쉼표로 구분해 여러 곳 선택 가능, 예: 1,2 / Enter = 5번)
> 선택:
```

For each selected integration, ask the required settings:

**Notion (option 1):**

```
Notion 데이터베이스 ID를 입력해주세요.
(Notion 페이지 URL 끝의 32자리 문자열)
> Database ID:
```

**Obsidian (option 2):**

```
Obsidian 볼트 경로를 입력해주세요. (예: ~/Documents/MyVault)
> Vault 경로:

저장할 폴더명을 입력해주세요. (Enter = work-logs)
> 폴더명:
```

**Confluence (option 3):**

```
Confluence Base URL을 입력해주세요. (예: https://yourcompany.atlassian.net)
> Base URL:

스페이스 키를 입력해주세요. (예: TEAM)
> Space Key:

부모 페이지 ID를 입력해주세요. (선택사항, Enter로 건너뜀)
> Parent Page ID:
```

**기타 — custom path (option 4):**

```
자동 저장할 폴더 경로를 입력해주세요. (절대경로 또는 ~ 사용 가능)
> 경로:
```

After collecting all integration settings, explain the auto-send behavior:

```
설정한 연동처에는 /clockout 시 일간 요약이 자동으로 전송됩니다.
나중에 설정을 바꾸고 싶으면 그냥 말로 하면 됩니다.
```

#### Step 3.5: Default work hours

Ask the user:

```
출퇴근을 깜빡했을 때 사용할 기본 시간을 설정해주세요.
(Enter = 기본값 사용)

  기본 출근 시간 (Enter = 08:30):
  >

  기본 퇴근 시간 (Enter = 17:30):
  >
```

- If the user presses Enter for either field, use `08:30` / `17:30` respectively.
- These values are used when clockin or clockout time cannot be inferred from session/git data.

#### Step 4: Write config and finish setup

Write `~/.claude/work-tracker-config.yaml` with the collected values:

```yaml
# ~/.claude/work-tracker-config.yaml
repositories:
  - path: ~/projects/my-service-a # filled from user selection
    service_name: 서비스A # filled from user input
  - path: ~/projects/my-service-b
    service_name: 서비스B

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

default_hours:
  clockin: "08:30"   # used when clockin time cannot be inferred
  clockout: "17:30"  # used when clockout time cannot be inferred

monthly_report:
  template: default
  export_default: local

file_management:
  archive_after_months: 2
  delete_archive_after_months: 0
  keep_monthly_reports: true

auto_update_claude_md: true
```

Then automatically create Claude Code slash command files so that /clockin, /clockout, /recap appear in the `/` autocomplete menu:

```bash
mkdir -p ~/.claude/commands
echo "출근 기록. 오늘의 Git HEAD를 스냅샷하고 세션 마커를 설정해줘." > ~/.claude/commands/clockin.md
echo "퇴근 기록. 오늘 하루 세션 컨텍스트를 수집하고 일간 요약을 생성해줘." > ~/.claude/commands/clockout.md
echo "월간 보고서를 생성해줘." > ~/.claude/commands/recap.md
```

Finally, confirm to the user with a summary of all configured settings. List enabled integrations — omit any that were skipped:

```
✅ 설정이 완료되었습니다!

📂 추적 레포: my-service-a (서비스A), my-service-b (서비스B)
💾 로컬 저장: ~/.claude/work-logs/
📤 자동 전송: Notion (database: xxxx), Obsidian (~/Documents/MyVault/work-logs)
   → /clockout 할 때마다 위 경로에 자동으로 업로드됩니다.

슬래시 커맨드가 등록되었습니다. Claude Code를 재시작하면
/clockin, /clockout, /recap이 자동완성 목록에 나타납니다.

출근할 준비가 되면 /clockin 을 입력해주세요!
```

If no external integration was selected, omit the "자동 전송" line entirely.

If the config already exists, load it. If repos have changed, notify the user and suggest updating.

---

## `/clockin` workflow

### Step 1: Load config

Read `~/.claude/work-tracker-config.yaml`. If missing, run interactive setup.

### Step 1.5: Check for missed clockout

Before recording today's clockin, check `~/.claude/work-logs/today.yaml`. If it exists and `clockout_time` is null, a previous clockout was missed.

**Recovery flow:**

1. Notify the user: "어제 퇴근(clockout)을 안 찍으셨네요."
2. Ask: "어제 퇴근 시간이 언제였나요? (예: 17:30, 또는 Enter로 자동 추정)"
3. If user enters a time → use that as clockout_time
4. If user presses Enter → estimate clockout_time from the last session JSONL timestamp or last Git commit time of that day. If neither is available, fall back to `default_hours.clockout` from config (default: 17:30)
5. Run the full `/clockout` workflow for the missed day (collect context, generate summary, save)
6. Then proceed with today's clockin as normal

This ensures no workday is lost even if the user forgets to clockout.

### Step 2: Record clock-in time + Git HEAD snapshots

Save to `~/.claude/work-logs/today.yaml`:

```yaml
clockin_time: "2025-03-20T08:30:00+09:00"
clockout_time: null
planned_tasks: ""
must_do_today: ""
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

Render a visually distinct banner using box-drawing characters. Fill in actual values (time, repo names, planned tasks).

```text
╭──────────────────────────────────────────────╮
│  🌅  WORK TRACKER  ·  출근                     │
╰──────────────────────────────────────────────╯

  ⏰  출근   08:30
  📂  레포   my-service-a  ·  my-service-b

──────────────────────────────────────────────
  오늘도 화이팅! 🙌
  터미널을 열고 닫아도 모든 세션이 추적됩니다.
  퇴근할 때 /clockout 🚪
──────────────────────────────────────────────
```

### Step 6: Ask for must-do task

After showing the banner, ask the user:

```text
✅ 오늘 꼭 해야 할 일이 있으신가요? (없으면 Enter)
>
```

- If the user enters something → save it to `must_do_today` field in `~/.claude/work-logs/today.yaml`
- If the user presses Enter → leave `must_do_today` as empty string, skip silently

---

## `/clockout` workflow

### Step 1: Load config + today.yaml

Read clockin_time and git_snapshots from `~/.claude/work-logs/today.yaml`.
If today.yaml is missing (clockout without clockin), use `default_hours.clockin` from config as clockin_time (default: 08:30).

### Step 2: Auto-collect context

Before collecting, show an opening banner:

```text
╭──────────────────────────────────────────────╮
│  🌙  WORK TRACKER  ·  퇴근                   │
╰──────────────────────────────────────────────╯

  🕐  08:30 → 17:30   (9시간)

  🔍  컨텍스트 수집 중...
```

Then report each source result on its own line as it completes (use ✓ for success, ✗ for skipped/failed):

```text
  ✓  Session JSONL    3개 세션
  ✓  Git diff         커밋 9건  ·  my-service-a, my-service-b
  ✓  Auto Memory      변경 3건
  ✗  MR/Branch        glab 미설치, 건너뜀
```

Collect from 4 sources in order. Graceful fallback if any source fails.

#### Source 1: Session JSONL (priority 1 — richest)

Find `.jsonl` files under `~/.claude/projects/` created/modified after clockin.
Compare with `clockin_sessions.txt` to filter only today's new sessions.

Extract from each JSONL:

- `type: "message"` → user requests (full), assistant responses (first 500 chars)
- `type: "tool_use"` → tool name, target file, timestamp
- Session start/end timestamps for timeline

Fall back to Session Memory (summary.md) if JSONL parsing fails.

#### Source 2: Git diff (priority 2 — most reliable)

```bash
git log --oneline <clockin_head>..HEAD --author="<git_author>"
git diff --stat <clockin_head>..HEAD
```

If glab CLI available:

```bash
glab mr list --author=@me --per-page=10
```

#### Source 3: Auto Memory changes (priority 3)

Read `.md` files under `~/.claude/projects/*/memory/` modified after clockin.

#### Source 4: User manual notes (supplementary)

If user included notes with `/clockout`, include them.
Otherwise ask: "코드 외 업무가 있었나요? (미팅, 코드리뷰 등) 없으면 Enter"

### Step 3: Generate daily summary (in Korean)

Read `templates/daily_summary.md` for the output format. Synthesize all collected context into that template. Every entry must include timestamps from session JSONL and Git commit times.

**Template variables:**

| Variable | Value |
|----------|-------|
| `{{DATE}}` | YYYY-MM-DD |
| `{{DAY}}` | 요일 (월/화/수/목/금) |
| `{{CLOCKIN}}` | HH:MM |
| `{{CLOCKOUT}}` | HH:MM |
| `{{DURATION}}` | N시간 M분 |
| `{{timeline}}` | Array of `{start_time, end_time, service, description}` |
| `{{services}}` | Array of per-repo work blocks |
| `{{non_code}}` | Array of `{time, description}` for non-code work |
| `{{todos}}` | Array of unresolved items / next-day tasks |

To customize the daily summary format, edit `templates/daily_summary.md` directly.

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

If `daily_storage` is fully configured, save automatically without prompting. Always save locally. Show the result as a compact save report:

#### Notion export: markdown → Notion blocks

**Page title format:** Use `YYYY-MM-DD(요일) 업무 요약` — e.g., `2026-03-27(금) 업무 요약`.
Derive the Korean day abbreviation from the date: 월/화/수/목/금/토/일.

**Page properties:** When creating each page, set the `날짜` property (date type) to the clockout date (YYYY-MM-DD). This is the basis for monthly view filtering.

**Monthly view auto-creation:**

Before creating the page, check whether a view named `{N}월` (e.g., `4월`) already exists in the Work Tracker database:

1. Call `GET https://api.notion.com/v1/databases/{database_id}` and inspect the `views` field.
2. If a view named `{N}월` does **not** exist, create it:
   ```json
   POST https://api.notion.com/v1/databases/{database_id}/views
   {
     "name": "4월",
     "type": "list",
     "filter": {
       "property": "날짜",
       "date": {
         "on_or_after": "YYYY-MM-01",
         "before": "YYYY-{MM+1}-01"
       }
     }
   }
   ```
   Use `{N}월` as the view name (N = month number without leading zero, e.g., `4월` not `04월`).
3. Then create the daily summary page as usual — it will automatically appear in the correct month's view.

If the Notion API does not support view creation (older API versions), fall back to creating a **sub-page** named `{N}월` under the Work Tracker database parent, and save daily summaries as child pages inside it.

Notion API does **not** auto-parse markdown. When sending to Notion, convert the summary into proper Notion block objects before calling the API:

| Markdown element | Notion block type |
|-----------------|-------------------|
| `# Heading 1` | `heading_1` |
| `## Heading 2` | `heading_2` |
| `### Heading 3` | `heading_3` |
| `\| table \|` | `table` + `table_row` blocks |
| `- list item` | `bulleted_list_item` |
| plain text paragraph | `paragraph` |

**Table conversion rule:** Parse each markdown table into a `table` block with `has_column_header: true`. Each row becomes a `table_row` block with `cells` as an array of rich text arrays. Never send raw `|---|` markdown as a text block — Notion will render it as plain text.

**Example Notion table block structure:**
```json
{
  "type": "table",
  "table": {
    "table_width": 3,
    "has_column_header": true,
    "children": [
      { "type": "table_row", "table_row": { "cells": [[{"text":{"content":"시간"}}],[{"text":{"content":"서비스"}}],[{"text":{"content":"작업 내용"}}]] }},
      { "type": "table_row", "table_row": { "cells": [[{"text":{"content":"09:33 ~ 10:17"}}],[{"text":{"content":"dw-ai-platform"}}],[{"text":{"content":"커리큘럼 탭 TDD 설계"}}]] }}
    ]
  }
}
```

Before showing the save report, check `must_do_today` in `~/.claude/work-logs/today.yaml`.

**If `must_do_today` is not empty**, show a reminder block first:

```text
──────────────────────────────────────────────
  💡  오늘 꼭 하기로 한 일
     "[must_do_today 값]"

  완료하셨나요? (y / n)
  >
```

- If `y` → append "[완료] [must_do_today 값]" to the daily summary's completed tasks section
- If `n` → append "[미완료] [must_do_today 값]" to the `todos` section so it carries over to tomorrow's plan

**If `must_do_today` is empty**, skip this block entirely.

Then show the save report:

```text
──────────────────────────────────────────────
  📋  일간 요약 저장 완료

  ✓  💾  로컬      ~/.claude/work-logs/2025/03/2025-03-20.md
  ✓  🔴  Notion    "2025-03-20 업무 요약(목)" 페이지 생성됨
  ✗  🟣  Obsidian  설정 없음, 건너뜀

──────────────────────────────────────────────
  수고했어요! 😊  내일 또 /clockin 해주세요 🌟
──────────────────────────────────────────────
```

If no external integrations are configured, omit those lines entirely. If the user has not fully configured storage destinations, ask:

```text
  저장할 위치를 선택해주세요.
  1. 로컬만  →  ~/.claude/work-logs/YYYY/MM/YYYY-MM-DD.md
  2. Notion
  3. Obsidian
  4. Confluence
  5. 모두 (로컬 + 설정된 외부)
  >
```

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

| Input                               | Interpretation                                |
| ----------------------------------- | --------------------------------------------- |
| `/recap`                            | Previous month (default). In March → February |
| `/recap 2025-02`                    | Specific month: February 2025                 |
| `/recap 이번달` or `/recap this`    | Current month (so far)                        |
| `/recap 2025-01 2025-03`            | Range: January through March 2025             |
| `/recap q1` or `/recap 1분기`       | Q1 of current year (Jan–Mar)                  |
| `/recap 2025-h1` or `/recap 상반기` | First half of current year (Jan–Jun)          |

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
1. Merge multi-day work on same branch/MR into single task
1. Tally duration, commit count, MR numbers per task
1. Classify non-code work separately

Output format (Korean):

```text
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

```text
📋 보고할 태스크를 선택하세요 (쉼표로 구분, 'all' 전체 선택):
> 선택:
```

### Step 5: Generate final report (in Korean)

**Template resolution:**

1. `--template=path` flag → that file
1. Config `monthly_report.template` as file path → that file
1. Neither → default 4-column table (see `references/report_format.md`)

**Default format:**

```markdown
# YYYY년 MM월 업무 피드백

| 목표                 | 핵심결과         | 잘한 점        | 부족한 점 및 보완계획 |
| -------------------- | ---------------- | -------------- | --------------------- |
| [서비스명] 상위 목표 | 구체적 구현 내용 | 성과/좋은 결정 | 미해결 이슈/다음 액션 |
```

**Column data sources:**

- **목표**: Infer from task group purpose. Use branch names, MR titles.
- **핵심결과**: Aggregate daily "오늘 한 일" sections. List specific implementations.
- **잘한 점**: Productivity gains, good decisions, proactive improvements. Include decision processes from sessions.
- **부족한 점 및 보완계획**: From "미해결" sections, debugging struggles, test gaps. Propose concrete actions.

One row per service.

### Step 6: Export

```text
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
1. Convert absolute paths to repo-relative (`~/projects/repo/src/file.tsx` → `src/file.tsx`)
1. Mask internal IPs/domains with `[내부주소]`
1. Ask user to confirm: "외부로 전송합니다. 민감 정보가 없는지 확인해주세요."

### Local storage security

1. File permissions: `chmod 600` (owner-only)
2. No code content or secrets even in local files
3. Same rules apply during archive

### Sensitive data regex patterns

```text
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

| File                            | When to read                                      |
| ------------------------------- | ------------------------------------------------- |
| `references/report_format.md`   | When generating default-format report in `/recap`     |
| `references/file_management.md` | When running auto file cleanup in `/clockin`          |
| `templates/daily_summary.md`    | Daily summary format — read this for `/clockout` Step 3 |
| `templates/default.md`          | Monthly report template — read this for `/recap`      |
