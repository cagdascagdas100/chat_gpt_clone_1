import unittest

from defans_mania_reference.quiz_engine import Question
from defans_mania_reference.session_controller import QuizSessionController


def questions():
    return {
        "q1": Question("q1", "Q1", ("a", "b", "c", "d"), "b"),
        "q2": Question("q2", "Q2", ("e", "f", "g", "h"), "g"),
    }


class SessionControllerTests(unittest.TestCase):
    def test_wrong_question_returns_without_skipping_other_pending_question(self):
        controller = QuizSessionController.create(questions())
        controller.submit_answer("q1", "a")
        self.assertEqual(controller.pending_question_ids(), ("q2", "q1"))
        controller.submit_answer("q2", "g")
        self.assertEqual(controller.pending_question_ids(), ("q1",))
        controller.submit_answer("q1", "b")
        self.assertTrue(controller.is_finished)
        self.assertEqual(controller.run.summary().total_wrong_attempts, 1)

    def test_required_correct_streak_resets_after_another_wrong(self):
        controller = QuizSessionController.create(
            {"q1": questions()["q1"]}, required_correct_after_wrong=2
        )
        controller.submit_answer("q1", "a")
        controller.submit_answer("q1", "b")
        self.assertFalse(controller.is_finished)
        controller.submit_answer("q1", "c")
        controller.submit_answer("q1", "b")
        self.assertFalse(controller.is_finished)
        controller.submit_answer("q1", "b")
        self.assertTrue(controller.is_finished)
        self.assertEqual(controller.run.summary().total_wrong_attempts, 2)

    def test_shuffled_display_index_is_resolved_to_immutable_option_id(self):
        controller = QuizSessionController.create({"q1": questions()["q1"]})
        attempt = controller.submit_display_index("q1", ("d", "b", "a", "c"), 1)
        self.assertTrue(attempt.is_correct)
        self.assertTrue(controller.is_finished)

    def test_stale_question_event_is_rejected(self):
        controller = QuizSessionController.create(questions())
        with self.assertRaises(RuntimeError):
            controller.submit_answer("q2", "g")
        self.assertEqual(controller.pending_question_ids(), ("q1", "q2"))
        self.assertEqual(controller.run.attempts, [])

    def test_displayed_option_set_must_match_question(self):
        controller = QuizSessionController.create({"q1": questions()["q1"]})
        with self.assertRaises(ValueError):
            controller.submit_display_index("q1", ("a", "b", "c", "x"), 1)
        self.assertEqual(controller.run.attempts, [])


if __name__ == "__main__":
    unittest.main()
