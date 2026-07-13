---
name: competitor-content-sync
description: Sync competitor posts into the social dashboard.
version: 1.0.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, competitors, linkedin]
    category: productivity
---

# Competitor Content Sync

Use this skill to refresh configured competitor LinkedIn content.

## Flow

1. Call `mcp_secure_proxy_social_fetch_competitor_posts` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, do not call the write tool because an empty write would erase the current competitor snapshot.
4. For each item, assign `relatedToDSVScore` from 0 to 100 based on service-related content, software-development services, developer knowledge, memes, case studies, engineering stories, or hiring stories relevant to Designveloper.
5. When the score is above 50, set `ignoreReason` to `null` and produce:
   - `contentCategory`.
   - `detectedContent`: `topic`, `hook`, `format`, `audienceAngle`, `cta`, `whyEffective`.
   - `strategy`: a concrete adaptation for Designveloper that does not copy the competitor.
   - `engagementLabel`: `High` or `Medium`.
   - `engagementNote`.
6. When the score is 50 or below, produce `ignoreReason` and set all analysis, strategy, and engagement fields to `null`.
7. Call `mcp_social_dashboard_update_competitor_contents` with the same `fetchedAt` and all normalized plus reasoned fields.
8. Report the number written and every skipped-company warning.

## Failure

Never retry the fetch, invent competitor content, or write an empty replacement. Report the exact MCP error.
