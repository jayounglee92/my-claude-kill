#!/usr/bin/env python3
"""
archive_old_logs.py — 오래된 일간 요약을 월별 archive로 병합한다.

Usage:
    python3 archive_old_logs.py <work_logs_dir> <archive_after_months>

/clockin 시 자동으로 호출된다.
"""

import os
import sys
import glob
from datetime import datetime, timedelta


def archive_month(month_dir, daily_files):
    """월별 일간 요약 파일들을 하나의 archive.md로 병합"""
    # 디렉토리 이름에서 연/월 추출
    parts = month_dir.rstrip("/").split("/")
    year_month = f"{parts[-2]}년 {parts[-1]}월"

    archive_lines = [f"# {year_month} 월간 아카이브\n"]

    for filepath in sorted(daily_files):
        filename = os.path.basename(filepath)
        date_str = filename.replace(".md", "")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError:
            continue

        # "오늘 한 일" 섹션만 추출하여 요약
        summary = extract_brief(content)
        archive_lines.append(f"\n## {date_str}")
        archive_lines.append(summary)

    archive_path = os.path.join(month_dir, "archive.md")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write("\n".join(archive_lines))

    # 원본 일간 파일 삭제
    deleted = 0
    for filepath in daily_files:
        try:
            os.remove(filepath)
            deleted += 1
        except OSError:
            pass

    return archive_path, deleted


def extract_brief(content):
    """일간 요약에서 핵심만 추출 (2~3줄)"""
    lines = content.split("\n")
    brief_lines = []
    in_section = False

    for line in lines:
        # "오늘 한 일" 또는 서비스별 섹션 시작
        if line.startswith("### [") or line.startswith("### 코드 외"):
            in_section = True
            brief_lines.append(line.replace("### ", "- "))
            continue

        if in_section:
            # 다음 ## 헤더가 나오면 섹션 종료
            if line.startswith("## ") and not line.startswith("### "):
                in_section = False
                continue

            # 주요 항목만 추출 (- 로 시작하는 첫 번째 레벨만)
            stripped = line.strip()
            if stripped.startswith("- ") and not stripped.startswith("  -"):
                brief_lines.append(stripped)

    # 최대 10줄
    return "\n".join(brief_lines[:10]) if brief_lines else "- (요약 없음)"


def run_archive(work_logs_dir, archive_after_months):
    """메인 아카이브 로직"""
    logs_dir = os.path.expanduser(work_logs_dir)
    threshold = datetime.now() - timedelta(days=archive_after_months * 30)

    archived = []

    # YYYY/MM 구조의 디렉토리 탐색
    for year_dir in sorted(glob.glob(os.path.join(logs_dir, "[0-9][0-9][0-9][0-9]"))):
        for month_dir in sorted(glob.glob(os.path.join(year_dir, "[0-9][0-9]"))):
            # 이미 archive됨
            if os.path.exists(os.path.join(month_dir, "archive.md")):
                continue

            # 일간 요약 파일들
            daily_files = [
                f
                for f in glob.glob(os.path.join(month_dir, "*.md"))
                if os.path.basename(f) != "archive.md"
            ]

            if not daily_files:
                continue

            # 가장 최근 파일의 수정 시간 확인
            latest_mtime = max(os.path.getmtime(f) for f in daily_files)
            latest_date = datetime.fromtimestamp(latest_mtime)

            if latest_date < threshold:
                archive_path, deleted = archive_month(month_dir, daily_files)
                archived.append(
                    {"month_dir": month_dir, "files_merged": deleted, "archive": archive_path}
                )

    return archived


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python3 archive_old_logs.py <work_logs_dir> <archive_after_months>",
            file=sys.stderr,
        )
        sys.exit(1)

    results = run_archive(sys.argv[1], int(sys.argv[2]))
    if results:
        for r in results:
            print(
                f"Archived {r['month_dir']}: {r['files_merged']} files → {r['archive']}"
            )
    else:
        print("No directories to archive.")
