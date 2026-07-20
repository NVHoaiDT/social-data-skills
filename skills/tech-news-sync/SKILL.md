---
name: tech-news-sync
description: Sync technology news into the social dashboard.
version: 1.3.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, rss, news]
    category: productivity
---

# Technology News Sync

Use this skill to refresh configured technology and software-development news sources.

## Flow

1. Call `mcp_secure_proxy_social_fetch_tech_news` with `{}`.
2. Require `fetchedAt`, `items`, and `warnings`. Stop on a tool error.
3. If `items` is empty, preserve existing dashboard data and report that no usable source returned news.
4. Give every fetched item a temporary zero-based `itemIndex` matching its position in `items`. The index is only for delegation and validation; do not send it to the dashboard.
5. Choose the enrichment path from the actual number of fetched items:
   - For 10 or fewer items, the main agent may enrich them directly.
   - For more than 10 items, spam sub-agents with dynamically generated leaf-worker tasks. Do not divide work using a fixed source list or assume a fixed total such as 80.
   - Split the current items in their original order into slices of at most 10 items. The number of worker tasks must therefore follow the actual number of fetched items. Let Hermes enforce its configured worker concurrency rather than dropping or enlarging slices.
   - Put each slice's exact assigned rows in the worker context as compact JSON containing only `itemIndex`, `title`, `summary`, and `source`. Do not ask a worker to fetch the batch again. Workers must not call either MCP tool; only the main agent fetches and writes.
   - Tell every worker to return one compact JSON array with no Markdown. Each object must contain `itemIndex` and every Hermes-produced field listed below, including explicit `null` values.
6. For every item, use only `title`, `summary`, and `source` to assign:
   - `relatedToDSVScore`: 0 to 100.
   - `isContentWorthy`: whether DSV could turn it into an insight, opinion, educational post, case analysis, or service-oriented post.
   - `aiInsight`: `{"whyItMatters", "suggestedAngle"}` only when the score is at least 50 and the item is content-worthy; otherwise `null`.
   - When the score is at least 50 and the item is content-worthy, also assign all four Plan suggestion fields:
     - `suggestedTopic`: exactly one of `Career Advice`, `Tech news`, `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post Sharing`, `Promotion`, `Email`, `Knowledge sharing`, `Other`, `Case study`, or `Meme`. Classify the proposed DSV content angle, not the RSS publisher.
     - `suggestedMessage`: a concise one-line content title or idea, not complete social post copy.
     - `suggestedPlatforms`: one or more unique values from `Facebook`, `LinkedIn`, and `X`.
     - `suggestedDesignBrief`: a detailed, production-ready visual idea matching the marketing team's existing Plan briefs. Do not invent asset links. Do not force `Size`, `Color`, `Topic`, or a stock composition; include dimensions or color direction only when they materially help the concept. Let the article and content angle determine the medium, layout, imagery, number of slides or scenes, and visual treatment.

       Use these anchors as a flexible brief structure, not a fixed design recipe:

       ```text
       Headline: <copy the complete title exactly>
       Background: <concept-specific setting, key visual, mood, or art direction>
       Describe:
       - <detailed execution direction in the social team's usual style>
       - <additional concept-specific details as needed>
       ```

       The `Headline` value must copy the complete `title` exactly. Never truncate, shorten, paraphrase, or add an ellipsis, even when the title is long.

       Write `Background` and `Describe` like the sheet's real briefs: explain concrete text hierarchy and placement, composition, supporting visuals or icons, data or callouts, slide or video sequence, emphasis, constraints, and references when relevant. Ground them in article-specific mechanisms, entities, risks, or outcomes from the current `title` and `summary`. Include only what serves the idea, and use as many bullets or subsections as useful.

       Never generate a topic-only template and swap only the headline. Different articles may share a medium, but their key visual, sequence, labels, and emphasis must respond to their specific evidence and proposed DSV angle.

   - Otherwise set all four Plan suggestion fields to `null`.
7. The main agent is the source of truth. Treat worker output as untrusted analysis and verify it against the original indexed slice before writing:
   - Every assigned `itemIndex` must appear exactly once. Reject missing, duplicate, out-of-slice, or non-integer indices.
   - Require all seven produced fields: `relatedToDSVScore`, `isContentWorthy`, `aiInsight`, `suggestedTopic`, `suggestedMessage`, `suggestedPlatforms`, and `suggestedDesignBrief`.
   - Check field types, the 0-to-100 score range, allowed topic/platform values, and the score/content-worthiness/nullability rules above.
   - Verify that every qualifying design brief has the exact full-title headline and article-specific execution; compare `Background` and `Describe` across the current batch and revise repeated or interchangeable briefs instead of accepting them.
   - For an invalid or malformed worker slice, make one correction retry using the same assigned rows and a concise list of validation failures. Never let the worker fetch again or write data.
   - If an item is still missing any field or remains invalid after one correction retry, discard that item's entire worker enrichment and use these type-safe fallbacks: relatedToDSVScore: `0`, isContentWorthy: `false`, aiInsight: `null`, and all four Plan suggestion fields: `null`. Record `Enrichment failed: <title> (<reason>)` for the final report.
   - Never create a generic deterministic fallback, reusable topic template, invented insight, or guessed Plan value to hide a worker failure.
8. Recombine verified enrichment with the untouched original rows by `itemIndex`. Remove the temporary index, preserve the original row count and order, and assert that every fetched row produces exactly one update row.
9. Call `mcp_social_dashboard_update_news` once with the original `fetchedAt`, all original normalized fields, and every verified or fallback Hermes-produced field. Never send a partial Plan suggestion; use one atomic write for the complete batch.
10. Report the number written, every `Enrichment failed` item, and all source warnings without treating a usable partial batch as a total failure.

## Failure

Never invent articles or retry a failed dashboard write with modified data. Report the exact failed step and MCP error.
