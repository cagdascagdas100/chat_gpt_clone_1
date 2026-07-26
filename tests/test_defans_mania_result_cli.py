import json
from pathlib import Path
import tempfile
import unittest

from tools.defans_mania_validate_result import main


VALID_TEXT = """Score: 200
Falsche Antworten: 3
Falsche Fragen: 2

1) Eins
Falsch: 2x
Erklaerung: No:q1

2) Zwei
Falsch: 0x
Erklaerung: No:q2

3) Drei
Falsch: 1x
Erklaerung: No:q3
"""


class ResultValidatorCliTests(unittest.TestCase):
    def test_writes_normalized_snapshot_and_contiguous_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "quiz_result_2.txt"
            output = root / "audit.json"
            source.write_text(VALID_TEXT, encoding="utf-8")

            exit_code = main([str(source), "--page-size", "1", "--output", str(output)])
            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["total_wrong_attempts"], 3)
            self.assertEqual(payload["unique_wrong_questions"], 2)
            self.assertEqual(
                payload["pages"],
                [
                    {"page_number": 1, "question_ids": ["q1"]},
                    {"page_number": 2, "question_ids": ["q3"]},
                ],
            )

    def test_returns_nonzero_for_inconsistent_header(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "quiz_result_bad.txt"
            source.write_text(
                VALID_TEXT.replace("Falsche Antworten: 3", "Falsche Antworten: 9"),
                encoding="utf-8",
            )
            self.assertEqual(main([str(source)]), 2)

    def test_utf8_bom_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "quiz_result_bom.txt"
            source.write_text(VALID_TEXT, encoding="utf-8-sig")
            self.assertEqual(main([str(source)]), 0)


if __name__ == "__main__":
    unittest.main()
