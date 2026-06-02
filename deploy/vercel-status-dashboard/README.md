# AAYS ChatGPT Status Dashboard

This folder is a standalone Vercel static site for the AAYS / TerraYield ChatGPT multi-page status dashboard.

## Vercel settings

- Framework Preset: Other
- Root Directory: `deploy/vercel-status-dashboard`
- Build Command: leave empty
- Output Directory: leave empty

## One-click import

Use Vercel Import Project and select this GitHub repository:

`cagdascagdas100/chat_gpt_clone_1`

Then set Root Directory to:

`deploy/vercel-status-dashboard`

## Files

- `index.html`: standalone dashboard

## Runtime behavior

- Reads live JSON from `docs/chatgpt_status/multi_page_status.json` through GitHub raw URL.
- Keeps a local embedded snapshot as fallback.
- Shows live “kaç dk önce” counters without page refresh.
- Refreshes JSON every 60 seconds when network access is available.
