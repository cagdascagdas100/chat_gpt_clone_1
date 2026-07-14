from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .quiz_engine import Attempt, Question, TestRun, option_id_for_display_index


@dataclass
class QuizSessionController:
    """Round-robin UI controller that keeps each pending question exactly once."""

    run: TestRun
    question_order: tuple[str, ...]
    _pending: deque[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.question_order:
            raise ValueError("question_order must not be empty")
        if len(set(self.question_order)) != len(self.question_order):
            raise ValueError("question_order must contain unique question IDs")
        if set(self.question_order) != set(self.run.questions):
            raise ValueError("question_order must contain every run question exactly once")
        self._pending = deque(self.question_order)

    @classmethod
    def create(
        cls,
        questions: Mapping[str, Question],
        *,
        required_correct_after_wrong: int = 1,
        question_order: Sequence[str] | None = None,
    ) -> "QuizSessionController":
        ordered = tuple(question_order) if question_order is not None else tuple(questions)
        return cls(
            run=TestRun(
                questions=dict(questions),
                required_correct_after_wrong=required_correct_after_wrong,
            ),
            question_order=ordered,
        )

    @property
    def current_question_id(self) -> str | None:
        return self._pending[0] if self._pending else None

    @property
    def is_finished(self) -> bool:
        return not self._pending and self.run.is_complete()

    def pending_question_ids(self) -> tuple[str, ...]:
        return tuple(self._pending)

    def submit_answer(self, question_id: str, selected_option_id: str) -> Attempt:
        current = self.current_question_id
        if current is None:
            raise RuntimeError("test is already finished")
        if question_id != current:
            raise RuntimeError(
                f"stale or out-of-order answer event: expected {current}, got {question_id}"
            )

        self._pending.popleft()
        attempt = self.run.submit_answer(question_id, selected_option_id)
        if not self.run.progress[question_id].completed:
            self._pending.append(question_id)
        self._validate_queue_invariant()
        return attempt

    def submit_display_index(
        self,
        question_id: str,
        displayed_option_ids: Sequence[str],
        selected_display_index: int,
    ) -> Attempt:
        question = self.run.questions.get(question_id)
        if question is None:
            raise KeyError(f"unknown question_id: {question_id}")
        if len(displayed_option_ids) != len(question.option_ids) or set(displayed_option_ids) != set(
            question.option_ids
        ):
            raise ValueError("displayed options do not match the immutable question option IDs")
        selected_option_id = option_id_for_display_index(
            displayed_option_ids, selected_display_index
        )
        return self.submit_answer(question_id, selected_option_id)

    def _validate_queue_invariant(self) -> None:
        pending_from_run = set(self.run.pending_question_ids())
        pending_from_queue = set(self._pending)
        if len(self._pending) != len(pending_from_queue):
            raise RuntimeError("pending queue contains duplicate question IDs")
        if pending_from_queue != pending_from_run:
            raise RuntimeError("pending queue and run progress are inconsistent")
