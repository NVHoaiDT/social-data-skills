---
name: tech-news-sync
description: Sync technology news into the social dashboard.
version: 1.0.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, rss, news, cron]
    category: productivity
---

# Technology News Sync

Use this skill to refresh configured technology and software-development news sources.

## Flow

1. Call `mcp_secure_proxy_social_fetch_tech_news` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, preserve existing dashboard data and report that no usable source returned news.
4. For every item, use only `title`, `summary`, and `source` to assign:
   - `relatedToDSVScore`: 0 to 100.
   - `isContentWorthy`: whether DSV could turn it into an insight, opinion, educational post, case analysis, or service-oriented post.
   - `aiInsight`: `{"whyItMatters", "suggestedAngle"}` only when the score is at least 50 and the item is content-worthy; otherwise `null`.
5. Call `mcp_social_dashboard_update_news` with the same `fetchedAt`, original normalized fields, and the three Hermes-produced fields.
6. Report the number written and list source warnings without treating a usable partial batch as a total failure.

## Failure

Never invent articles or retry a failed write with modified data. Report the exact failed step and MCP error.
