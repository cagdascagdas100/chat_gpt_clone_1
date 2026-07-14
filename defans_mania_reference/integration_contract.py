from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Mapping, Sequence

from .quiz_engine import (
    Attempt,
    Question,
    TestRun,
    TestSummary,
    WrongQuestionSummary,
    paginate,
    validate_saved_summary,
)

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PersistedAttempt:
    event_id: str
    run_id: str
    question_id: str
    selected_option_id: str
    correct_option_id: str
    is_correct: bool
    attempt_number: int
    occurred_at: str

    def __post_init__(self) -> None:
        if not self.event_id or not self.run_id or not self.question_id:
            raise ValueError("event_id, run_id and question_id must not be empty")
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be at least 1")
        if self.is_correct != (self.selected_option_id == self.correct_option_id):
            raise ValueError("stored is_correct does not match immutable option IDs")
        if not self.occurred_at:
            raise ValueError("occurred_at must not be empty")


@dataclass(frozen=True)
class SavedTestRun:
    run_id: str
    question_ids: tuple[str, ...]
    required_correct_after_wrong: int
    attempts: tuple[PersistedAttempt, ...]
    source_run_id: str | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        if not self.run_id:
            raise ValueError("run_id must not be empty")
        if not self.question_ids or len(set(self.question_ids)) != len(self.question_ids):
            raise ValueError("question_ids must be non-empty and unique")
        if self.required_correct_after_wrong < 1:
            raise ValueError("required_correct_after_wrong must be at least 1")

        event_ids: set[str] = set()
        next_attempt_number = {question_id: 1 for question_id in self.question_ids}
        for attempt in self.attempts:
            if attempt.event_id in event_ids:
                raise ValueError(f"duplicate event_id: {attempt.event_id}")
            event_ids.add(attempt.event_id)
            if attempt.run_id != self.run_id:
                raise ValueError("attempt run_id does not match saved test run_id")
            if attempt.question_id not in next_attempt_number:
                raise ValueError(f"attempt references unknown question_id: {attempt.question_id}")
            expected = next_attempt_number[attempt.question_id]
            if attempt.attempt_number != expected:
                raise ValueError(
                    f"non-contiguous attempt_number for {attempt.question_id}: "
                    f"expected {expected}, got {attempt.attempt_number}"
                )
            next_attempt_number[attempt.question_id] = expected + 1

    def summary(self) -> TestSummary:
        wrong_counts: dict[str, int] = {}
        for attempt in self.attempts:
            if not attempt.is_correct:
                wrong_counts[attempt.question_id] = wrong_counts.get(attempt.question_id, 0) + 1

        wrong_questions = tuple(
            WrongQuestionSummary(question_id=question_id, wrong_attempts=wrong_counts[question_id])
            for question_id in self.question_ids
            if question_id in wrong_counts
        )
        summary = TestSummary(
            total_wrong_attempts=sum(wrong_counts.values()),
            unique_wrong_questions=len(wrong_questions),
            wrong_questions=wrong_questions,
        )
        validate_saved_summary(summary)
        return summary

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> "SavedTestRun":
        payload = json.loads(raw)
        attempts = tuple(PersistedAttempt(**item) for item in payload.get("attempts", []))
        return cls(
            run_id=payload["run_id"],
            question_ids=tuple(payload["question_ids"]),
            required_correct_after_wrong=int(payload["required_correct_after_wrong"]),
            attempts=attempts,
            source_run_id=payload.get("source_run_id"),
            schema_version=int(payload.get("schema_version", SCHEMA_VERSION)),
        )


@dataclass(frozen=True)
class ResultRow:
    question_id: str
    prompt: str
    wrong_attempts: int


@dataclass(frozen=True)
class ResultPage:
    page_number: int
    total_pages: int
    rows: tuple[ResultRow, ...]


class FinishAction(str, Enum):
    NEW_TEST = "new_test"
    END_GAME = "end_game"
    REPEAT_SAME_TEST = "repeat_same_test"
    RETEST_PREVIOUS_WRONG_ONLY = "retest_previous_wrong_only"


@dataclass(frozen=True)
class FinishOption:
    action: FinishAction
    label: str
    enabled: bool = True
    disabled_reason: str | None = None


def save_test_run(
    run: TestRun,
    run_id: str,
    *,
    occurred_at: str,
    source_run_id: str | None = None,
) -> SavedTestRun:
    if not run_id:
        raise ValueError("run_id must not be empty")
    if not occurred_at:
        raise ValueError("occurred_at must not be empty")

    persisted = tuple(
        PersistedAttempt(
            event_id=f"{run_id}:{attempt.question_id}:{attempt.attempt_number}",
            run_id=run_id,
            question_id=attempt.question_id,
            selected_option_id=attempt.selected_option_id,
            correct_option_id=attempt.correct_option_id,
            is_correct=attempt.is_correct,
            attempt_number=attempt.attempt_number,
            occurred_at=occurred_at,
        )
        for attempt in run.attempts
    )
    return SavedTestRun(
        run_id=run_id,
        source_run_id=source_run_id,
        question_ids=tuple(run.questions),
        required_correct_after_wrong=run.required_correct_after_wrong,
        attempts=persisted,
    )


def build_result_pages(
    saved: SavedTestRun,
    questions: Mapping[str, Question],
    page_size: int,
) -> tuple[ResultPage, ...]:
    summary = saved.summary()
    rows: list[ResultRow] = []
    for item in summary.wrong_questions:
        question = questions.get(item.question_id)
        if question is None:
            raise KeyError(f"missing question metadata: {item.question_id}")
        rows.append(
            ResultRow(
                question_id=item.question_id,
                prompt=question.prompt,
                wrong_attempts=item.wrong_attempts,
            )
        )

    raw_pages = paginate(rows, page_size)
    total_pages = len(raw_pages)
    return tuple(
        ResultPage(page_number=index + 1, total_pages=total_pages, rows=tuple(page))
        for index, page in enumerate(raw_pages)
    )


def flatten_result_pages(pages: Sequence[ResultPage]) -> tuple[ResultRow, ...]:
    if not pages:
        return ()
    total_pages = pages[0].total_pages
    if total_pages != len(pages):
        raise ValueError("page count metadata does not match page collection")
    for expected_number, page in enumerate(pages, start=1):
        if page.page_number != expected_number or page.total_pages != total_pages:
            raise ValueError("result pages are not contiguous or have inconsistent metadata")
    return tuple(row for page in pages for row in page.rows)


def build_wrong_only_retest_from_saved(
    saved: SavedTestRun,
    questions: Mapping[str, Question],
) -> TestRun:
    wrong_ids = tuple(item.question_id for item in saved.summary().wrong_questions)
    if not wrong_ids:
        raise ValueError("previous test contains no wrong questions")
    selected = {question_id: questions[question_id] for question_id in wrong_ids}
    return TestRun(
        questions=selected,
        required_correct_after_wrong=saved.required_correct_after_wrong,
    )


def finish_options(saved: SavedTestRun) -> tuple[FinishOption, ...]:
    has_wrong_questions = saved.summary().unique_wrong_questions > 0
    return (
        FinishOption(FinishAction.NEW_TEST, "Yeni test oluştur"),
        FinishOption(FinishAction.END_GAME, "Oyunu bitir"),
        FinishOption(FinishAction.REPEAT_SAME_TEST, "Aynı testi yeniden yap"),
        FinishOption(
            FinishAction.RETEST_PREVIOUS_WRONG_ONLY,
            "Sadece önceki testte yanlış yaptığım soruları yeniden sor",
            enabled=has_wrong_questions,
            disabled_reason=None if has_wrong_questions else "Önceki testte yanlış soru yok",
        ),
    )


def replay_attempts(saved: SavedTestRun, questions: Mapping[str, Question]) -> TestRun:
    run_questions = {question_id: questions[question_id] for question_id in saved.question_ids}
    run = TestRun(
        questions=run_questions,
        required_correct_after_wrong=saved.required_correct_after_wrong,
    )
    for stored in saved.attempts:
        produced: Attempt = run.submit_answer(stored.question_id, stored.selected_option_id)
        if (
            produced.correct_option_id != stored.correct_option_id
            or produced.is_correct != stored.is_correct
            or produced.attempt_number != stored.attempt_number
        ):
            raise ValueError("saved attempt cannot be reproduced from current question data")
    return run
