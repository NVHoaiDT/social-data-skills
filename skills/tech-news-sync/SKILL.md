---
name: tech-news-sync
description: Sync technology news into the social dashboard.
version: 1.2.0
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
4. For every item, use only `title`, `summary`, and `source` to assign:
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
       Headline: <main on-image copy, or state that no headline is needed>
       Background: <concept-specific setting, key visual, mood, or art direction>
       Describe:
       - <detailed execution direction in the social team's usual style>
       - <additional concept-specific details as needed>
       ```

       Write `Describe` like the sheet's real briefs: explain concrete text hierarchy and placement, composition, supporting visuals or icons, data or callouts, slide or video sequence, emphasis, constraints, and references when relevant. Include only what serves the idea, and use as many bullets or subsections as useful. If the concept intentionally has no conventional headline or background, say so rather than inventing one.

   - Otherwise set all four Plan suggestion fields to `null`.
5. Call `mcp_social_dashboard_update_news` with the same `fetchedAt`, original normalized fields, and every Hermes-produced field. Never send a partial Plan suggestion.
6. Report the number written and list source warnings without treating a usable partial batch as a total failure.

## Failure

Never invent articles or retry a failed write with modified data. Report the exact failed step and MCP error.
