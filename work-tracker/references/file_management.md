# 파일 관리 정책

<!-- Internal policy doc. Korean content is intentional — describes archive format for Korean output files. -->

`/clockin` 실행 시 자동으로 호출되는 파일 정리 로직.

## 3단계 수명 관리

### Hot (0~2개월)
- 개별 일간 요약 .md 파일 원본 보관
- `/recap`가 직접 읽는 대상
- 경로: `~/.claude/work-logs/YYYY/MM/YYYY-MM-DD.md`

### Archive (3개월+)
- 해당 월의 모든 일간 .md를 1개 archive.md로 병합
- 각 날짜의 "오늘 한 일" 섹션만 핵심 요약으로 남김
- 원본 일간 .md 파일은 삭제
- 경로: `~/.claude/work-logs/YYYY/MM/archive.md`

### Cold (1년+)
- `delete_archive_after_months > 0`이면 해당 기간 후 archive 삭제
- 0이면 영구 보관 (부담 없음 — 연간 ~60KB)

## 정리 로직

```bash
# /clockin 시 아래 로직을 실행

현재 날짜 = today
archive_threshold = today - (archive_after_months * 30일)

for each 월별 디렉토리 in ~/.claude/work-logs/YYYY/MM/:
  if archive.md가 이미 존재하면:
    skip (이미 archive됨)
  
  해당 월의 가장 최근 .md 파일의 수정 시간을 확인
  if 가장 최근 파일 < archive_threshold:
    모든 일간 .md를 읽어서 archive.md로 병합
    원본 .md 파일 삭제
```

## archive.md 형식

```markdown
# 2025년 1월 월간 아카이브

## 2025-01-02 (목)
- [서비스A] 로그인 페이지 초기 설정, 외부 인증 연동 시작
- [서비스B] 검색 필터링 버그 수정

## 2025-01-03 (금)
- [서비스A] 입력 폼 UI 구현 완료
- 코드리뷰: my-service-b MR !130

...
```

각 날짜는 2~3줄의 핵심 요약만 남긴다. 상세 내용(세션 요약, 커밋 목록, 미해결 이슈 등)은 제거.

## reports/ 디렉토리

최종 보고서는 `~/.claude/work-logs/reports/`에 별도 보관한다.
`keep_monthly_reports: true`이면 이 디렉토리는 절대 정리하지 않는다.
