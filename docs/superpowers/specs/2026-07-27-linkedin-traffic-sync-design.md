# LinkedIn Traffic Sync Design

## Goal

Add LinkedIn as a third synced platform alongside Facebook and X: fetch
Designveloper's own LinkedIn company page posts and engagement via the
newly-approved Community Management API, sync them into the dashboard, and
surface them in the Traffic Report UI — matching the existing
`facebook-traffic-sync` / `x-traffic-sync` pipeline end to end.

This is one feature spanning four repos because the existing Facebook/X
pipeline already spans them: `hermes-agent-stack` (secure proxy gateway
fetcher), `infra-k8s` (policy/config/secrets for the proxy), `social-dashboard`
(storage + API + UI), `social-data-skills` (the Hermes skill that ties fetch
and write together).

## Background

- DSV's LinkedIn company page ID is `3675128` (confirmed against
  `linkedin.com/company/3675128/admin/dashboard/`; also referenced in
  `social-dashboard/project-specs.md`). Organization URN:
  `urn:li:organization:3675128`.
- LinkedIn Developer app `256752104` has Community Management API product
  access approved. Client ID/Secret exist; no OAuth consent flow has been run
  yet, so no access token exists yet.
- The dashboard already has placeholder scaffolding for LinkedIn (a disabled
  "Pending" option in the platform selector, stub donut-chart files with
  "not implemented yet" notes) but no working data path.
- API shapes below were verified against LinkedIn's current Microsoft Learn
  docs (`li-lms-2026-07`), not assumed from memory.

## Architecture / data flow

```
Hermes skill (linkedin-traffic-sync)
   │ 1. mcp_secure_proxy_social_fetch_linkedin_posts {}
   ▼
secure-proxy-gateway (hermes-agent-stack)
   │ 2. GET /rest/posts (Posts API, finder=author)         → list org posts
   │ 3. GET /rest/organizationalEntityShareStatistics       → batch engagement
   ▼
   { fetchedAt, items[], warnings[] }  (same envelope shape as Facebook/X)
   │
Hermes skill
   │ 4. assign one of 11 content categories per item
   │ 5. mcp_social_dashboard_update_dsv_linkedin_posts { fetchedAt, items }
   ▼
social-dashboard  →  dsv_linkedin_posts table
   │
Traffic Report UI (LinkedIn tab): overview, donut charts, growth trend,
post detail table — same layout family as Facebook/X
```

## Scope

- Proxy gateway fetcher for LinkedIn posts + engagement stats.
- `linkedin-traffic-sync` Hermes skill.
- Dedicated `dsv_linkedin_posts` table, MCP write tool, and read path
  (`get_traffic_posts`).
- Full LinkedIn Traffic Report UI: overview cards, category/impression donut
  charts, growth trend line chart, post detail table, platform selector
  enabled.
- infra-k8s policy/config/secret scaffolding for the new proxy locations.

## Out of scope

- Refresh-token / auto-renewal auth (see Auth below) — start with a static
  60-day access token; revisit once that path is confirmed working.
- LinkedIn follower-count-over-time tracking (would need the separate
  Follower Statistics API and a new table; Facebook's growth chart doesn't
  track followers either today, so this stays consistent).
- Any change to Facebook or X sync behavior.
- Competitor LinkedIn scraping (`competitor-content-sync`, BrightData-based)
  — unrelated existing feature, not touched.

## Component 1: Proxy gateway fetcher (hermes-agent-stack)

New `proxy_gateway/social_data/linkedin.py`, registered in `mcp.py`'s
`social_fetchers` dict as `social_fetch_linkedin_posts`.

`ORG_URN = "urn:li:organization:3675128"` — a Python constant, same
convention as Facebook's `PAGE_ID` and X's `USER_ID`.

**Step 1 — list posts.**
`GET https://api.linkedin.com/rest/posts?q=author&author={encoded org URN}&count=100&start={N}&sortBy=CREATED`
- Headers: `Authorization: Bearer …`, `Linkedin-Version: 202607`,
  `X-Restli-Protocol-Version: 2.0.0`, `X-RestLi-Method: FINDER`.
- Requires `r_organization_social` scope.
- `sortBy=CREATED` is deliberate (not the API default `LAST_MODIFIED`): an
  edited old post would otherwise jump to the front of the list and break
  the lookback-cutoff pagination stop condition.
- Lookback window: 183 days, same as Facebook/X.
- Paginate by incrementing `start` by `count` until a page returns fewer
  than `count` elements, or every element on a page is older than the
  cutoff.
- Skip elements where `lifecycleState != "PUBLISHED"`.
- Field mapping:
  - `id` → `postId`; `postUrl` = `https://www.linkedin.com/feed/update/{id}/`
  - `commentary` → `message` (passed through as-is, same as Facebook's
    `message` — may contain LinkedIn's "little" mention/hashtag templates)
  - `publishedAt` (epoch ms) → ISO 8601 string
  - `postType` derived from `content` shape: `content.media.id` prefix
    `urn:li:image:` → `photo`, `urn:li:video:` → `video`,
    `urn:li:document:` → `document`; `content.article` → `article`;
    `content.multiImage` → `carousel`; `content.poll` → `poll`; no
    `content` → `text`. Unrecognized shapes produce a warning (mirrors
    Facebook's `_unmapped_format_metadata`), not a silent guess.

**Step 2 — engagement stats.**
`GET https://api.linkedin.com/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity={org URN}&shares=List(...)`
(and a separate `ugcPosts[i]=...` call, since post ids come back as either
`urn:li:share:` or `urn:li:ugcPost:` — split fetched ids by prefix and query
each URN type through its matching param).
- Requires `rw_organization_admin` scope — different from `r_organization_social`;
  both must be granted at OAuth consent time.
- Single batched call per id-type chunk (~50 URNs per chunk, for URL-length
  safety) rather than Facebook's per-post loop.
- Per LinkedIn's docs, a post absent from a *successful* response is defined
  as all-zero engagement, not unknown. Only a whole-chunk call failure
  produces `null` + a warning for every post in that chunk.
- Field mapping into the write schema: `likeCount` → `numReactions`,
  `commentCount` → `numComments`, `shareCount` → `numShares`,
  `impressionCount` → `impressions`, `uniqueImpressionsCount` → `reach`,
  `clickCount` → `totalClicks`. No `linkClicks` field — LinkedIn has no
  distinct sub-metric for it, so it's dropped from the schema entirely
  rather than carried as a permanently-null column.

## Auth

Static bearer token, not an auto-refreshing flow, for this pass:
- New `upstream_auth`-free location using a static `upstream_headers`
  `Authorization: Bearer __PROXY_ENV__LINKEDIN_ACCESS_TOKEN` — same pattern
  already used by the Ahrefs and GitHub proxy locations. No changes to
  `oauth2_refresh_auth.py`.
- LinkedIn access tokens are a flat 60-day lifespan (`expires_in: 5184000`)
  regardless of Marketing Developer Platform (MDP) partner status. The
  30-minute figure sometimes quoted is the one-time *authorization code*'s
  lifespan (must be exchanged immediately), not the resulting access token.
- Refresh tokens are only issued to apps with MDP partner status, which is a
  separate approval from Community Management API product access and is
  unconfirmed for app `256752104`. **Deferred**: once the static access
  token is confirmed working end-to-end, revisit whether MDP/refresh-token
  auto-renewal is worth adding (would reuse `oauth2_refresh_token`'s
  rotation/persistence logic with one addition: a `client_auth_style: "body"`
  option, since LinkedIn authenticates via POST body fields, not the HTTP
  Basic auth X uses).
- One-time bootstrap (manual, human-in-the-loop — LinkedIn OAuth requires an
  interactive browser login as a DSV page admin): a small script in
  `hermes-agent-stack` (private repo, not the public skills repo) builds
  the authorization URL with `scope=r_organization_social%20rw_organization_admin`,
  runs a local callback server on a redirect URI registered in the app's
  Auth tab, captures `code`, and exchanges it via
  `POST https://www.linkedin.com/oauth/v2/accessToken` (body fields
  `grant_type=authorization_code`, `code`, `client_id`, `client_secret`,
  `redirect_uri`) for the access token. Operator seals the resulting token
  into the k8s secret.
- Operational note: a static token needs manual renewal roughly every 60
  days until/unless the refresh-token path is added later.

## Component 2: infra-k8s

- `secure-proxy-policy.yaml`: new `linkedin` server
  (`linkedin.proxy.local`, base `https://api.linkedin.com`) with two
  `fixed_tool_only: true` locations — `linkedin_posts_finder` and
  `linkedin_share_statistics` — reusing the existing `social_data_allow`
  Mattermost user anchor. Static headers `Linkedin-Version: "202607"` and
  `X-Restli-Protocol-Version: "2.0.0"` on both; `X-RestLi-Method: "FINDER"`
  additionally on the posts location.
- `2-proxy-env-configmap.yaml`: add `LINKEDIN_BASE_URL` (`https://api.linkedin.com`).
- `5-proxy-secrets.sealed-secret.yaml`: add `LINKEDIN_ACCESS_TOKEN`.
  Cannot be sealed from this environment (no cluster public cert) — operator
  runs `kubeseal` after the bootstrap step.
- `Linkedin-Version: 202607` is a static pin; LinkedIn deprecates API
  versions ~12 months after release, so this header needs a manual bump on
  that cadence. Documented here, not automated (YAGNI).

## Component 3: Dashboard backend (social-dashboard)

- `db/schema.ts`: new `dsvLinkedinPosts` table — `postId, postUrl,
  platform (enum: ['LinkedIn']), message, publishedAt, postType, pic,
  category, numReactions, numComments, numShares, impressions, reach,
  totalClicks, fetchedAt`, unique index on `(platform, postId)`. New Drizzle
  migration.
- `app/api/mcp/schemas.ts`: new `dsvLinkedinPostItemSchema` /
  `updateDsvLinkedinPostsArgsSchema`. `trafficPlatformSchema` becomes
  `z.enum(['Facebook', 'Twitter', 'LinkedIn'])`.
- `app/api/mcp/route.ts`: new `update_dsv_linkedin_posts` tool (upsert into
  `dsvLinkedinPosts`, same onConflict pattern as Facebook/X).
  `get_traffic_posts` becomes an explicit 3-way branch (Facebook / Twitter /
  LinkedIn) instead of today's Facebook-or-else-Twitter fallback — the
  fallback becomes a real bug once a third platform exists, so this is
  fixed as part of this change, not left as latent debt.
  `get_traffic_posts` / `create_visualization_blocks` inputSchema enums gain
  `'LinkedIn'`.
- `features/traffic/visualization-blocks/types.ts`: `VisualizationPlatform`
  becomes `'Facebook' | 'Twitter' | 'LinkedIn'` (hand-maintained, separate
  from the Zod schema).
- `features/traffic/actions/update-post-pic.ts`: 3-way branch, imports
  `dsvLinkedinPosts`.

## Component 4: Dashboard frontend (social-dashboard)

Full LinkedIn component family, each a direct port of the Facebook
equivalent (this codebase keeps per-platform actions/hooks/components fully
separate rather than sharing beyond `bucket-posts-by-date.ts` and the
generic chart/type primitives — confirmed by reading the existing Facebook
and X implementations):

| Layer | Files |
|---|---|
| Types | `LinkedInGrowthMetricKey` (`numReactions \| numComments \| numShares \| impressions`), `LinkedInOverviewMetric(s)`, `LinkedInPostDetailItem` in `types/index.ts` |
| Actions | `get-linkedin-overview.ts`, `get-linkedin-growth-trend.ts`, `get-linkedin-category-distribution.ts`, `get-linkedin-post-detail.ts` |
| Hooks | `use-linkedin-overview.ts`, `use-linkedin-growth-trend.ts`, `use-linkedin-category-distribution.ts`, `use-linkedin-post-detail.ts` |
| Overview | `overview-section/linkedin-overview/{overview-section,filter,index}.tsx` |
| Donut charts | Fill in `donut-chart/linkedin-chart/{category-percentage,impression-percentage}.tsx` for real (own Filter/Chart/CategoryGroup/Section — deliberately not shared with Facebook's, per the existing "legitimately free to diverge" convention) |
| Growth chart | `growth-line-chart/linkedin-chart/{growth-trend-section,index}.tsx` |
| Post detail | `post-detail/linkedin-post-detail-table.tsx` |

**Metric scope**: growth chart and overview use the same 4 metrics as
Facebook (Reactions/Comments/Shares/Impressions), not project-specs.md's
aspirational "impressions, views, clicks, followers" list — "views" isn't a
distinct LinkedIn field (same as impressions), and follower-over-time
tracking is out of scope (see Out of scope).

**Post detail table columns**: PIC, Topic, Message, Date, Link, Format,
Impressions, Reach, Reactions, Comments, Shares, Total Clicks — Facebook's
columns minus Link Clicks (no LinkedIn equivalent).

**Wiring**:
- `platform-selector.tsx`: remove `disabled`/`badge: 'Pending'` from the
  LinkedIn option.
- `traffic/page.tsx`: replace the binary `isTwitterSelected` ternary with a
  3-way switch over `selectedPlatform`.
- `post-detail-section.tsx`, `pic-cell.tsx`: widen the platform union to
  include `'LinkedIn'`.
- `content-performance-analysis`: no change needed — already typed on the
  generic `VisualizationPlatform`, which picks up `'LinkedIn'` from the
  backend section above.

## Component 5: `linkedin-traffic-sync` skill (social-data-skills)

Mirrors `facebook-traffic-sync/SKILL.md`:
1. Call `mcp_secure_proxy_social_fetch_linkedin_posts` with `{}`.
2. Require `fetchedAt`, `items`, `warnings`. Stop on tool error.
3. Empty `items` → preserve existing rows, report no-data.
4. Assign exactly one category per item, same taxonomy as
   `facebook-traffic-sync`/`x-traffic-sync`: `Career Advice`, `Tech news`,
   `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post
   Sharing`, `Promotion`, `Knowledge sharing`, `Case study`, `Meme`, or
   `Other`. Use `Other` when `message` is null or empty.
5. Pass `postType`, `impressions`, `reach`, `totalClicks` through
   unmodified.
6. Call `mcp_social_dashboard_update_dsv_linkedin_posts` with `fetchedAt`,
   normalized fields, `category`.
7. Report upsert count + warnings.

README gets the matching install/update lines. `tests/test_skills.py` gets
a new `EXPECTED` entry:
`"linkedin-traffic-sync": ("mcp_secure_proxy_social_fetch_linkedin_posts", "mcp_social_dashboard_update_dsv_linkedin_posts")`,
version `1.0.0`.

## Testing

- `hermes-agent-stack`: `test_social_data_linkedin.py` mirroring
  `test_social_data_facebook.py` — pagination, lookback cutoff, `postType`
  derivation, batch-stats chunking/mapping, chunk-failure → null + warning.
- `social-dashboard`: schema/route tests for `update_dsv_linkedin_posts` and
  the 3-way `get_traffic_posts`; `linkedin-chart.test.tsx` mirroring
  `facebook-chart.test.tsx`.
- `social-data-skills`: covered by the existing `test_skills.py` suite once
  the new `EXPECTED` entry and README lines are added.

## Rollout order

1. infra-k8s: policy/config/secret scaffolding (secret values filled in
   after the OAuth bootstrap step, which requires the app credentials that
   already exist).
2. hermes-agent-stack: fetcher + `mcp.py` registration, validated against
   real credentials once the access token exists.
3. social-dashboard: schema/migration → backend route → frontend
   components, in that order.
4. social-data-skills: skill definition last, once both MCP tools it calls
   exist and work.

## Open risks

- MDP partner status for app `256752104` is unconfirmed — affects only the
  deferred refresh-token work, not this pass.
- Exact LinkedIn API response shapes are verified against current docs but
  not against a live call (no credentials available in this environment);
  first real sync may surface response-shape surprises the same way
  Facebook's nullable Insights fields did after initial deployment.
