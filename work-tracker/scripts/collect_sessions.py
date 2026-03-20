#!/usr/bin/env python3
"""
collect_sessions.py — clockin 이후 생성된 세션 JSONL을 파싱하여 업무 컨텍스트를 수집한다.

Usage:
    python3 collect_sessions.py <clockin_time_iso> <claude_projects_dir> [existing_sessions_file]

Output:
    JSON으로 수집된 세션 데이터를 stdout에 출력한다.
"""

import json
import os
import re
import sys
import glob
from datetime import datetime, timezone

# ── 보안 필터링 ──

# 시크릿 패턴 (대소문자 무시)
_SECRET_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_\-]?key|private[_\-]?key|credential|"
    r"auth[_\-]?token|access[_\-]?key|bearer|client[_\-]?secret)"
    r"[\s]*[=:\"']",
    re.IGNORECASE,
)

# 민감 파일 경로 패턴
_SENSITIVE_FILE_PATTERN = re.compile(
    r"\.(env|env\..+|pem|key|p12|pfx|jks|keystore|cer|crt)$", re.IGNORECASE
)

# 내부 네트워크 IP
_INTERNAL_IP_PATTERN = re.compile(
    r"(10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)"
)

# DB 접속 문자열
_DB_URI_PATTERN = re.compile(
    r"(mongodb|postgres|mysql|redis|amqp)://[^\s]+", re.IGNORECASE
)

# 코드 블록 패턴
_CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")


def contains_secret(text):
    """텍스트에 시크릿 패턴이 포함되어 있는지 확인"""
    if not text:
        return False
    return bool(
        _SECRET_PATTERN.search(text)
        or _DB_URI_PATTERN.search(text)
    )


def sanitize_text(text):
    """텍스트에서 민감 정보를 마스킹"""
    if not text:
        return text
    # 시크릿이 포함된 텍스트는 전체 스킵
    if contains_secret(text):
        return "[민감 정보 포함 — 스킵됨]"
    # 내부 IP 마스킹
    text = _INTERNAL_IP_PATTERN.sub("[내부주소]", text)
    # DB URI 마스킹
    text = _DB_URI_PATTERN.sub("[DB접속정보]", text)
    # 코드 블록 제거 (코드 내용 대신 표시만)
    code_blocks = _CODE_BLOCK_PATTERN.findall(text)
    if code_blocks:
        text = _CODE_BLOCK_PATTERN.sub(
            f"[코드 블록 — 보안상 생략]", text
        )
    return text


def is_sensitive_file(filepath):
    """민감한 파일 경로인지 확인"""
    if not filepath:
        return False
    basename = os.path.basename(filepath)
    return bool(_SENSITIVE_FILE_PATTERN.search(basename)) or basename.startswith(".env")


def sanitize_filepath(filepath):
    """파일 경로에서 홈 디렉토리 등 민감 부분 제거"""
    if not filepath:
        return filepath
    if is_sensitive_file(filepath):
        return "[민감 설정 파일]"
    # 홈 디렉토리 이하 경로를 상대경로로 변환
    home = os.path.expanduser("~")
    if filepath.startswith(home):
        filepath = filepath[len(home):]
        if filepath.startswith("/"):
            filepath = filepath[1:]
    return filepath


def parse_iso_time(iso_str):
    """ISO 8601 시간 문자열을 datetime으로 파싱"""
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def load_existing_sessions(filepath):
    """clockin 시점에 기록된 기존 세션 목록을 로드"""
    if not filepath or not os.path.exists(filepath):
        return set()
    with open(filepath, "r") as f:
        return set(line.strip() for line in f if line.strip())


def collect_session_data(jsonl_path, max_message_chars=500):
    """단일 JSONL 파일에서 세션 데이터를 추출"""
    session = {
        "session_id": os.path.basename(jsonl_path).replace(".jsonl", ""),
        "file_path": jsonl_path,
        "start_time": None,
        "end_time": None,
        "user_messages": [],
        "assistant_summaries": [],
        "tools_used": {},
        "files_edited": [],
        "activity_timeline": [],  # 시간별 활동 기록
        "total_messages": 0,
        "total_tool_calls": 0,
    }

    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                timestamp = entry.get("timestamp")
                if timestamp:
                    if session["start_time"] is None:
                        session["start_time"] = timestamp
                    session["end_time"] = timestamp

                entry_type = entry.get("type")

                if entry_type == "message":
                    session["total_messages"] += 1
                    role = entry.get("role", "")
                    content = entry.get("content", "")

                    # content가 리스트인 경우 (tool_use 등 포함)
                    if isinstance(content, list):
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                        content = " ".join(text_parts)
                    elif not isinstance(content, str):
                        content = str(content)

                    if role == "user":
                        sanitized = sanitize_text(content[:max_message_chars])
                        session["user_messages"].append(sanitized)
                        # 타임라인에 사용자 요청 기록
                        if timestamp:
                            session["activity_timeline"].append({
                                "time": timestamp,
                                "type": "user_request",
                                "summary": sanitize_text(content[:200]),
                            })
                    elif role == "assistant":
                        # assistant 응답은 짧게 요약, 코드 블록 제거
                        sanitized = sanitize_text(content[:max_message_chars])
                        session["assistant_summaries"].append(sanitized)

                elif entry_type == "tool_use":
                    session["total_tool_calls"] += 1
                    tool_name = entry.get("toolName", entry.get("name", "unknown"))
                    session["tools_used"][tool_name] = (
                        session["tools_used"].get(tool_name, 0) + 1
                    )

                    # 파일 편집 추적
                    tool_input = entry.get("toolInput", entry.get("input", {}))
                    if isinstance(tool_input, dict):
                        file_path = tool_input.get(
                            "file_path", tool_input.get("path", "")
                        )
                        if file_path and tool_name in (
                            "Edit",
                            "Write",
                            "str_replace",
                            "create_file",
                        ):
                            # 민감 파일은 마스킹
                            safe_path = sanitize_filepath(file_path)
                            if safe_path not in session["files_edited"]:
                                session["files_edited"].append(safe_path)

                        # Bash 명령어 보안 필터링
                        command = tool_input.get("command", "")
                        if tool_name == "Bash" and contains_secret(command):
                            command = "[민감 명령어 — 스킵됨]"

                        # 타임라인에 도구 사용 기록
                        if timestamp:
                            timeline_entry = {
                                "time": timestamp,
                                "type": "tool_use",
                                "tool": tool_name,
                            }
                            if file_path:
                                timeline_entry["file"] = sanitize_filepath(file_path)
                            session["activity_timeline"].append(timeline_entry)

    except (IOError, OSError) as e:
        session["error"] = str(e)

    return session


def collect_all_sessions(clockin_time_iso, claude_projects_dir, existing_sessions_file=None):
    """clockin 이후 생성/수정된 모든 세션을 수집"""
    clockin_time = parse_iso_time(clockin_time_iso)
    if not clockin_time:
        return {"error": f"Invalid clockin time: {clockin_time_iso}", "sessions": []}

    # 기존 세션 목록
    existing = load_existing_sessions(existing_sessions_file)

    # 프로젝트 디렉토리 확장
    projects_dir = os.path.expanduser(claude_projects_dir)
    if not os.path.exists(projects_dir):
        return {
            "error": f"Projects directory not found: {projects_dir}",
            "sessions": [],
        }

    sessions = []
    jsonl_files = glob.glob(os.path.join(projects_dir, "*", "*.jsonl")) + glob.glob(
        os.path.join(projects_dir, "*", "*", "*.jsonl")
    )

    for jsonl_path in jsonl_files:
        # 기존 세션 제외
        if jsonl_path in existing:
            continue

        # 파일 수정 시간 확인
        try:
            mtime = datetime.fromtimestamp(
                os.path.getmtime(jsonl_path), tz=timezone.utc
            )
            # clockin_time이 timezone-aware가 아닐 수 있으므로 비교를 위해 처리
            if clockin_time.tzinfo is None:
                clockin_compare = clockin_time.replace(tzinfo=timezone.utc)
            else:
                clockin_compare = clockin_time

            if mtime < clockin_compare:
                continue
        except OSError:
            continue

        session_data = collect_session_data(jsonl_path)
        if session_data["total_messages"] > 0:  # 빈 세션은 제외
            sessions.append(session_data)

    # 시간 순 정렬
    sessions.sort(key=lambda s: s.get("start_time") or "")

    return {
        "clockin_time": clockin_time_iso,
        "total_sessions": len(sessions),
        "total_messages": sum(s["total_messages"] for s in sessions),
        "total_tool_calls": sum(s["total_tool_calls"] for s in sessions),
        "sessions": sessions,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python3 collect_sessions.py <clockin_time_iso> <claude_projects_dir> [existing_sessions_file]",
            file=sys.stderr,
        )
        sys.exit(1)

    clockin_time = sys.argv[1]
    projects_dir = sys.argv[2]
    existing_file = sys.argv[3] if len(sys.argv) > 3 else None

    result = collect_all_sessions(clockin_time, projects_dir, existing_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
