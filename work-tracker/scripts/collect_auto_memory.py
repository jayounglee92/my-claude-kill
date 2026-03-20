#!/usr/bin/env python3
"""
collect_auto_memory.py — clockin 이후 변경된 Auto Memory 파일을 수집한다.

Usage:
    python3 collect_auto_memory.py <clockin_time_iso> <claude_projects_dir>

Output:
    JSON으로 변경된 memory 파일 내용을 stdout에 출력한다.
"""

import json
import os
import sys
import glob
from datetime import datetime, timezone


def collect_memory_changes(clockin_time_iso, claude_projects_dir):
    """clockin 이후 수정된 auto memory 파일 수집"""
    try:
        clockin_time = datetime.fromisoformat(
            clockin_time_iso.replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        return {"error": f"Invalid clockin time: {clockin_time_iso}", "changes": []}

    projects_dir = os.path.expanduser(claude_projects_dir)
    memory_pattern = os.path.join(projects_dir, "*", "memory", "*.md")
    changes = []

    for md_file in glob.glob(memory_pattern):
        try:
            mtime = datetime.fromtimestamp(
                os.path.getmtime(md_file), tz=timezone.utc
            )

            if clockin_time.tzinfo is None:
                clockin_compare = clockin_time.replace(tzinfo=timezone.utc)
            else:
                clockin_compare = clockin_time

            if mtime <= clockin_compare:
                continue

            with open(md_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            changes.append(
                {
                    "file": md_file,
                    "filename": os.path.basename(md_file),
                    "modified": mtime.isoformat(),
                    "content": content[:2000],  # 최대 2000자
                    "size_bytes": len(content),
                }
            )
        except (IOError, OSError):
            continue

    return {"total_changes": len(changes), "changes": changes}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python3 collect_auto_memory.py <clockin_time_iso> <claude_projects_dir>",
            file=sys.stderr,
        )
        sys.exit(1)

    result = collect_memory_changes(sys.argv[1], sys.argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
