# Existing Live Blocker: index.html hash mismatch

Current user-supplied runner logs show `index_html` is failing the live hash baseline while other checked live modules pass.

This task does not repair or overwrite `index.html`, because that file is explicitly protected. The correct behavior is to continue producing scope-only evidence infrastructure and mark the live mismatch as an existing blocker.

Resolution requires a separate authorized live-surface review.