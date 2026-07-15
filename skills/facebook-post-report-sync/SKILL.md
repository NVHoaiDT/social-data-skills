---
name: facebook-post-report-sync
description: Sync missing Facebook posts into the report Google Sheet.
version: 1.0.0
author: Designveloper
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [social-data, facebook, google-sheets, reporting]
    category: productivity
---

# Facebook Post Report Sync

Add Facebook posts missing from the team's content-report spreadsheet. Keep the sync strictly add-only: never edit a row whose LINK cell is already populated.

## Script

Use `scripts/plan_sheet_updates.py` to make exact-link deduplication, placeholder selection, and cell-range planning deterministic. The script performs no network or credential access.

## Flow

1. Resolve the spreadsheet. If the user's message contains a Google Sheets URL, use it without another confirmation. Otherwise state the default URL and ask for confirmation before continuing: `https://docs.google.com/spreadsheets/d/1DT36lacwhMIaPe6Kp5jhhVfVnKudyiqVneevwehtwWg/edit?gid=119200873`.
2. Extract the spreadsheet ID from the confirmed URL: the value between `/d/` and the next `/`.
3. Read spreadsheet metadata with the available Google Sheets command and require exactly one tab literally named `Facebook`. Stop if it is absent or ambiguous; never guess another tab.
4. Read only the two existing-state columns:
   - `python google_api.py sheets get SPREADSHEET_ID "Facebook!B2:B"` for PIC.
   - `python google_api.py sheets get SPREADSHEET_ID "Facebook!F2:F"` for LINK.
   Preserve row positions and represent an empty cell as `""`. Never read the existing MESSAGE column.
5. Call `mcp_secure_proxy_social_fetch_facebook_posts` with `{}`. Require `fetchedAt`, `items`, and `warnings`; stop on a tool error.
6. Classify every fetched post, leaving deduplication to the script. Assign exactly one TOPIC: `Career Advice`, `Tech news`, `DSV's member sharing`, `DSV's services`, `DSV's news`, `Blog Post Sharing`, `Promotion`, `Email`, `Knowledge sharing`, `Other`, `Case study`, or `Meme`. Use `Other` for a null or empty message.
7. Map `postType` to FORMAT: `photo` to `Ảnh`, `video` to `Video`, and `text` or null to `Văn bản`. Do not invent metrics; preserve null values.
8. Run the planner with every fetched post, including `topic` and `format`:

   ```bash
   PLAN_SCRIPT="${HERMES_HOME:-$HOME/.hermes}/skills/facebook-post-report-sync/scripts/plan_sheet_updates.py"
   python "$PLAN_SCRIPT" <<'JSON'
   {"pic_column": [], "link_column": [], "fetched_posts": []}
   JSON
   ```

   Supply the real arrays and posts as JSON. Each post must include `postUrl`, `message`, `publishedAt`, `format`, `topic`, `impressions`, `reach`, `totalClicks`, `linkClicks`, `numReactions`, `numComments`, and `numShares`.
9. Parse `existing_link_count`, `placeholder_row_count`, and `writes`. If `writes` is empty, report that the sheet is up to date and make no write calls.
10. Execute each planned write in order with the `python google_api.py sheets update` command. Pass `SPREADSHEET_ID`, `Facebook!RANGE`, `--values`, and the JSON-encoded `values` as separate process arguments; never build a shell command by interpolating post content. Use the script's range unchanged. A placeholder write must remain `C:M`; never expand it to include column B. An appended write uses `B:M` and the script-provided default PIC.
11. Report fetched count, already-present count (`items` count minus `writes` count), placeholder writes, appended writes, and every fetch warning verbatim. Do not request another confirmation before writing.

## Failure

Stop on a failed fetch, metadata read, column read, or Sheets write and report the exact error. Never expose credentials, invent metrics, guess a tab, retry with changed data, or write column B for a placeholder row.
