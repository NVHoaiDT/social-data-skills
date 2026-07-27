---
name: linkedin-traffic-sync
description: Sync LinkedIn traffic into the social dashboard.
version: 1.2.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, linkedin, traffic]
    category: productivity
---

# LinkedIn Traffic Sync

Use this skill to refresh Designveloper LinkedIn company page posts and engagement metrics. This skill does not analyze traffic or create visualization blocks; use the `traffic-analysis` skill for that.

## Flow

1. Call `mcp_secure_proxy_social_fetch_linkedin_posts` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, preserve existing rows and report the no-data result.
4. Assign exactly one category to each post: `Career Advice`, `Tech news`, `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post Sharing`, `Promotion`, `Knowledge sharing`, `Case study`, `Meme`, or `Other`.
5. Use `Other` when `message` is null or empty. Do not invent `postType`. Pass `numReactions`, `numComments`, `numShares`, `impressions`, `reach`, and `totalClicks` through exactly as returned. They are real LinkedIn share-statistics data, but an individual post's values may be `null` when its statistics lookup failed. Never invent replacement values.
6. Call `mcp_social_dashboard_update_dsv_linkedin_posts` in batches of about 25 items, using the same `fetchedAt` for every batch. Every item in every batch must carry all of its fields — the tool has no mode for sending only changed fields (e.g. metrics alone) on an existing row, and there is no file, reference, or bulk-import path; sequential `items[]` calls through this one tool are the complete, intended mechanism, so do not search for another one or attempt a raw/unauthenticated write. Each batch call is an independent upsert, not a step in one all-or-nothing transaction: send the first batch as soon as it is ready, and keep sending batches — in this run and, if needed, in a follow-up run — until every fetched item has been written. Stopping partway through a run (time, budget, or a transient error) is expected and safe, never a reason to withhold the batches you can still send; the write is idempotent, so resuming later just re-upserts already-written rows harmlessly.
7. Sum the upsert counts across batches and report the total plus provider warnings. If the run stopped before every item was written, say exactly how many remain and that a follow-up run will pick them up.

## Failure

Never expose credentials, invent metrics, or retry a failed write with changed data. An authentication-shaped fetch failure requires operator credential repair because the LinkedIn access token expires roughly every 60 days and must be manually renewed until refresh-token support is added. Report the exact MCP error.
