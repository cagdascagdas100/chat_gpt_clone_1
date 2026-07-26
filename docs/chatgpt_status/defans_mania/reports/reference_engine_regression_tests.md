# Defans Mania reference-engine regression tests

Status: PASS

Execution environment: Python 3, isolated local verification

Command:

```text
python -m unittest -v tests/test_defans_mania_reference.py
```

Result:

```text
Ran 9 tests
OK
```

Covered invariants:

1. Correctness is decided by immutable option ID, not the displayed A/B/C/D position.
2. A wrong displayed option cannot be accepted because of option shuffling.
3. A wrong attempt remains recorded after a later correct answer.
4. Required consecutive correct answers restart after another wrong answer.
5. Questions answered correctly on the first attempt are excluded from the wrong-question list.
6. Multiple wrong attempts are counted exactly.
7. Wrong-only retest contains each previously wrong question once.
8. Pagination of 15 records at 6 per page produces pages 1-6, 7-12 and 13-15 without skipping page 2.
9. Unknown questions and invalid option IDs are rejected.

Boundary: this validates the reference algorithm and regression contract. It does not prove the unavailable Defans Mania desktop source currently implements the same logic.
