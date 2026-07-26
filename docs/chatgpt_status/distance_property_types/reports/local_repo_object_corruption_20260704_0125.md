# Local Repo Object Corruption

page_key=distance_property_types
status=LOCAL_REPO_OBJECT_CORRUPTION_RECLONE_REQUIRED
final_ready=false

The local F repo cannot parse HEAD. Git reset, status, fetch, checkout, commit, pull and push are blocked by bad local objects or refs.

The runner chain works and the input gate task was copied to bridge pending. The safe fix is to keep the backup and create a fresh local clone, then restore the saved input and queue files.

No fake data. No database write. No schema change. No migration. No production deploy.
