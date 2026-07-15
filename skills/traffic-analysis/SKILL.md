---
name: traffic-analysis
description: Answer Facebook or X traffic questions from stored data.
version: 1.0.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, facebook, x, twitter, traffic, analysis]
    category: productivity
---

# Traffic Analysis

Use this skill to answer Facebook or X traffic performance questions from data already stored in the social dashboard. This skill never fetches from Facebook or X and never writes post data; it only reads stored posts and writes visualization blocks.

## Flow

1. Require a clear platform (`Facebook` or `Twitter`), an inclusive date range, and a non-empty list of questions. Ask the user to clarify any missing or ambiguous input. Do not silently choose a default range or invent questions.
2. Call `mcp_social_dashboard_get_traffic_posts` with the confirmed platform, date range, and limit `100`.
3. Continue calling the tool with `nextCursor` until it returns `null`. Combine every returned row for the analysis.
4. If the combined list is empty, report that no stored posts match the platform and date range, and do not create blocks.
5. Call `mcp_social_dashboard_list_visualization_block_types` with `{}`. Keep each chosen contract's `jsonSchema` and `example` at hand; they are the only source of truth for that block's `payload` shape.
6. Answer each question in the order given, using only the combined raw rows. Perform all calculations yourself. Do not describe reactions or likes as impressions; treat `impressions` as unavailable when null. Do not analyze visual quality unless provider data in the current rows actually contains visual information.
7. For each question, choose one or more advertised visualization contracts. Use `others` only when none of the specialized contracts fits.
8. Create one unique `runId`, one ISO-8601 `generatedAt`, and ordered block payloads across all questions. Every block uses its originating question as `question`, the confirmed platform, the confirmed date range, the selected type/version, and a unique `sortOrder` starting at `0`. Build each block's `payload` using exactly the field names and structure in that contract's `jsonSchema`/`example` (for example, `scorecard` requires a non-empty `items` array). Never omit a required field and never add a field the contract does not define; re-check every payload against its contract before the next step.
9. Call `mcp_social_dashboard_create_visualization_blocks` once with the complete run.
10. Report the number of questions answered, the number of blocks created, and the `runId`.

## Failure

Never expose credentials, invent metrics, or retry a failed write with changed data. Report the exact MCP error.
