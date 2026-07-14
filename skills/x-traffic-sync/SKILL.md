---
name: x-traffic-sync
description: Sync and analyze X traffic in the social dashboard.
version: 1.1.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, x, twitter, traffic]
    category: productivity
---

# X Traffic Sync

Use this skill to refresh Designveloper X posts and engagement metrics, or answer follow-up X traffic questions from stored dashboard data.

## Refresh And Analyze Flow

Before fetching, require a clear analysis date range. If the user did not provide one, ask for it. Do not silently choose a default range.

1. Call `mcp_secure_proxy_social_fetch_x_posts` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, preserve existing rows and report the no-data result.
4. Assign exactly one category to each post: `Career Advice`, `Tech news`, `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post Sharing`, `Promotion`, `Knowledge sharing`, `Case study`, `Meme`, or `Other`.
5. Use `Other` when `message` is null or empty. Do not invent `postType`. Preserve `numLikes`, `numReplies`, `numRetweets`, `numQuotes`, `numBookmarks`, and real `impressions`.
6. Call `mcp_social_dashboard_update_dsv_x_posts` with the same `fetchedAt`, all normalized fields, and `category`.
7. Filter the freshly fetched items to the user-confirmed inclusive date range. If none match, report that the refresh succeeded but do not create analysis blocks.
8. Call `mcp_social_dashboard_list_visualization_block_types` with `{}`.
9. Analyze the filtered posts using the Standard Questions below. Perform all calculations yourself from the returned post rows.
10. Choose one or more advertised visualization contracts. Use `others` only when none of the specialized contracts fits.
11. Create one unique `runId`, one ISO-8601 `generatedAt`, and ordered block payloads. Every block uses the originating user request as `question`, platform `Twitter`, the confirmed date range, the selected type/version, and a unique `sortOrder` starting at `0`.
12. Call `mcp_social_dashboard_create_visualization_blocks` once with the complete run.
13. Report the post upsert count, generated block count, and provider warnings.

## Standard Questions

For a refresh request, answer these questions using only available fields and metrics:

- Which content categories are most effective?
- Which available post formats are most effective?
- Which topics create the most impressions and engagement?
- What do high-performing posts have in common?
- What problems appear in underperforming posts?
- What content should be prioritized next?

Never invent clicks, reach, follower history, or visual details. Do not analyze visual quality unless provider data in the current rows actually contains visual information.

## Follow-Up Analysis Flow

Use this flow when the user asks an X traffic question without requesting a provider refresh.

1. Require a clear question, platform, and date range. The platform is `Twitter` when this skill is already selected. Ask the user to clarify any missing or ambiguous input.
2. Call `mcp_social_dashboard_get_traffic_posts` with platform `Twitter`, the confirmed date range, and limit `100`.
3. Continue calling the tool with `nextCursor` until it returns `null`. Preserve every returned row for the analysis.
4. If the combined list is empty, report that no stored X posts match and do not create blocks.
5. Call `mcp_social_dashboard_list_visualization_block_types` with `{}`.
6. Perform the requested calculations and qualitative analysis from the combined raw rows.
7. Choose advertised contracts, build one ordered run, and call `mcp_social_dashboard_create_visualization_blocks` once.
8. Report the answer and the number of blocks stored.

## Failure

Never expose credentials, invent metrics, or retry a failed write with changed data. An authentication-shaped fetch failure requires operator credential repair. Report the exact MCP error.
