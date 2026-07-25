import unittest

from defans_mania_reference.legacy_result import (
    LegacyResultError,
    build_wrong_only_manifest,
    normalized_legacy_snapshot,
    paginate_wrong_rows,
    parse_legacy_result,
)


def sample_result() -> str:
    return """Score: 300
Falsche Antworten: 4
Falsche Fragen: 3

1) Frage eins
Falsch: 2x
Erklaerung: No:q1

2) Frage zwei
Falsch: 0x
Erklaerung: No:q2

3) Frage drei
Falsch: 1x
Erklaerung: No:q3

4) Frage vier
Falsch: 1x
Erklaerung: No:q4
"""


class LegacyResultTests(unittest.TestCase):
    def test_parses_and_filters_only_questions_with_wrong_attempts(self):
        result = parse_legacy_result(sample_result())
        self.assertEqual(result.total_wrong_attempts, 4)
        self.assertEqual(result.wrong_question_count, 3)
        self.assertEqual(
            [row.question_id for row in result.wrong_only_rows()],
            ["q1", "q3", "q4"],
        )

    def test_filter_happens_before_pagination(self):
        result = parse_legacy_result(sample_result())
        pages = paginate_wrong_rows(result, 2)
        self.assertEqual([[row.question_id for row in page] for page in pages], [["q1", "q3"], ["q4"]])
        flattened = [row.question_id for page in pages for row in page]
        self.assertEqual(flattened, ["q1", "q3", "q4"])

    def test_wrong_only_manifest_is_unique_and_links_previous_run(self):
        result = parse_legacy_result(sample_result())
        manifest = build_wrong_only_manifest("run-17", result.questions)
        self.assertEqual(manifest.source_run_id, "run-17")
        self.assertEqual(manifest.question_ids, ("q1", "q3", "q4"))

    def test_normalized_snapshot_does_not_invent_attempts(self):
        snapshot = normalized_legacy_snapshot(parse_legacy_result(sample_result()))
        self.assertEqual(snapshot["provenance"], "legacy_aggregate")
        self.assertNotIn("attempts", snapshot)
        self.assertEqual(snapshot["total_wrong_attempts"], 4)
        self.assertEqual(snapshot["unique_wrong_questions"], 3)

    def test_rejects_wrong_answer_header_mismatch(self):
        text = sample_result().replace("Falsche Antworten: 4", "Falsche Antworten: 99")
        with self.assertRaisesRegex(LegacyResultError, "Falsche Antworten"):
            parse_legacy_result(text)

    def test_rejects_wrong_question_header_mismatch(self):
        text = sample_result().replace("Falsche Fragen: 3", "Falsche Fragen: 4")
        with self.assertRaisesRegex(LegacyResultError, "Falsche Fragen"):
            parse_legacy_result(text)

    def test_rejects_missing_page_question_number(self):
        text = sample_result().replace("3) Frage drei", "4) Frage drei", 1)
        with self.assertRaisesRegex(LegacyResultError, "not contiguous"):
            parse_legacy_result(text)

    def test_rejects_duplicate_question_ids(self):
        text = sample_result().replace("Erklaerung: No:q4", "Erklaerung: No:q3")
        with self.assertRaisesRegex(LegacyResultError, "duplicate question ID"):
            parse_legacy_result(text)

    def test_rejects_question_without_wrong_count(self):
        text = sample_result().replace("Falsch: 1x\nErklaerung: No:q4", "Erklaerung: No:q4", 1)
        with self.assertRaisesRegex(LegacyResultError, "missing Falsch"):
            parse_legacy_result(text)


if __name__ == "__main__":
    unittest.main()
