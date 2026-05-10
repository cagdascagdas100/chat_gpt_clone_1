# Runner Continue Protocol - 2026-05-07

The ChatGPT-to-local-runner bridge works as follows:

1. The user writes `devam et` in ChatGPT.
2. ChatGPT writes a new PowerShell script under the bridge repository path `ai-task-scripts/`.
3. ChatGPT updates `ai-tasks/current-task.json` with a new task id and command.
4. The local PowerShell runner polls GitHub, notices the id change, pulls the bridge repo, and runs the command.
5. The runner writes stdout/stderr/results under `ai-results/` and pushes them back to GitHub.

For this project, every generated file must remain under `security_accuracy_expansion/` in the AAYS repo. Live surfaces are read-only.