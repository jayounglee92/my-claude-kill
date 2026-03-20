# Work Tracker

매일 출퇴근 시점에 업무 컨텍스트를 자동 캡처하고, 월간 보고서를 생성하는 Claude Code 스킬.

## 커맨드

```bash
/clockin                              # 출근 기록
/clockin 오늘은 로그인 페이지 작업 예정          # 출근 + 오늘 계획 메모

/clockout                             # 퇴근 → 일간 요약 자동 생성
/clockout 코드리뷰 2건, 프론트 미팅 참석   # 퇴근 + 코드 외 업무 메모

/recap                              # 전달 월간 보고서 생성
/recap 2025-02                      # 특정 월 지정
/recap 이번달                        # 이번 달 (진행중)
/recap 2025-01 2025-03              # 1월~3월 범위
/recap q1                           # 1분기 (1~3월)
/recap 상반기                        # 상반기 (1~6월)
/recap --template=~/t.md            # 커스텀 양식
```

## 어떻게 동작하는가

```
/clockin (09:15)
  → Git HEAD 스냅샷 저장
  → 세션 마커 설정

  ... 하루 동안 터미널 여러 개 열고 닫으며 작업 ...
  (세션마다 JSONL이 자동으로 디스크에 쌓임)

/clockout (18:30)
  → Session JSONL 자동 수집 (오늘 모든 세션)
  → Git diff 수집 (clockin HEAD vs 현재 HEAD)
  → Auto Memory 변경분 수집
  → MR/Branch 정보 수집
  → + 사용자 수동 메모 (코드 외 업무)
  → Claude가 일간 요약 생성
  → 로컬 .md / Notion / Obsidian / Confluence 저장

/recap (매월 초)
  → 30일치 일간 요약 로드
  → 서비스별 태스크 종합
  → 사용자가 보고할 항목 선택
  → 4열 테이블 보고서 생성 (목표/핵심결과/잘한점/보완계획)
  → 내보내기
```

## Claude Code의 세션 간 컨텍스트 유지 메커니즘

이 스킬이 "터미널을 여러 번 열고 닫아도 컨텍스트가 유지된다"고 말할 수 있는 이유는, Claude Code가 **3겹의 영속 데이터**를 디스크에 남기기 때문이다.

### 1. Auto Memory (공식, v2.1.59+)

- **위치**: `~/.claude/projects/<project>/memory/`
- **내용**: Claude가 스스로 중요하다고 판단한 것을 자동 저장. 빌드 명령, 디버깅 인사이트, 아키텍처 노트, 코드 스타일 선호 등.
- **특징**: 세션 시작 시 자동 로드. `/memory`로 확인/토글 가능.

### 2. Session Memory (공식, Pro/Max)

- **위치**: `~/.claude/projects/<hash>/<session-id>/session-memory/summary.md`
- **내용**: 세션 중 ~10,000토큰마다 자동으로 요약 생성. 다음 세션 시작 시 관련 과거 세션 요약을 자동 주입.
- **특징**: "Recalled X memories" / "Wrote X memories" 메시지로 확인. `ctrl+o`로 내용 조회.
- **주의**: 과거 세션을 "참고 자료"로 취급하며, 지시사항으로 따르지는 않음.

### 3. Session JSONL 트랜스크립트 (비공식, 안정적)

- **위치**: `~/.claude/projects/<hash>/<session-id>.jsonl`
- **내용**: 모든 대화의 라인별 트랜스크립트. 메시지, 도구 사용, 파일 편집 전부 기록.
- **특징**: `claude --resume` 또는 `claude -c`로 이전 세션 이어가기 가능.
- **이 스킬에서의 역할**: `/clockout`이 이 JSONL을 파싱하여 오늘 하루의 모든 세션 컨텍스트를 복원함. **가장 핵심적인 데이터 소스**.

> **결론**: 세션이 끝나도 대화 데이터는 디스크에 남아있다. `/clockout`은 이 데이터를 읽어서 일간 요약을 만들기 때문에, 터미널을 몇 번 열고 닫든 상관없다.

## 로컬 파일 저장 — 용량 문제 없음

일간 요약은 텍스트 파일(2~3KB/일)이라 용량 부담이 거의 없다.

| 기간 | 파일 수 | 용량 |
|------|--------|------|
| 1개월 | ~22개 | ~60KB |
| 1년 | ~260개 | ~720KB |
| 5년 | ~1,300개 | ~3.5MB |

5년을 써도 사진 한 장보다 작다.

### 자동 파일 정리 정책

파일 수가 쌓이는 것은 자동 정리로 관리한다. `/clockin` 실행 시 백그라운드로 정리.

- **Hot (0~2개월)**: 개별 .md 파일 원본 보관. `/recap`가 직접 읽는 대상.
- **Archive (3개월+)**: 월별 1개 archive.md로 병합. 30개 파일 → 1개 (~5KB).
- **Cold (1년+)**: 외부 백업이 있으면 로컬 삭제 가능. 없으면 그대로 유지 (부담 없음).

```yaml
# config에서 정책 설정
file_management:
  archive_after_months: 2        # 2개월 지난 일간 요약 자동 archive
  delete_archive_after_months: 0 # 0 = 삭제 안 함
  keep_monthly_reports: true     # 최종 보고서는 항상 보관
```

### 개선 여지

- 현재는 단순 시간 기반 archive. 향후 "중요도 기반 보관" (커밋 많은 날은 상세 보관, 적은 날은 요약만) 가능.
- Git LFS 스타일의 로컬/원격 분리 — 최근 N개월은 로컬, 나머지는 Notion/Confluence에서 온디맨드 로드.
- archive 포맷을 SQLite로 변경하면 날짜 범위 검색이 빨라짐.

## 보안

이 스킬은 Git 히스토리, Claude 세션 대화 등 민감할 수 있는 데이터를 다루기 때문에 다층적 보안 필터링을 적용한다.

### 절대 수집하지 않는 것

- **시크릿/크리덴셜**: API 키, 토큰, 비밀번호, 인증서, 개인키 등
- **환경 변수 파일**: `.env`, `.env.local`, `.env.production` 등의 내용
- **인증서/키 파일**: `*.pem`, `*.key`, `*.p12` 등의 내용
- **개인정보(PII)**: 주민등록번호, 카드번호 등
- **인프라 정보**: 내부 IP, DB 접속 문자열, 서버 호스트명

### 수집 단계별 필터링

| 단계 | 필터링 내용 |
|------|-----------|
| Git diff | 커밋 메시지만 수집, 코드 diff 전문 X. `.env*` 관련 커밋은 마스킹 |
| Session JSONL | 코드 블록 제거, 시크릿 포함 메시지 스킵, Bash 명령어 중 민감 명령 마스킹 |
| 일간 요약 저장 | 파일 경로를 레포 기준 상대경로로 변환, 홈 디렉토리 절대경로 제거 |
| 외부 전송 | 전송 전 최종 스캔, 내부 IP/도메인 마스킹, 사용자 확인 요청 |
| 로컬 저장 | 파일 권한 `chmod 600` (소유자만 읽기) |

### `collect_sessions.py`의 내장 필터

스크립트에 정규식 기반 필터가 내장되어 있다:
- `contains_secret(text)` — 시크릿 패턴 감지
- `sanitize_text(text)` — 민감 정보 마스킹, 코드 블록 제거
- `sanitize_filepath(path)` — 민감 파일 마스킹, 절대경로→상대경로 변환
- `is_sensitive_file(path)` — `.env`, `.pem` 등 민감 파일 판별

### 주의사항

- 필터링은 **최선의 노력(best-effort)** 방식이다. 모든 민감 정보를 100% 잡아내지 못할 수 있다.
- 외부(Notion/Confluence 등)로 전송하기 전에 사용자가 직접 한 번 더 확인하는 것을 권장한다.
- 회사의 보안 정책에 따라 외부 전송 자체를 비활성화할 수 있다 (`daily_storage.notion.enabled: false` 등).

## 설정

최초 실행 시 `~/.claude/work-tracker-config.yaml`을 인터랙티브하게 생성한다.

```yaml
# 관리하는 레포 목록
repositories:
  - path: ~/projects/my-service-a    # 예시
    service_name: 서비스A              # 예시 — 실제 서비스명으로 변경
  - path: ~/projects/my-service-b    # 예시
    service_name: 서비스B              # 예시 — 실제 서비스명으로 변경

# Git author
git_author: "user@company.com"

# 일간 요약 저장 위치
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

# 월간 보고서
monthly_report:
  template: default              # default 또는 커스텀 템플릿 파일 경로
  export_default: local          # local / notion / obsidian / confluence
```

## 내보내기 대상

| 대상 | 일간 요약 | 월간 보고서 | 연동 방식 |
|------|---------|-----------|---------|
| 로컬 | ✅ (기본) | ✅ | 파일 시스템 직접 쓰기 |
| Notion | ✅ | ✅ | Notion MCP 서버 또는 API |
| Obsidian | ✅ | ✅ | 볼트 경로에 .md 파일 저장 |
| Confluence | ✅ | ✅ | Atlassian MCP 서버 또는 API |
| 클립보드 | — | ✅ | 복사만 |

## 디렉토리 구조

```
~/.claude/
├── work-tracker-config.yaml          # 설정 파일
└── work-logs/
    ├── today.yaml                    # 오늘의 clockin 상태
    ├── clockin_sessions.txt          # clockin 시점 세션 목록
    ├── 2025/
    │   ├── 01/
    │   │   └── archive.md            # 3개월+ 지난 월은 archive
    │   ├── 02/
    │   │   └── archive.md
    │   └── 03/
    │       ├── 2025-03-01.md         # 개별 일간 요약
    │       ├── 2025-03-02.md
    │       └── ...
    └── reports/                      # 최종 보고서 (항상 보관)
        ├── 2025-01-업무리스트.md
        ├── 2025-01-피드백.md
        └── ...
```

## 비개발자 확장

동일한 프레임워크로 직군별 커스터마이징 가능. config의 context_sources만 변경.

| 직군 | 자동 소스 | 수동 소스 |
|------|---------|---------|
| 프론트엔드 개발자 | Session JSONL, Git, MR, Auto Memory | 미팅, 코드리뷰 |
| 기획자/PM | Jira/Linear, Notion, Calendar (MCP) | 이해관계자 미팅 |
| 디자이너 | Figma API, Notion (MCP) | 디자인 리뷰 |
