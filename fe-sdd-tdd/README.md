# fe-sdd-tdd

**Frontend Spec-Driven Development + Test-Driven Development** 스킬

Claude Code / Claude.ai에서 프론트엔드 기능을 구현할 때, **Spec 작성 → 테스트 작성 → 구현** 순서를 강제하는 워크플로우 스킬입니다.

## 이 스킬이 하는 일

```
Spec이 있나? → 없으면 만든다 → 테스트 먼저 작성 → 최소 구현 → 리팩터링 → 완료 체크
```

Kent C. Dodds의 **Testing Trophy** 패턴을 기반으로, 기능 복잡도에 따라 테스트 전략을 자동 추천합니다.

```
        /\
       /E2E\          ← 핵심 플로우만 (소수)
      /------\
     /Integration\    ← 가장 넓은 층 (다수)
    /------------\
   / Unit Tests   \   ← TDD 사이클 드라이버
  /----------------\
 / Static Analysis  \  ← 항상 실행 (TS)
/--------------------\
```

## 주요 기능

### Spec 자동 생성 (STEP 0)
- Spec 디렉토리를 **자동 탐색** (docs/specs, specs, docs 등 순회)
- 못 찾으면 사용자에게 질문
- **기능 유형별 맞춤 질문** (폼, 데이터 표시, 신규 페이지, 버그 수정 등)
- **코드베이스 자동 분석** — 재사용 컴포넌트, API 패턴, 타입, 테스트 도구 탐지
- 인터뷰 답변 + 코드 분석을 조합해서 Spec 초안 생성
- 사용자 확인 → 수정 루프 → 확정

### TDD 사이클 (STEP 2-6)
- **RED**: Spec에서 테스트 케이스 도출 → 실패하는 테스트 작성
- **GREEN**: 테스트를 통과시키는 최소 구현
- **Integration**: MSW로 API 모킹한 통합 테스트 (Testing Trophy 핵심)
- **Refactor**: 5항목 체크리스트 (side effect, hook 추출, 타입 중복, 100줄 초과, 테스트 호환)
- **E2E**: 핵심 유저 플로우만 (Playwright)

### 구현 중 의사결정 (STEP 7)
- TODO/FIXME 자동 스캔
- Spec 대비 미구현 항목 탐지
- 사용자에게 선택지 제시 (구현 vs 다음 이터레이션 연기)

### 완료 체크리스트 (STEP 8)
- **반응형**: MANDATORY — 모든 기능에서 3 브레이크포인트 검증 필수
- **접근성, i18n, Storybook, 문서화, 에러 모니터링**: 사용자 확인 후 선택

### 언어 규칙
- 스킬 문서: 영어
- 사용자 대면 커뮤니케이션: **사용자의 언어에 맞춤** (자동 감지)
- 코드: 영어
- UI 텍스트: 프로젝트 로케일에 맞춤

## 파일 구조

```
fe-sdd-tdd/
├── SKILL.md                          ← 핵심 워크플로우 (~350줄)
└── references/
    ├── spec-template.md              ← Spec 생성 시 참조하는 템플릿
    ├── test-examples.md              ← Unit/Integration 테스트 코드 예시
    ├── msw-and-playwright.md         ← MSW 세팅 + Playwright 명령어 레퍼런스
    └── checklists.md                 ← a11y + responsive 체크리스트
```

SKILL.md는 500줄 이내로 유지하고, 상세 레퍼런스는 `references/`에 분리했습니다. 각 STEP에서 필요할 때만 해당 reference를 읽습니다.

## 설치

### Claude Code
```bash
# 프로젝트의 .claude/skills/ 디렉토리에 복사
cp -r fe-sdd-tdd/ your-project/.claude/skills/fe-sdd-tdd/
```

### Claude.ai
Settings → Skills에서 SKILL.md와 references/ 폴더를 업로드합니다.

## 사용법

아래와 같이 요청하면 스킬이 자동으로 트리거됩니다:

- "댓글 위젯 만들어줘"
- "회원가입 기능 구현"
- "EVT-021 구현해줘" (feature ID)
- "spec 만들어줘"
- "TDD로 개발하자"

## 개발 과정

이 스킬은 Claude.ai 대화를 통해 반복적으로 개발 + 테스트되었습니다.

### v1: 초기 버전
- 기존에 가지고 있던 SDD+TDD 스킬을 기반으로 시작
- Spec이 이미 존재한다고 가정하는 구조

### v2: Spec 생성 플로우 추가
- Spec이 없을 때 사용자 인터뷰 + 코드베이스 분석으로 자동 생성
- 기능 유형별 맞춤 질문 세트 설계
- 구현 중 의사결정 분기점 (STEP 7) 추가
- 완료 후 체크리스트 (STEP 8) 추가

### v3: 실전 테스트 — 댓글 위젯
- 가상 Next.js 프로젝트에서 STEP 0~8 전체 플로우 실행
- 비밀댓글 기능 추가 요청 → Spec 수정 루프 검증
- 발견된 개선점: 리팩터링 체크리스트, TODO 자동 스캔, a11y/반응형 상세화

### v4: 실전 테스트 — Todo 리스트
- 두 번째 테스트로 범용성 검증
- STEP 0-0 (Spec Directory Discovery) 추가 — 하드코딩 경로 제거
- 사용자 지정 경로(`docs/`) 지원 확인

### v5: 영어 전환 + 구조 최적화
- 전체 스킬을 영어로 재작성
- Language Rule 추가 (스킬은 영어, 사용자 대면은 사용자 언어)
- YAML frontmatter 파싱 에러 수정
- 863줄 → 352줄로 축소 (references/ 분리)
- 반응형을 필수(MANDATORY)로 변경

### v6: 실전 테스트 — 회원가입 플로우
- 세 번째 테스트로 복잡한 시나리오 검증 (폼 + 실시간 검증 + 인증)
- zod 스키마 테스트, onBlur 이메일 중복 체크, next-auth 자동 로그인
- STEP 7에서 gap 발견 → 미니 RED/GREEN 사이클로 해결

## 테스트 결과 요약

| 테스트 | 기능 | 복잡도 | Unit | Integration | E2E | 총 테스트 |
|--------|------|--------|------|-------------|-----|----------|
| #1 | 댓글 위젯 (CRUD + 비밀댓글) | High | 13 | 8 | 2 | 23 |
| #2 | Todo 리스트 (CRUD) | Medium | 12 | 5 | 1 | 18 |
| #3 | 회원가입 (폼 + 인증) | High | 19 | 5 | 2 | 26 |

세 번의 테스트에서 스킬 플로우가 일관되게 동작하는 것을 확인했습니다.

## 라이선스

MIT
