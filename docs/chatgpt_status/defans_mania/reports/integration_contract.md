# Defans Mania quiz integration contract

Status: implementation contract complete; desktop application source not present in the accessible repository.

## 1. Stable identity rules

- Every question must have an immutable `question_id`.
- Every answer option must have an immutable `option_id`.
- Shuffling changes only the displayed order; it must never change the stored correct `option_id`.
- A click event must carry `question_id`, the displayed option-ID array, and selected display index.
- The controller resolves the selected index to `option_id` and compares it with `correct_option_id`.
- Stale events for a question that is no longer on screen must be rejected.

## 2. Attempt ledger

Each submitted answer is an append-only event:

```text
schema_version
run_id
event_id
question_id
selected_option_id
correct_option_id
is_correct
attempt_number
occurred_at
```

`is_correct` must equal `selected_option_id == correct_option_id`. A later correct answer must not delete or overwrite an earlier wrong event.

## 3. Repeat-until-correct state

For each question store:

```text
wrong_attempts
correct_attempts_after_first_wrong
completed
```

Rules:

1. Correct on the first attempt completes the question.
2. After any wrong attempt, the configured number of correct answers is required.
3. A new wrong answer resets the current correct streak to zero.
4. Each pending question occurs exactly once in the pending queue.
5. An unanswered or incomplete question is rotated to the end of the queue; it is never silently removed.

## 4. Saved-test totals

Saved-test totals are derived from the immutable attempt ledger, not from mutable UI counters:

```text
total_wrong_attempts = count(attempt where is_correct = false)
unique_wrong_questions = distinct question_id where is_correct = false
wrong_attempts_for_question = count(false attempts for that question_id)
```

On load, reject records with duplicated event IDs, missing question IDs, inconsistent correctness, or non-contiguous per-question attempt numbers.

## 5. Result screen and pagination

Processing order is mandatory:

1. Derive wrong counts from the attempt ledger.
2. Filter to questions with `wrong_attempts >= 1`.
3. Preserve original test question order.
4. Paginate the already-filtered rows with `start = page_index * page_size`.
5. Increment the page index by exactly one.

Never paginate all questions before applying the wrong-only filter. For 15 wrong rows and page size 6, the only valid distribution is `6 + 6 + 3`, with pages numbered `1, 2, 3`.

## 6. Test-finish menu

The finish screen exposes four actions:

- New test
- End game
- Repeat the same complete test
- Repeat only questions answered incorrectly at least once in the immediately previous test

The wrong-only retest contains each wrong `question_id` exactly once, starts with a fresh attempt ledger, retains the same repeat-until-correct configuration, and stores the previous `run_id` as `source_run_id`.

When the previous test has no wrong questions, the wrong-only action remains visible but disabled with an explanatory message.

## 7. Transaction boundary

A submitted answer should be processed atomically:

1. Validate current `question_id` and displayed option IDs.
2. Resolve the selected immutable option ID.
3. Append the attempt event.
4. Update per-question progress.
5. Update the pending queue.
6. Commit persistence.
7. Refresh the UI from committed state.

Do not update UI counters independently before the attempt event is committed.

## 8. Required desktop-adapter hooks

The real desktop application must map these reference calls to its framework:

- answer button callback -> `QuizSessionController.submit_display_index`
- test save -> `save_test_run(...).to_json()` or equivalent database columns
- saved-test load -> `SavedTestRun.from_json()` plus `replay_attempts`
- result screen -> `build_result_pages`
- finish dialog -> `finish_options`
- wrong-only action -> `build_wrong_only_retest_from_saved`

## 9. Acceptance gates

The installed application is not considered fixed until all of the following pass against the real source and storage:

- shuffled-option correctness test
- wrong then correct history-preservation test
- required-correct streak reset test
- exact total/per-question wrong-count test
- correct-only exclusion test
- 15-row pagination test proving page 2 is visible
- saved-test reload/replay test
- wrong-only retest test
- manual UI smoke test on the packaged desktop build
