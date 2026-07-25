from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Question:
    question_id: str
    prompt: str
    option_ids: tuple[str, ...]
    correct_option_id: str

    def __post_init__(self) -> None:
        if not self.question_id:
            raise ValueError("question_id must not be empty")
        if self.correct_option_id not in self.option_ids:
            raise ValueError("correct_option_id must be one of option_ids")
        if len(set(self.option_ids)) != len(self.option_ids):
            raise ValueError("option_ids must be unique")


@dataclass(frozen=True)
class Attempt:
    question_id: str
    selected_option_id: str
    correct_option_id: str
    is_correct: bool
    attempt_number: int


@dataclass
class QuestionProgress:
    wrong_attempts: int = 0
    correct_attempts_after_first_wrong: int = 0
    completed: bool = False


@dataclass(frozen=True)
class WrongQuestionSummary:
    question_id: str
    wrong_attempts: int


@dataclass(frozen=True)
class TestSummary:
    total_wrong_attempts: int
    unique_wrong_questions: int
    wrong_questions: tuple[WrongQuestionSummary, ...]


@dataclass
class TestRun:
    questions: Mapping[str, Question]
    required_correct_after_wrong: int = 1
    attempts: list[Attempt] = field(default_factory=list)
    progress: dict[str, QuestionProgress] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.required_correct_after_wrong < 1:
            raise ValueError("required_correct_after_wrong must be at least 1")
        if not self.questions:
            raise ValueError("questions must not be empty")
        self.progress = {question_id: QuestionProgress() for question_id in self.questions}

    def submit_answer(self, question_id: str, selected_option_id: str) -> Attempt:
        question = self.questions.get(question_id)
        if question is None:
            raise KeyError(f"unknown question_id: {question_id}")
        if selected_option_id not in question.option_ids:
            raise ValueError("selected_option_id must be one of the question option IDs")

        state = self.progress[question_id]
        if state.completed:
            raise RuntimeError("question is already completed")

        is_correct = selected_option_id == question.correct_option_id
        attempt = Attempt(
            question_id=question_id,
            selected_option_id=selected_option_id,
            correct_option_id=question.correct_option_id,
            is_correct=is_correct,
            attempt_number=1 + sum(a.question_id == question_id for a in self.attempts),
        )
        self.attempts.append(attempt)

        if is_correct:
            if state.wrong_attempts == 0:
                state.completed = True
            else:
                state.correct_attempts_after_first_wrong += 1
                state.completed = (
                    state.correct_attempts_after_first_wrong
                    >= self.required_correct_after_wrong
                )
        else:
            state.wrong_attempts += 1
            state.correct_attempts_after_first_wrong = 0
            state.completed = False

        return attempt

    def is_complete(self) -> bool:
        return all(state.completed for state in self.progress.values())

    def pending_question_ids(self) -> tuple[str, ...]:
        return tuple(
            question_id
            for question_id, state in self.progress.items()
            if not state.completed
        )

    def summary(self) -> TestSummary:
        wrong_counts: dict[str, int] = {}
        for attempt in self.attempts:
            if not attempt.is_correct:
                wrong_counts[attempt.question_id] = wrong_counts.get(attempt.question_id, 0) + 1

        wrong_questions = tuple(
            WrongQuestionSummary(question_id=question_id, wrong_attempts=count)
            for question_id, count in self.questions_ordered_wrong_counts(wrong_counts)
        )
        return TestSummary(
            total_wrong_attempts=sum(wrong_counts.values()),
            unique_wrong_questions=len(wrong_counts),
            wrong_questions=wrong_questions,
        )

    def questions_ordered_wrong_counts(
        self, wrong_counts: Mapping[str, int]
    ) -> Iterable[tuple[str, int]]:
        for question_id in self.questions:
            count = wrong_counts.get(question_id)
            if count:
                yield question_id, count

    def build_wrong_only_retest(self) -> "TestRun":
        wrong_ids = {attempt.question_id for attempt in self.attempts if not attempt.is_correct}
        if not wrong_ids:
            raise ValueError("previous run contains no wrong questions")
        selected = {
            question_id: question
            for question_id, question in self.questions.items()
            if question_id in wrong_ids
        }
        return TestRun(
            questions=selected,
            required_correct_after_wrong=self.required_correct_after_wrong,
        )


def option_id_for_display_index(
    displayed_option_ids: Sequence[str], selected_display_index: int
) -> str:
    if selected_display_index < 0 or selected_display_index >= len(displayed_option_ids):
        raise IndexError("selected_display_index is outside displayed options")
    return displayed_option_ids[selected_display_index]


def paginate(items: Sequence[object], page_size: int) -> tuple[tuple[object, ...], ...]:
    if page_size < 1:
        raise ValueError("page_size must be at least 1")
    return tuple(
        tuple(items[start : start + page_size])
        for start in range(0, len(items), page_size)
    )


def validate_saved_summary(summary: TestSummary) -> None:
    summed_wrong_attempts = sum(item.wrong_attempts for item in summary.wrong_questions)
    if summary.total_wrong_attempts != summed_wrong_attempts:
        raise ValueError("total wrong attempts do not match per-question wrong counts")
    if summary.unique_wrong_questions != len(summary.wrong_questions):
        raise ValueError("unique wrong-question total does not match rendered entries")
    if any(item.wrong_attempts < 1 for item in summary.wrong_questions):
        raise ValueError("wrong-question list must contain only questions with wrong attempts")
