---
name: facebook-traffic-sync
description: Sync and analyze Facebook traffic in the social dashboard.
version: 1.1.1
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, facebook, traffic]
    category: productivity
---

# Facebook Traffic Sync

Use this skill to refresh Designveloper Facebook Page posts and engagement metrics, or answer follow-up Facebook traffic questions from stored dashboard data.

## Refresh And Analyze Flow

Before fetching, require a clear analysis date range. If the user did not provide one, ask for it. Do not silently choose a default range.

1. Call `mcp_secure_proxy_social_fetch_facebook_posts` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, preserve existing rows and report the no-data result.
4. Assign exactly one category to each post: `Career Advice`, `Tech news`, `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post Sharing`, `Promotion`, `Knowledge sharing`, `Case study`, `Meme`, or `Other`.
5. Use `Other` when `message` is null or empty. Do not invent `postType` or `impressions`; pass through the returned nullable values.
6. Call `mcp_social_dashboard_update_dsv_facebook_posts` with the same `fetchedAt`, all normalized fields, and `category`.
7. Filter the freshly fetched items to the user-confirmed inclusive date range. If none match, report that the refresh succeeded but do not create analysis blocks.
8. Call `mcp_social_dashboard_list_visualization_block_types` with `{}`. Keep each chosen contract's `jsonSchema` and `example` at hand; they are the only source of truth for that block's `payload` shape.
9. Analyze the filtered posts using the Standard Questions below. Perform all calculations yourself from the returned post rows.
10. Choose one or more advertised visualization contracts. Use `others` only when none of the specialized contracts fits.
11. Create one unique `runId`, one ISO-8601 `generatedAt`, and ordered block payloads. Every block uses the originating user request as `question`, platform `Facebook`, the confirmed date range, the selected type/version, and a unique `sortOrder` starting at `0`. Build each block's `payload` using exactly the field names and structure in that contract's `jsonSchema`/`example` (for example, `scorecard` requires a non-empty `items` array). Never omit a required field and never add a field the contract does not define; re-check every payload against its contract before the next step.
12. Call `mcp_social_dashboard_create_visualization_blocks` once with the complete run.
13. Report the post upsert count, generated block count, and provider warnings.

## Standard Questions

For a refresh request, answer these questions using only available fields and metrics:

- Which content categories are most effective?
- Which available post formats are most effective?
- Which topics create the most engagement, and impressions when real impressions are present?
- What do high-performing posts have in common?
- What problems appear in underperforming posts?
- What content should be prioritized next?

Do not describe Facebook reactions as real impressions. The `impressions` field may be null. Do not analyze visual quality unless provider data in the current rows actually contains visual information.

## Follow-Up Analysis Flow

Use this flow when the user asks a Facebook traffic question without requesting a provider refresh.

1. Require a clear question, platform, and date range. The platform is `Facebook` when this skill is already selected. Ask the user to clarify any missing or ambiguous input.
2. Call `mcp_social_dashboard_get_traffic_posts` with platform `Facebook`, the confirmed date range, and limit `100`.
3. Continue calling the tool with `nextCursor` until it returns `null`. Preserve every returned row for the analysis.
4. If the combined list is empty, report that no stored Facebook posts match and do not create blocks.
5. Call `mcp_social_dashboard_list_visualization_block_types` with `{}`.
6. Perform the requested calculations and qualitative analysis from the combined raw rows.
7. Choose advertised contracts, build one ordered run, and call `mcp_social_dashboard_create_visualization_blocks` once.
8. Report the answer and the number of blocks stored.

## Failure

Never expose credentials, invent metrics, or retry a failed write with changed data. Report the exact MCP error.
