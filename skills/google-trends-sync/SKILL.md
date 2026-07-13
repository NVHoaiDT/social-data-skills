---
name: google-trends-sync
description: Sync Google Trends into the social dashboard.
version: 1.0.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, google-trends]
    category: productivity
---

# Google Trends Sync

Use this skill to refresh Google Trends data for Designveloper's social dashboard.

## Flow

1. Call `mcp_secure_proxy_social_fetch_google_trends` with `{}`.
2. Require an object containing `fetchedAt`, `items`, and `warnings`.
3. If the fetch tool fails, stop and report the exact error. Do not call the write tool.
4. If `items` is empty, preserve existing dashboard data and report that no qualifying trends were returned.
5. For every item, assign `relatedToDSVScore` from 0 to 100. Judge the actual topic against software development, AI, product engineering, web/mobile development, cybersecurity, cloud, outsourcing, startup technology, and Designveloper's audience. Do not keyword-match and do not drop low-scoring items.
6. Call `mcp_social_dashboard_update_trends` with the same `fetchedAt` and every original item plus `relatedToDSVScore`.
7. Report the number written and include every warning from the fetch result.

Never invent `sparklineData`. Pass through the array returned by secure-proxy, including an empty array.

## Failure

Report the failed step, exact MCP error, and whether existing dashboard data was preserved. Do not retry a failed write with changed or invented data.
