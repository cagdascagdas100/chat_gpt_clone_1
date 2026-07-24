from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence


_HEADER_PATTERNS = {
    "score": re.compile(r"(?im)^\s*Score\s*:\s*(\d+)\s*$"),
    "wrong_answers": re.compile(r"(?im)^\s*Falsche\s+Antworten\s*:\s*(\d+)\s*$"),
    "wrong_questions": re.compile(r"(?im)^\s*Falsche\s+Fragen\s*:\s*(\d+)\s*$"),
}
_QUESTION_START = re.compile(r"(?m)^\s*(\d+)\)\s+(.+?)\s*$")
_WRONG_COUNT = re.compile(r"(?im)Falsch\s*:\s*(\d+)x")
_EXPLANATION_ID = re.compile(r"(?im)Erklaerung\s*:\s*No\s*:\s*([^\r\n]+)")


@dataclass(frozen=True)
class LegacyQuestionRow:
    display_number: int
    prompt: str
    question_id: str
    wrong_attempts: int
    raw_block: str


@dataclass(frozen=True)
class LegacyResult:
    score: int | None
    header_wrong_answers: int
    header_wrong_questions: int
    questions: tuple[LegacyQuestionRow, ...]

    @property
    def total_wrong_attempts(self) -> int:
        return sum(row.wrong_attempts for row in self.questions)

    @property
    def wrong_question_count(self) -> int:
        return sum(row.wrong_attempts > 0 for row in self.questions)

    def wrong_only_rows(self) -> tuple[LegacyQuestionRow, ...]:
        return tuple(row for row in self.questions if row.wrong_attempts > 0)


@dataclass(frozen=True)
class WrongOnlyRetestManifest:
    source_run_id: str
    question_ids: tuple[str, ...]


class LegacyResultError(ValueError):
    pass


def _header_value(text: str, key: str, *, required: bool = True) -> int | None:
    match = _HEADER_PATTERNS[key].search(text)
    if match:
        return int(match.group(1))
    if required:
        raise LegacyResultError(f"missing required header: {key}")
    return None


def _question_blocks(text: str) -> Iterable[tuple[re.Match[str], str]]:
    starts = list(_QUESTION_START.finditer(text))
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        yield match, text[match.start() : end].strip()


def parse_legacy_result(text: str) -> LegacyResult:
    if not text.strip():
        raise LegacyResultError("result text is empty")

    rows: list[LegacyQuestionRow] = []
    seen_ids: set[str] = set()
    for expected_index, (start, block) in enumerate(_question_blocks(text), start=1):
        display_number = int(start.group(1))
        if display_number != expected_index:
            raise LegacyResultError(
                f"question numbers are not contiguous: expected {expected_index}, got {display_number}"
            )

        wrong_match = _WRONG_COUNT.search(block)
        if not wrong_match:
            raise LegacyResultError(f"question {display_number} is missing Falsch: Nx")
        wrong_attempts = int(wrong_match.group(1))

        id_match = _EXPLANATION_ID.search(block)
        question_id = id_match.group(1).strip() if id_match else f"legacy-{display_number}"
        if question_id in seen_ids:
            raise LegacyResultError(f"duplicate question ID: {question_id}")
        seen_ids.add(question_id)

        rows.append(
            LegacyQuestionRow(
                display_number=display_number,
                prompt=start.group(2).strip(),
                question_id=question_id,
                wrong_attempts=wrong_attempts,
                raw_block=block,
            )
        )

    result = LegacyResult(
        score=_header_value(text, "score", required=False),
        header_wrong_answers=int(_header_value(text, "wrong_answers")),
        header_wrong_questions=int(_header_value(text, "wrong_questions")),
        questions=tuple(rows),
    )
    validate_legacy_result(result)
    return result


def validate_legacy_result(result: LegacyResult) -> None:
    if result.header_wrong_answers != result.total_wrong_attempts:
        raise LegacyResultError(
            "Falsche Antworten header does not equal the sum of per-question wrong counts"
        )
    if result.header_wrong_questions != result.wrong_question_count:
        raise LegacyResultError(
            "Falsche Fragen header does not equal the number of questions with at least one wrong attempt"
        )
    if any(row.wrong_attempts < 0 for row in result.questions):
        raise LegacyResultError("wrong-attempt counts cannot be negative")


def paginate_wrong_rows(
    result: LegacyResult, page_size: int
) -> tuple[tuple[LegacyQuestionRow, ...], ...]:
    if page_size < 1:
        raise ValueError("page_size must be at least 1")
    rows = result.wrong_only_rows()
    return tuple(
        tuple(rows[start : start + page_size])
        for start in range(0, len(rows), page_size)
    )


def build_wrong_only_manifest(
    source_run_id: str, rows: Sequence[LegacyQuestionRow]
) -> WrongOnlyRetestManifest:
    if not source_run_id:
        raise ValueError("source_run_id must not be empty")
    unique_ids = tuple(dict.fromkeys(row.question_id for row in rows if row.wrong_attempts > 0))
    if not unique_ids:
        raise ValueError("previous test contains no wrong questions")
    return WrongOnlyRetestManifest(source_run_id=source_run_id, question_ids=unique_ids)


def normalized_legacy_snapshot(result: LegacyResult) -> dict[str, object]:
    """Return a non-lossy aggregate snapshot.

    Legacy result files contain aggregate wrong counts rather than the full attempt ledger.
    The migration therefore records provenance explicitly and never invents synthetic attempts.
    """
    return {
        "schema_version": 1,
        "provenance": "legacy_aggregate",
        "score": result.score,
        "total_wrong_attempts": result.total_wrong_attempts,
        "unique_wrong_questions": result.wrong_question_count,
        "wrong_questions": [
            {
                "question_id": row.question_id,
                "display_number": row.display_number,
                "prompt": row.prompt,
                "wrong_attempts": row.wrong_attempts,
            }
            for row in result.wrong_only_rows()
        ],
    }
