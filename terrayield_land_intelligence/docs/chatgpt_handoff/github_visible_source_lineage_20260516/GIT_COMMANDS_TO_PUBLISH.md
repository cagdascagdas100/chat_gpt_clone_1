# Git Commands To Publish

Run only after ChatGPT confirms the package is clean.

Set-Location "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
git status --short
git diff --check
git add "docs/chatgpt_handoff/github_visible_source_lineage_20260516"
git add "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py"
git commit -m "Prepare source lineage evidence and partial-lineage guard"
git push origin security-accuracy-expansion-20260508
