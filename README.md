# My Claude Skills

개인 Claude Skills 모음집입니다.

## 스킬 목록

| 스킬 | 설명 | 트리거 키워드 |
| --- | --- | --- |
| [fe-sdd-tdd](#fe-sdd-tdd) | Spec 작성 → 테스트 → 구현 순서를 강제하는 프론트엔드 TDD 워크플로우 | "구현해줘", "TDD", "spec 만들어줘" |
| [keycloak-auth-generator](#keycloak-auth-generator) | 프레임워크별 Keycloak SSO 인증 코드 자동 생성 | "Keycloak 연동", "SSO", "로그인 페이지" |
| [work-tracker](#work-tracker) | 출퇴근 자동 기록 + 월간 업무 보고서 생성 | "출근", "퇴근", "월간 보고서", /clockin, /clockout, /recap |

---

## fe-sdd-tdd

### Frontend Spec-Driven Development + Test-Driven Development

프론트엔드 기능을 구현할 때 **Spec 작성 → 테스트 작성 → 구현** 순서를 강제하는 워크플로우 스킬입니다.

### 플로우 (fe-sdd-tdd)

```text
Spec이 있나? → 없으면 만든다 → 테스트 먼저 작성 → 최소 구현 → 리팩터링 → 완료 체크
```

### 주요 기능

- **Spec 자동 생성** — 기능 유형별 맞춤 질문 + 코드베이스 분석으로 Spec 초안 생성
- **Testing Trophy 기반 TDD** — Unit → Integration (MSW) → E2E (Playwright)
- **구현 중 의사결정** — TODO/FIXME 스캔, 미구현 항목 탐지
- **완료 체크리스트** — 반응형(필수), 접근성, i18n, Storybook 등

### 사용 예시 (fe-sdd-tdd)

```text
"댓글 위젯 만들어줘"
"회원가입 기능 구현"
"TDD로 개발하자"
```

### 파일 구조 (fe-sdd-tdd)

```text
fe-sdd-tdd/
├── SKILL.md
└── references/
    ├── spec-template.md
    ├── test-examples.md
    ├── msw-and-playwright.md
    └── checklists.md
```

---

## keycloak-auth-generator

### Keycloak SSO 인증 코드 자동 생성기

7개 프레임워크에 대해 Keycloak SSO 인증에 필요한 모든 코드를 자동 생성합니다. keycloakify 대신 각 프레임워크의 공식 권장 방식을 사용합니다.

### 지원 프레임워크

| 프레임워크 | 인증 방식 | UI 디자인 시스템 |
| --- | --- | --- |
| Next.js | Auth.js v5 + Keycloak Provider | shadcn/ui, MUI, Ant Design |
| Vue 3 | @josempgon/vue-keycloak | Vuetify, PrimeVue, Element Plus |
| Nuxt 3 | sidebase/nuxt-auth | Nuxt UI, Vuetify |
| FastAPI | PyJWT (JWT) | Swagger UI |
| Django | mozilla-django-oidc | crispy-forms+Bootstrap |
| Flask | Authlib | Bootstrap 5 |
| Thymeleaf | Spring Security OAuth2 | Bootstrap 5 |

### 플로우 (keycloak-auth-generator)

```text
정보 수집 → 디자인 시스템 선택 → 코드 생성 → 패키지 자동 설치 → Keycloak 환경 선택 → 완료
```

### 생성되는 코드

- 로그인 페이지 (선택한 디자인 시스템 적용)
- 로그아웃 (Keycloak 세션까지 종료)
- 토큰 자동 재발급
- 인증 미들웨어/가드
- 역할 기반 접근제어 (RBAC)
- 타입 정의
- Docker 기반 로컬 Keycloak (선택)

### Keycloak 환경 옵션

| 옵션 | 설명 | Keycloak 서버 필요 |
| --- | --- | --- |
| Docker | docker-compose + realm 자동 설정. 바로 테스트 가능 | 불필요 (Docker가 대신) |
| 기존 서버 | 이미 있는 Keycloak에 연결. Admin Console 설정 안내 | 필요 |
| 코드만 | placeholder 값으로 생성. 나중에 연결 | 불필요 |

### 사용 예시 (keycloak-auth-generator)

```text
"Next.js에 Keycloak 연동해줘"
"FastAPI 인증 코드 만들어줘"
"SSO 붙여줘"
```

### 파일 구조 (keycloak-auth-generator)

```text
keycloak-auth-generator/
├── SKILL.md
├── README.md
└── references/
    ├── nextjs.md
    ├── vue3.md
    ├── nuxt3.md
    ├── fastapi.md
    ├── django.md
    ├── flask.md
    └── thymeleaf.md
```

---

## work-tracker

### 출퇴근 자동 기록 + 월간 업무 보고서 생성기

매일 출퇴근 시점에 Claude Code 세션, Git 커밋, Auto Memory를 자동 수집해 일간 요약을 만들고, 월간 보고서를 생성합니다. 터미널을 여러 번 열고 닫아도 하루의 컨텍스트가 자동으로 유지됩니다.

### 커맨드

| 커맨드 | 설명 |
| --- | --- |
| `/clockin` | 출근 기록. Git HEAD 스냅샷 저장 |
| `/clockout` | 퇴근 기록. 오늘 전체 세션 수집 → 일간 요약 자동 생성 |
| `/recap` | 월간 보고서 생성. 날짜 범위 지정 가능 |

### 플로우 (work-tracker)

```text
/clockin → 하루 작업 → /clockout → 일간 요약 자동 생성 → /recap → 월간 보고서
```

### 주요 기능

- **자동 컨텍스트 수집** — Claude Code 세션 JSONL + Git diff + Auto Memory를 자동 파싱
- **일간 요약 생성** — 퇴근 시 당일 전체 작업 내용을 자동 요약
- **월간 보고서** — 목표/핵심결과/잘한점/보완계획 4열 테이블 형식으로 생성
- **다양한 내보내기** — 로컬 .md, Notion, Obsidian, Confluence 지원
- **보안 필터링** — API 키, .env, 인증서 등 민감 정보 자동 마스킹

### 사용 예시 (work-tracker)

```text
"출근 찍어줘"
"퇴근할게, 오늘 코드리뷰 2건 했어"
"저번 달 업무 정리해줘"
/recap 2025-02
/recap q1
```

### 파일 구조 (work-tracker)

```text
work-tracker/
├── SKILL.md
├── README.md
├── references/
└── scripts/
    └── collect_sessions.py
```

---

## 설치

### Claude Code (npx)

프로젝트 루트에서 아래 명령어로 원하는 스킬을 바로 설치할 수 있습니다.

```bash
# keycloak-auth-generator 설치
npx degit jayounglee92/my-claude-skill/keycloak-auth-generator .claude/skills/keycloak-auth-generator

# fe-sdd-tdd 설치
npx degit jayounglee92/my-claude-skill/fe-sdd-tdd .claude/skills/fe-sdd-tdd

# work-tracker 설치
npx degit jayounglee92/my-claude-skill/work-tracker .claude/skills/work-tracker
```

> `npx degit`은 Git 없이 GitHub 서브폴더만 다운로드합니다. npm에 아무것도 배포할 필요 없이 바로 사용 가능합니다.

### Claude.ai

1. 각 스킬 폴더를 ZIP으로 압축
2. **Settings → Features → Skills**에서 업로드

### 수동 설치

```bash
cp -r fe-sdd-tdd/ your-project/.claude/skills/
cp -r keycloak-auth-generator/ your-project/.claude/skills/
cp -r work-tracker/ your-project/.claude/skills/
```

## 라이선스

MIT
