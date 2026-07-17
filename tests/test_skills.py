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
    "tech-news-sync": "1.2.0",
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


def collect_skill_files(skills: Path) -> set[str]:
    return {
        path.relative_to(skills).as_posix()
        for path in skills.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def test_skill_file_listing_ignores_python_bytecode(tmp_path):
    skills = tmp_path / "skills"
    skill = skills / "example-skill"
    (skill / "scripts" / "__pycache__").mkdir(parents=True)
    (skill / "SKILL.md").write_text("skill", encoding="utf-8")
    (skill / "scripts" / "tool.py").write_text("pass\n", encoding="utf-8")
    (skill / "scripts" / "__pycache__" / "tool.cpython-312.pyc").write_bytes(
        b"bytecode"
    )

    assert collect_skill_files(skills) == {
        "example-skill/SKILL.md",
        "example-skill/scripts/tool.py",
    }


def test_exact_skill_set_and_frontmatter():
    files = sorted(SKILLS.glob("*/SKILL.md"))
    assert {path.parent.name for path in files} == set(EXPECTED)
    skill_files = collect_skill_files(SKILLS)
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


def test_tech_news_skill_defines_plan_handoff_contract():
    _, text = parse_skill(SKILLS / "tech-news-sync" / "SKILL.md")

    for field in (
        "suggestedTopic",
        "suggestedMessage",
        "suggestedPlatforms",
        "suggestedDesignBrief",
    ):
        assert field in text

    expected_topics = (
        "Career Advice",
        "Tech news",
        "DSV's member sharing",
        "DSV's services",
        "DSV's news",
        "Blog Post Sharing",
        "Promotion",
        "Email",
        "Knowledge sharing",
        "Other",
        "Case study",
        "Meme",
    )
    topic_match = re.search(
        r"`suggestedTopic`: exactly one of (.*?)\. Classify",
        text,
    )
    assert topic_match
    assert tuple(re.findall(r"`([^`]+)`", topic_match.group(1))) == expected_topics

    platform_match = re.search(
        r"`suggestedPlatforms`: one or more unique values from (.*?)\.",
        text,
    )
    assert platform_match
    assert tuple(re.findall(r"`([^`]+)`", platform_match.group(1))) == (
        "Facebook",
        "LinkedIn",
        "X",
    )

    assert "concise one-line content title or idea" in text
    assert "not complete social post copy" in text
    for brief_label in ("Headline:", "Background:", "Describe:"):
        assert brief_label in text
    for hardcoded_brief in (
        "Size: 1920x1920",
        "Color: Designveloper branding",
        "Topic: <what the visual communicates>",
        "Description:",
    ):
        assert hardcoded_brief not in text
    assert "Do not force `Size`, `Color`, `Topic`" in text
    assert "marketing team's existing Plan briefs" in text
    assert "as many bullets or subsections as useful" in text
    assert "all four Plan suggestion fields to `null`" in text
