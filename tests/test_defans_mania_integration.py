import dataclasses
import unittest

from defans_mania_reference.integration_contract import (
    FinishAction,
    PersistedAttempt,
    SavedTestRun,
    build_result_pages,
    build_wrong_only_retest_from_saved,
    finish_options,
    flatten_result_pages,
    replay_attempts,
    save_test_run,
)
from defans_mania_reference.quiz_engine import Question, TestRun


STAMP = "2026-07-14T10:00:00Z"


def question(question_id: str, correct: str = "b") -> Question:
    return Question(
        question_id=question_id,
        prompt=f"Prompt {question_id}",
        option_ids=("a", "b", "c", "d"),
        correct_option_id=correct,
    )


def completed_saved_run() -> tuple[SavedTestRun, dict[str, Question]]:
    questions = {"q1": question("q1"), "q2": question("q2")}
    run = TestRun(questions, required_correct_after_wrong=2)
    run.submit_answer("q1", "a")
    run.submit_answer("q2", "b")
    run.submit_answer("q1", "c")
    run.submit_answer("q1", "b")
    run.submit_answer("q1", "b")
    return save_test_run(run, "run-1", occurred_at=STAMP), questions


class IntegrationContractTests(unittest.TestCase):
    def test_json_round_trip_preserves_event_ledger_and_summary(self):
        saved, _ = completed_saved_run()
        restored = SavedTestRun.from_json(saved.to_json())
        self.assertEqual(restored, saved)
        self.assertEqual(restored.summary().total_wrong_attempts, 2)
        self.assertEqual(restored.summary().unique_wrong_questions, 1)
        self.assertEqual(restored.summary().wrong_questions[0].question_id, "q1")

    def test_persisted_correctness_cannot_disagree_with_option_ids(self):
        with self.assertRaises(ValueError):
            PersistedAttempt(
                event_id="run:q1:1",
                run_id="run",
                question_id="q1",
                selected_option_id="a",
                correct_option_id="b",
                is_correct=True,
                attempt_number=1,
                occurred_at=STAMP,
            )

    def test_attempt_numbers_must_be_contiguous_per_question(self):
        attempt = PersistedAttempt(
            event_id="run:q1:2",
            run_id="run",
            question_id="q1",
            selected_option_id="a",
            correct_option_id="b",
            is_correct=False,
            attempt_number=2,
            occurred_at=STAMP,
        )
        with self.assertRaises(ValueError):
            SavedTestRun(
                run_id="run",
                question_ids=("q1",),
                required_correct_after_wrong=1,
                attempts=(attempt,),
            )

    def test_saved_summary_is_derived_only_from_immutable_attempts(self):
        saved, _ = completed_saved_run()
        summary = saved.summary()
        self.assertEqual(summary.total_wrong_attempts, 2)
        self.assertEqual(summary.unique_wrong_questions, 1)
        self.assertEqual(summary.wrong_questions[0].wrong_attempts, 2)

    def test_result_pages_contain_only_wrong_questions_and_never_skip_page_two(self):
        questions = {f"q{i}": question(f"q{i}") for i in range(1, 18)}
        run = TestRun(questions)
        wrong_ids = {f"q{i}" for i in range(1, 16)}
        for question_id in questions:
            if question_id in wrong_ids:
                run.submit_answer(question_id, "a")
            run.submit_answer(question_id, "b")
        saved = save_test_run(run, "run-pages", occurred_at=STAMP)
        pages = build_result_pages(saved, questions, page_size=6)
        self.assertEqual([page.page_number for page in pages], [1, 2, 3])
        self.assertEqual([len(page.rows) for page in pages], [6, 6, 3])
        flattened = flatten_result_pages(pages)
        self.assertEqual(tuple(row.question_id for row in flattened), tuple(f"q{i}" for i in range(1, 16)))
        self.assertNotIn("q16", {row.question_id for row in flattened})
        self.assertNotIn("q17", {row.question_id for row in flattened})

    def test_wrong_only_finish_option_is_present_and_enabled(self):
        saved, _ = completed_saved_run()
        options = {option.action: option for option in finish_options(saved)}
        option = options[FinishAction.RETEST_PREVIOUS_WRONG_ONLY]
        self.assertTrue(option.enabled)
        self.assertIn("yanlış", option.label.lower())

    def test_wrong_only_finish_option_is_disabled_when_test_is_perfect(self):
        questions = {"q1": question("q1")}
        run = TestRun(questions)
        run.submit_answer("q1", "b")
        saved = save_test_run(run, "perfect", occurred_at=STAMP)
        options = {option.action: option for option in finish_options(saved)}
        option = options[FinishAction.RETEST_PREVIOUS_WRONG_ONLY]
        self.assertFalse(option.enabled)
        self.assertIsNotNone(option.disabled_reason)

    def test_wrong_only_retest_uses_unique_wrong_ids_and_fresh_attempt_history(self):
        saved, questions = completed_saved_run()
        retest = build_wrong_only_retest_from_saved(saved, questions)
        self.assertEqual(tuple(retest.questions), ("q1",))
        self.assertEqual(retest.attempts, [])
        self.assertEqual(retest.required_correct_after_wrong, 2)

    def test_replay_rejects_changed_answer_key(self):
        saved, questions = completed_saved_run()
        changed = dict(questions)
        changed["q1"] = question("q1", correct="c")
        with self.assertRaises(ValueError):
            replay_attempts(saved, changed)

    def test_duplicate_event_id_is_rejected(self):
        saved, _ = completed_saved_run()
        duplicated = dataclasses.replace(saved.attempts[1], event_id=saved.attempts[0].event_id)
        with self.assertRaises(ValueError):
            dataclasses.replace(saved, attempts=(saved.attempts[0], duplicated))


if __name__ == "__main__":
    unittest.main()
