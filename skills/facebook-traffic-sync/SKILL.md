---
name: facebook-traffic-sync
description: Sync Facebook traffic into the social dashboard.
version: 2.1.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, facebook, traffic]
    category: productivity
---

# Facebook Traffic Sync

Use this skill to refresh Designveloper Facebook Page posts and engagement metrics. This skill does not analyze traffic or create visualization blocks; use the `traffic-analysis` skill for that.

## Flow

1. Call `mcp_secure_proxy_social_fetch_facebook_posts` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, preserve existing rows and report the no-data result.
4. Assign exactly one category to each post: `Career Advice`, `Tech news`, `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post Sharing`, `Promotion`, `Knowledge sharing`, `Case study`, `Meme`, or `Other`.
5. Use `Other` when `message` is null or empty. Pass `postType`, `impressions`, `reach`, `totalClicks`, and `linkClicks` through exactly as returned. They are real Facebook Insights data, but an individual field may be `null` when that post's Insights lookup failed. Never invent a replacement value.
6. Call `mcp_social_dashboard_update_dsv_facebook_posts` with the same `fetchedAt`, all normalized fields (including `reach`, `totalClicks`, and `linkClicks`), and `category`.
7. Report the upsert count and provider warnings.

## Failure

Never expose credentials, invent metrics, or retry a failed write with changed data. Report the exact MCP error.
