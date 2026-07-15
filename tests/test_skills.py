from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED = {
    "google-trends-sync": (
        "mcp_secure_proxy_social_fetch_google_trends",
        "mcp_social_dashboard_update_trends",
    ),
    "tech-news-sync": (
        "mcp_secure_proxy_social_fetch_tech_news",
        "mcp_social_dashboard_update_news",
    ),
    "competitor-content-sync": (
        "mcp_secure_proxy_social_fetch_competitor_posts",
        "mcp_social_dashboard_update_competitor_contents",
    ),
    "facebook-traffic-sync": (
        "mcp_secure_proxy_social_fetch_facebook_posts",
        "mcp_social_dashboard_update_dsv_facebook_posts",
    ),
    "facebook-post-report-sync": (
        "mcp_secure_proxy_social_fetch_facebook_posts",
        "google_api.py sheets update",
    ),
    "x-traffic-sync": (
        "mcp_secure_proxy_social_fetch_x_posts",
        "mcp_social_dashboard_update_dsv_x_posts",
    ),
    "traffic-analysis": (
        "mcp_social_dashboard_get_traffic_posts",
        "mcp_social_dashboard_create_visualization_blocks",
    ),
}
EXPECTED_VERSIONS = {
    "google-trends-sync": "1.0.0",
    "tech-news-sync": "1.0.0",
    "competitor-content-sync": "1.0.0",
    "facebook-traffic-sync": "2.1.0",
    "facebook-post-report-sync": "1.0.0",
    "x-traffic-sync": "2.0.0",
    "traffic-analysis": "1.0.0",
}

# This skill's exact-link deduplication and placeholder matching are
# correctness-critical, so it carries one credential-free deterministic script.
EXTRA_FILES = {
    "facebook-post-report-sync": ["scripts/plan_sheet_updates.py"],
}
FORBIDDEN = [
    "MCP_JWT_SECRET",
    "__PROXY_ENV__",
    "proxy.local",
    "/opt/data",
    "/opt/team-skills",
    "mattermost_users",
    "x59sinq9pjdotm5bebj785hyka",
]


def parse_skill(path: Path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, f"{path} has no YAML frontmatter"
    return yaml.safe_load(match.group(1)), text


def test_exact_skill_set_and_frontmatter():
    files = sorted(SKILLS.glob("*/SKILL.md"))
    assert {path.parent.name for path in files} == set(EXPECTED)
    skill_files = {
        path.relative_to(SKILLS).as_posix()
        for path in SKILLS.rglob("*")
        if path.is_file()
    }
    expected_files = {f"{name}/SKILL.md" for name in EXPECTED}
    for name, extras in EXTRA_FILES.items():
        expected_files.update(f"{name}/{extra}" for extra in extras)
    assert skill_files == expected_files
    names = []
    for path in files:
        frontmatter, _ = parse_skill(path)
        names.append(frontmatter["name"])
        assert frontmatter["name"] == path.parent.name
        assert frontmatter["version"] == EXPECTED_VERSIONS[path.parent.name]
        assert len(frontmatter["description"]) <= 60
        assert frontmatter["description"].endswith(".")
        assert "required_environment_variables" not in frontmatter
    assert len(names) == len(set(names))


def test_each_skill_names_its_exact_fetch_and_write_tools():
    for name, (fetch_tool, write_tool) in EXPECTED.items():
        _, text = parse_skill(SKILLS / name / "SKILL.md")
        assert fetch_tool in text
        assert write_tool in text


def test_public_files_contain_no_private_credentials_or_paths():
    public_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "tests" not in path.parts
    ]
    for path in public_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for forbidden in FORBIDDEN:
            assert forbidden not in text, f"{path} contains forbidden text {forbidden!r}"


def test_readme_documents_install_and_update():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in EXPECTED:
        assert f"designveloper/social-data-skills/skills/{name}" in readme
        assert f"hermes skills update {name}" in readme


def test_public_files_have_no_cron_commands_or_tags():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "hermes cron" not in readme

    for name in EXPECTED:
        frontmatter, _ = parse_skill(SKILLS / name / "SKILL.md")
        assert "cron" not in frontmatter["metadata"]["hermes"]["tags"]
