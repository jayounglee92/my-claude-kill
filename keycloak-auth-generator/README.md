# 🔐 Keycloak Auth Generator

프레임워크별 Keycloak SSO 인증 코드를 자동 생성하는 Claude Skill입니다.

## 지원 프레임워크

| 프레임워크 | 인증 방식 | UI 디자인 시스템 |
|-----------|----------|-----------------|
| **Next.js** | Auth.js v5 + Keycloak Provider | shadcn/ui, MUI, Ant Design, Tailwind |
| **Vue 3** | @josempgon/vue-keycloak | Vuetify, PrimeVue, Element Plus, Naive UI |
| **Nuxt 3** | sidebase/nuxt-auth | Nuxt UI, Vuetify, PrimeVue |
| **FastAPI** | PyJWT (JWT) | Swagger UI, Jinja2+Bootstrap |
| **Django** | mozilla-django-oidc | crispy-forms+Bootstrap, Tailwind |
| **Flask** | Authlib | Bootstrap 5, Tailwind |
| **Thymeleaf** | Spring Security OAuth2 Client | Bootstrap 5, Tailwind |

## 생성되는 코드

- ✅ 로그인 페이지 (선택한 디자인 시스템 적용)
- ✅ 로그아웃 (Keycloak 세션까지 종료)
- ✅ 토큰 자동 재발급 (refresh token rotation)
- ✅ 인증 미들웨어/가드
- ✅ 역할 기반 접근제어 (RBAC)
- ✅ 타입 정의 (TypeScript)
- ✅ 환경변수 파일 (.env)
- ✅ Docker 기반 로컬 Keycloak (선택)

## 설치 방법

### Claude.ai
1. 이 레포의 ZIP 파일을 다운로드
2. **Settings → Features → Skills**에서 업로드

### Claude Code
```bash
# 프로젝트의 .claude/skills/ 디렉토리에 복사
cp -r keycloak-auth-generator .claude/skills/
```

## 사용법

새 대화에서 아래처럼 요청하면 됩니다:

```
Next.js 프로젝트에 Keycloak SSO 연동해줘
```

스킬이 자동으로 트리거되어 필요한 정보를 물어봅니다:

1. **프레임워크** — 자동 감지 또는 직접 선택
2. **Keycloak 정보** — URL, Realm, Client ID, Client Secret
3. **디자인 시스템** — 프레임워크별 인기 UI 라이브러리 추천
4. **Keycloak 환경** — Docker(로컬 테스트) / 기존 서버 / 코드만

## 전체 플로우

```
사용자: "Keycloak 연동해줘"
  ↓
Step 1: 정보 수집 (프레임워크, Keycloak URL, Realm, Client ID)
  ↓
Step 2: 디자인 시스템 선택 (shadcn/ui, Vuetify 등)
  ↓
Step 3: 코드 생성 (auth, login, dashboard, middleware 등)
  ↓
Step 4: 패키지 자동 설치 (npm install / pip install)
  ↓
Step 5: Keycloak 환경 선택
  ├── 🐳 Docker → docker-compose.yml + realm 설정 자동 생성 + 실행
  ├── 🏢 기존 서버 → Admin Console 설정 안내
  └── 📄 코드만 → placeholder 값으로 생성
  ↓
Step 6: 최종 요약 (파일 목록, 실행 방법, 테스트 계정)
```

## Docker로 로컬 테스트 (Keycloak 서버 없이)

Docker 옵션을 선택하면 아래가 자동 생성됩니다:

- `docker-compose.yml` — Keycloak 서버
- `keycloak/realm-export.json` — Realm, Client, 테스트 사용자 설정

```bash
docker compose up -d   # Keycloak 서버 시작
npm run dev            # 앱 시작
# → http://localhost:3000 에서 testuser / 1234 로 로그인 테스트
```

## 주의사항

- `keycloak-connect` (Node.js 어댑터)는 deprecated입니다. 사용하지 마세요.
- `keycloakify` 대신 각 프레임워크의 공식 권장 방식을 사용합니다.
- Auth.js **v5** 기준입니다 (NextAuth v4와 설정 방식이 다릅니다).
- `flask-oidc`는 유지보수가 중단되었습니다. `Authlib`을 사용합니다.

## 파일 구조

```
keycloak-auth-generator/
├── SKILL.md                    ← 스킬 메인 (영어)
├── README.md                   ← 이 파일 (한글)
└── references/
    ├── nextjs.md               ← Next.js + Auth.js v5
    ├── vue3.md                 ← Vue 3 + vue-keycloak
    ├── nuxt3.md                ← Nuxt 3 + sidebase/nuxt-auth
    ├── fastapi.md              ← FastAPI + PyJWT
    ├── django.md               ← Django + mozilla-django-oidc
    ├── flask.md                ← Flask + Authlib
    └── thymeleaf.md            ← Spring Boot + Spring Security
```

## 라이선스

MIT
