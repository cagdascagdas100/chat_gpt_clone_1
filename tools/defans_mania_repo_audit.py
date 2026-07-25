from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "defans_mania_repo_audit.json"

MARKERS = [
    re.compile(r"Quiz\s+Ergebnis", re.I),
    re.compile(r"FALSCHE\+OPTION", re.I),
    re.compile(r"ALLE\s+FRAGEN", re.I),
    re.compile(r"quiz_result_", re.I),
    re.compile(r"Falsche\s+Antworten", re.I),
    re.compile(r"Falsche\s+Fragen", re.I),
    re.compile(r"Wortquiz", re.I),
    re.compile(r"Erklaerung:\s*No:", re.I),
    re.compile(r"kelimesinin\s+artikeli\s+nedir", re.I),
]
RISK_PATTERNS = [
    re.compile(r"(?:current|result|quiz)?_?page\s*\+=\s*2", re.I),
    re.compile(r"page\w*\s*=\s*page\w*\s*\+\s*2", re.I),
    re.compile(r"\[\s*::\s*2\s*\]"),
    re.compile(r"range\s*\([^\)]*,\s*2\s*\)", re.I),
    re.compile(r"slice\s*\(", re.I),
    re.compile(r"\.skip\s*\(", re.I),
    re.compile(r"\.take\s*\(", re.I),
    re.compile(r"shuffle|random\.shuffle", re.I),
    re.compile(r"correct\w*(?:index|option|answer)", re.I),
    re.compile(r"selected\w*(?:index|option|answer)", re.I),
    re.compile(r"wrong\w*(?:count|questions|answers|attempt)", re.I),
    re.compile(r"falsch\w*(?:count|fragen|antwort)", re.I),
]
TEXT_EXTS = {".py", ".pyw", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".cs", ".cpp", ".c", ".h", ".hpp", ".html", ".htm", ".json", ".xml", ".txt", ".md", ".ps1"}
EXCLUDED = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "site-packages", "packages"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_matches(text: str, patterns: list[re.Pattern[str]], limit: int = 160) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    for number, line in enumerate(text.splitlines(), 1):
        for pattern in patterns:
            if pattern.search(line):
                found.append({"line": number, "pattern": pattern.pattern, "text": line.strip()[:500]})
                break
        if len(found) >= limit:
            break
    return found


def audit_result(path: Path, text: str) -> dict[str, object]:
    def first_int(pattern: str) -> int | None:
        m = re.search(pattern, text, re.I | re.M)
        return int(m.group(1)) if m else None

    wrong_answers = first_int(r"Falsche\s+Antworten:\s*(\d+)")
    wrong_questions = first_int(r"Falsche\s+Fragen:\s*(\d+)")
    score = first_int(r"^Score:\s*(\d+)")
    numbers = [int(x) for x in re.findall(r"(?m)^\s*(\d+)\)\s+", text)]
    wrong_counts = [int(x) for x in re.findall(r"Falsch:\s*(\d+)x", text, re.I)]
    ids = [x.strip() for x in re.findall(r"Erklaerung:\s*No:([^\r\n]+)", text, re.I)]
    duplicate_ids = sorted({x for x in ids if ids.count(x) > 1})
    wrong_sum = sum(wrong_counts)
    contiguous = numbers == list(range(1, len(numbers) + 1))
    return {
        "path": str(path.relative_to(ROOT)),
        "score": score,
        "header_wrong_answers": wrong_answers,
        "header_wrong_questions": wrong_questions,
        "rendered_question_blocks": len(numbers),
        "rendered_question_numbers": numbers,
        "per_question_wrong_counts": wrong_counts,
        "per_question_wrong_sum": wrong_sum,
        "duplicate_explanation_ids": duplicate_ids,
        "checks": {
            "wrong_answers_matches_sum": None if wrong_answers is None else wrong_answers == wrong_sum,
            "wrong_questions_matches_blocks": None if wrong_questions is None else wrong_questions == len(numbers),
            "each_block_has_wrong_count": len(numbers) == len(wrong_counts),
            "explanation_ids_unique": not duplicate_ids,
            "rendered_numbers_are_contiguous": contiguous,
        },
    }


def main() -> int:
    candidates: list[dict[str, object]] = []
    result_audits: list[dict[str, object]] = []
    unreadable: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTS or path.stat().st_size > 5 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            unreadable.append(str(path.relative_to(ROOT)))
            continue

        marker_hits = line_matches(text, MARKERS, 100)
        if marker_hits:
            candidates.append({
                "path": str(path.relative_to(ROOT)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "marker_matches": marker_hits,
                "risk_matches": line_matches(text, RISK_PATTERNS, 160),
            })

        if path.name.lower().startswith("quiz_result_") and path.suffix.lower() == ".txt":
            result_audits.append(audit_result(path, text))

    failed_results = [x for x in result_audits if any(v is False for v in x["checks"].values())]
    report = {
        "status": "completed",
        "scope": "repository_only",
        "source_candidate_count": len(candidates),
        "result_file_count": len(result_audits),
        "failed_result_audit_count": len(failed_results),
        "source_candidates": candidates,
        "result_audits": result_audits,
        "unreadable": unreadable,
        "external_machine_scanned": False,
        "source_modified": False,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "scope", "source_candidate_count", "result_file_count", "failed_result_audit_count")}, ensure_ascii=False))
    for item in candidates:
        print(f"CANDIDATE {item['path']} risk_matches={len(item['risk_matches'])}")
    for item in failed_results:
        print(f"RESULT_FAIL {item['path']} checks={json.dumps(item['checks'], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
