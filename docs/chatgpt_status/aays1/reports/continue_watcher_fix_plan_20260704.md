# AAYS1 Continue Watcher Fix Plan

status=LOCAL_RUNNER_TRIGGER_REQUIRED
final_ready=false
fake_data=false

## Problem

The current proven runner mode is single-pass. It does not continuously watch pending queue files. This is why `zzzz_114_security_official_source_join_probe.task.json` can remain pending after it is queued.

## Required fix

Use one local runner command to process the pending queue task, mark it done, push the output, and update the program progress JSON. After that, ChatGPT can continue checking GitHub outputs with the normal `devam et` flow.

## Current pending task

`docs/chatgpt_status/aays1/queue/zzzz_114_security_official_source_join_probe.task.json`

## Expected output

`docs/chatgpt_status/security_public_safety/runner_outputs/114_security_official_source_join_probe.json`

## Gate

Do not mark final_ready=true until non-empty verified official source rows exist and the program/site output has been updated.
