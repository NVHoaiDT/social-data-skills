#!/usr/bin/env python3
"""Compute deterministic Google Sheets writes for Facebook report sync."""
from __future__ import annotations

import json
import sys
from typing import Any


HEADER_OFFSET = 2
DEFAULT_PIC = "Ms. Tran"


def _blank_if_none(value: Any) -> Any:
    return "" if value is None else value


def _row_values(post: dict[str, Any]) -> list[Any]:
    return [
        post["topic"],
        post.get("message") or "",
        post["publishedAt"],
        post["postUrl"],
        post["format"],
        _blank_if_none(post.get("impressions")),
        _blank_if_none(post.get("reach")),
        post["numReactions"] + post["numComments"] + post["numShares"],
        _blank_if_none(post.get("totalClicks")),
        _blank_if_none(post.get("linkClicks")),
        post["numShares"],
    ]


def plan_sheet_updates(
    pic_column: list[str],
    link_column: list[str],
    fetched_posts: list[dict[str, Any]],
) -> dict[str, Any]:
    existing_links = {link.strip() for link in link_column if link.strip()}
    posts = []
    seen_links = set(existing_links)
    for post in sorted(fetched_posts, key=lambda item: item["publishedAt"]):
        post_url = post["postUrl"]
        if post_url in seen_links:
            continue
        seen_links.add(post_url)
        posts.append(post)

    row_count = max(len(pic_column), len(link_column))
    placeholder_rows = []
    for index in range(row_count):
        pic = pic_column[index] if index < len(pic_column) else ""
        link = link_column[index] if index < len(link_column) else ""
        if pic.strip() and not link.strip():
            placeholder_rows.append(HEADER_OFFSET + index)

    writes = []
    post_index = 0
    for row in placeholder_rows:
        if post_index >= len(posts):
            break
        writes.append(
            {
                "row": row,
                "range": f"C{row}:M{row}",
                "values": [_row_values(posts[post_index])],
                "kind": "placeholder",
            }
        )
        post_index += 1

    next_row = HEADER_OFFSET + row_count
    while post_index < len(posts):
        writes.append(
            {
                "row": next_row,
                "range": f"B{next_row}:M{next_row}",
                "values": [[DEFAULT_PIC, *_row_values(posts[post_index])]],
                "kind": "appended",
            }
        )
        post_index += 1
        next_row += 1

    return {
        "existing_link_count": len(existing_links),
        "placeholder_row_count": len(placeholder_rows),
        "writes": writes,
    }


def main() -> None:
    payload = json.load(sys.stdin)
    result = plan_sheet_updates(
        pic_column=payload.get("pic_column", []),
        link_column=payload.get("link_column", []),
        fetched_posts=payload.get("fetched_posts", []),
    )
    json.dump(result, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
