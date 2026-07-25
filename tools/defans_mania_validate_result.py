#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from defans_mania_reference.legacy_result import (
    LegacyResultError,
    normalized_legacy_snapshot,
    paginate_wrong_rows,
    parse_legacy_result,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Defans Mania quiz_result_*.txt and emit a normalized audit snapshot."
    )
    parser.add_argument("result_file", type=Path)
    parser.add_argument("--page-size", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.page_size < 1:
        parser.error("--page-size must be at least 1")

    try:
        text = args.result_file.read_text(encoding="utf-8-sig")
        result = parse_legacy_result(text)
    except (OSError, UnicodeError, LegacyResultError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    pages = paginate_wrong_rows(result, args.page_size)
    snapshot = normalized_legacy_snapshot(result)
    snapshot["source_file"] = str(args.result_file)
    snapshot["page_size"] = args.page_size
    snapshot["pages"] = [
        {
            "page_number": index,
            "question_ids": [row.question_id for row in page],
        }
        for index, page in enumerate(pages, start=1)
    ]

    payload = json.dumps(snapshot, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    print(
        f"VALID: wrong_answers={result.total_wrong_attempts} "
        f"wrong_questions={result.wrong_question_count} pages={len(pages)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
