---
name: x-traffic-sync
description: Sync X traffic into the social dashboard.
version: 1.0.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, x, twitter, traffic]
    category: productivity
---

# X Traffic Sync

Use this skill to refresh Designveloper X posts and engagement metrics.

## Flow

1. Call `mcp_secure_proxy_social_fetch_x_posts` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, preserve existing rows and report the no-data result.
4. Assign exactly one category to each post: `Career Advice`, `Tech news`, `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post Sharing`, `Promotion`, `Knowledge sharing`, `Case study`, `Meme`, or `Other`.
5. Use `Other` when `message` is null or empty. Do not invent `postType`; pass through the returned value and all real public metrics.
6. Call `mcp_social_dashboard_update_dsv_x_posts` with the same `fetchedAt`, all normalized fields, and `category`.
7. Report the upsert count and warnings. An authentication-shaped fetch failure requires operator credential repair, not invented fallback data.

## Failure

Never expose credentials, invent metrics, or retry a failed write with changed data. Report the exact MCP error.
