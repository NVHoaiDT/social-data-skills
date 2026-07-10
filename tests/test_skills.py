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
    "x-traffic-sync": (
        "mcp_secure_proxy_social_fetch_x_posts",
        "mcp_social_dashboard_update_dsv_x_posts",
    ),
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
    assert skill_files == {f"{name}/SKILL.md" for name in EXPECTED}
    names = []
    for path in files:
        frontmatter, _ = parse_skill(path)
        names.append(frontmatter["name"])
        assert frontmatter["name"] == path.parent.name
        assert frontmatter["version"] == "1.0.0"
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


def test_readme_documents_install_update_and_default_jobs():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in EXPECTED:
        assert f"designveloper/social-data-skills/skills/{name}" in readme
        assert f"hermes skills update {name}" in readme
    for job_name in (
        "Update Google Trends",
        "Update Tech News",
        "Update Competitor Content",
        "Update Facebook Traffic",
        "Update X Traffic",
    ):
        assert job_name in readme
