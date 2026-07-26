import unittest

from defans_mania_reference.quiz_engine import (
    Question,
    TestRun,
    option_id_for_display_index,
    paginate,
    validate_saved_summary,
)


def make_questions():
    return {
        "q1": Question("q1", "Question 1", ("a", "b", "c", "d"), "b"),
        "q2": Question("q2", "Question 2", ("e", "f", "g", "h"), "g"),
        "q3": Question("q3", "Question 3", ("i", "j", "k", "l"), "i"),
    }


class QuizEngineTests(unittest.TestCase):
    def test_correctness_uses_option_id_not_display_position(self):
        question = make_questions()["q1"]
        displayed = ("d", "b", "a", "c")
        selected_id = option_id_for_display_index(displayed, 1)
        run = TestRun({"q1": question})
        attempt = run.submit_answer("q1", selected_id)
        self.assertTrue(attempt.is_correct)
        self.assertTrue(run.is_complete())

    def test_wrong_display_position_is_not_accepted(self):
        question = make_questions()["q1"]
        displayed = ("b", "d", "a", "c")
        selected_id = option_id_for_display_index(displayed, 1)
        run = TestRun({"q1": question})
        attempt = run.submit_answer("q1", selected_id)
        self.assertFalse(attempt.is_correct)
        self.assertFalse(run.is_complete())

    def test_wrong_attempt_is_preserved_after_later_correct_answer(self):
        run = TestRun({"q1": make_questions()["q1"]})
        run.submit_answer("q1", "a")
        run.submit_answer("q1", "b")
        summary = run.summary()
        self.assertEqual(summary.total_wrong_attempts, 1)
        self.assertEqual(summary.unique_wrong_questions, 1)
        self.assertEqual(summary.wrong_questions[0].question_id, "q1")
        self.assertEqual(summary.wrong_questions[0].wrong_attempts, 1)
        validate_saved_summary(summary)

    def test_required_correct_count_restarts_after_new_wrong_answer(self):
        run = TestRun({"q1": make_questions()["q1"]}, required_correct_after_wrong=2)
        run.submit_answer("q1", "a")
        run.submit_answer("q1", "b")
        self.assertFalse(run.is_complete())
        run.submit_answer("q1", "a")
        run.submit_answer("q1", "b")
        self.assertFalse(run.is_complete())
        run.submit_answer("q1", "b")
        self.assertTrue(run.is_complete())
        self.assertEqual(run.summary().total_wrong_attempts, 2)

    def test_correct_only_questions_are_excluded_from_wrong_list(self):
        questions = make_questions()
        run = TestRun(questions)
        run.submit_answer("q1", "b")
        run.submit_answer("q2", "e")
        run.submit_answer("q2", "g")
        run.submit_answer("q3", "i")
        summary = run.summary()
        self.assertEqual([item.question_id for item in summary.wrong_questions], ["q2"])
        self.assertEqual(summary.unique_wrong_questions, 1)
        self.assertEqual(summary.total_wrong_attempts, 1)

    def test_multiple_wrong_attempts_are_counted_exactly(self):
        run = TestRun({"q1": make_questions()["q1"]})
        run.submit_answer("q1", "a")
        run.submit_answer("q1", "c")
        run.submit_answer("q1", "d")
        run.submit_answer("q1", "b")
        summary = run.summary()
        self.assertEqual(summary.total_wrong_attempts, 3)
        self.assertEqual(summary.wrong_questions[0].wrong_attempts, 3)
        validate_saved_summary(summary)

    def test_wrong_only_retest_contains_unique_previous_wrong_questions(self):
        questions = make_questions()
        run = TestRun(questions)
        run.submit_answer("q1", "a")
        run.submit_answer("q1", "c")
        run.submit_answer("q1", "b")
        run.submit_answer("q2", "g")
        run.submit_answer("q3", "j")
        run.submit_answer("q3", "i")
        retest = run.build_wrong_only_retest()
        self.assertEqual(tuple(retest.questions), ("q1", "q3"))
        self.assertEqual(len(retest.questions), 2)
        self.assertEqual(retest.attempts, [])

    def test_pagination_never_skips_the_second_page(self):
        items = tuple(range(1, 16))
        pages = paginate(items, 6)
        self.assertEqual(pages[0], (1, 2, 3, 4, 5, 6))
        self.assertEqual(pages[1], (7, 8, 9, 10, 11, 12))
        self.assertEqual(pages[2], (13, 14, 15))
        self.assertEqual(tuple(item for page in pages for item in page), items)

    def test_unknown_or_invalid_option_is_rejected(self):
        run = TestRun({"q1": make_questions()["q1"]})
        with self.assertRaises(KeyError):
            run.submit_answer("missing", "a")
        with self.assertRaises(ValueError):
            run.submit_answer("q1", "not-an-option")


if __name__ == "__main__":
    unittest.main()
