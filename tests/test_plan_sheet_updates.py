import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "skills"
        / "facebook-post-report-sync"
        / "scripts"
    ),
)

from plan_sheet_updates import plan_sheet_updates  # noqa: E402


def _make_post(**overrides):
    post = {
        "postUrl": "https://facebook.com/1",
        "message": "Hello",
        "publishedAt": "2026-07-01T09:00:00+0000",
        "format": "Ảnh",
        "topic": "Tech news",
        "impressions": 100,
        "reach": 60,
        "totalClicks": 5,
        "linkClicks": 1,
        "numReactions": 3,
        "numComments": 2,
        "numShares": 1,
    }
    post.update(overrides)
    return post


def test_posts_whose_link_already_exists_are_never_written():
    pic_column = ["Ms. Tran"]
    link_column = ["https://facebook.com/already-here"]
    fetched = [
        _make_post(postUrl="https://facebook.com/already-here"),
        _make_post(
            postUrl="https://facebook.com/new-one",
            publishedAt="2026-07-02T09:00:00+0000",
        ),
    ]

    result = plan_sheet_updates(pic_column, link_column, fetched)

    assert len(result["writes"]) == 1
    assert result["writes"][0]["values"][0][4] == "https://facebook.com/new-one"


def test_duplicate_links_in_one_fetch_are_written_once():
    fetched = [
        _make_post(
            postUrl="https://facebook.com/duplicate",
            publishedAt="2026-07-02T09:00:00+0000",
        ),
        _make_post(
            postUrl="https://facebook.com/duplicate",
            publishedAt="2026-07-01T09:00:00+0000",
        ),
    ]

    result = plan_sheet_updates([], [], fetched)

    assert len(result["writes"]) == 1
    assert result["writes"][0]["values"][0][3] == "2026-07-01T09:00:00+0000"


def test_mid_sheet_placeholder_is_detected_not_only_trailing():
    pic_column = ["Ms. Tran", "Ms. Tran", "Ms. Tran"]
    link_column = [
        "https://facebook.com/existing-1",
        "",
        "https://facebook.com/existing-3",
    ]
    fetched = [
        _make_post(
            postUrl="https://facebook.com/new-1",
            publishedAt="2026-07-05T09:00:00+0000",
        )
    ]

    result = plan_sheet_updates(pic_column, link_column, fetched)

    assert result["placeholder_row_count"] == 1
    assert result["writes"] == [
        {
            "row": 3,
            "range": "C3:M3",
            "values": [
                [
                    "Tech news",
                    "Hello",
                    "2026-07-05T09:00:00+0000",
                    "https://facebook.com/new-1",
                    "Ảnh",
                    100,
                    60,
                    6,
                    5,
                    1,
                    1,
                ]
            ],
            "kind": "placeholder",
        }
    ]


def test_exhausted_placeholders_then_appends_remaining():
    pic_column = ["Ms. Tran"]
    link_column = [""]
    fetched = [
        _make_post(
            postUrl="https://facebook.com/new-1",
            publishedAt="2026-07-01T09:00:00+0000",
        ),
        _make_post(
            postUrl="https://facebook.com/new-2",
            publishedAt="2026-07-02T09:00:00+0000",
        ),
    ]

    result = plan_sheet_updates(pic_column, link_column, fetched)

    assert [write["kind"] for write in result["writes"]] == [
        "placeholder",
        "appended",
    ]
    assert result["writes"][0]["row"] == 2
    assert result["writes"][1]["row"] == 3
    assert result["writes"][1]["range"] == "B3:M3"
    assert result["writes"][1]["values"][0][0] == "Ms. Tran"


def test_empty_sheet_appends_starting_at_row_two():
    result = plan_sheet_updates([], [], [_make_post()])

    assert result["writes"][0]["row"] == 2
    assert result["writes"][0]["range"] == "B2:M2"


def test_placeholder_write_range_never_includes_column_b():
    result = plan_sheet_updates(["Ms. Tran"], [""], [_make_post()])

    range_start = result["writes"][0]["range"].split(":")[0]
    assert range_start.startswith("C")
    assert "B" not in range_start


def test_missing_posts_are_written_oldest_first_regardless_of_input_order():
    newer = _make_post(
        postUrl="https://facebook.com/newer",
        publishedAt="2026-07-10T09:00:00+0000",
    )
    older = _make_post(
        postUrl="https://facebook.com/older",
        publishedAt="2026-07-01T09:00:00+0000",
    )

    result = plan_sheet_updates([], [], [newer, older])

    assert result["writes"][0]["values"][0][4] == "https://facebook.com/older"
    assert result["writes"][1]["values"][0][4] == "https://facebook.com/newer"


def test_null_metrics_become_blank_not_zero():
    post = _make_post(
        impressions=None,
        reach=None,
        totalClicks=None,
        linkClicks=None,
    )

    result = plan_sheet_updates([], [], [post])

    values = result["writes"][0]["values"][0]
    assert values[6] == ""
    assert values[7] == ""
    assert values[9] == ""
    assert values[10] == ""
    assert values[8] == (
        post["numReactions"] + post["numComments"] + post["numShares"]
    )
