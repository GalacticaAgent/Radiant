from app.utils.format_review_skill import SKILL_DESCRIPTION_FIXED, is_valid_skill_name, render_skill_markdown


def test_skill_name_validation():
    assert is_valid_skill_name("abc")
    assert is_valid_skill_name("a1_b2-c3")
    assert not is_valid_skill_name("Aaa")
    assert not is_valid_skill_name("1abc")
    assert not is_valid_skill_name("ab")


def test_render_skill_markdown_contains_frontmatter_and_sections():
    content = {
        "name": "测试规则",
        "summary": "这是一段摘要",
        "source_file": "rule.docx",
        "executable_rules": [
            {"check_type": "docx_normal_size_pt", "description": "正文字号应为 10.5", "suggestion": "设置为五号"},
        ],
        "llm_rules": [
            {"description": "参考文献数量应不少于 15", "check_method": "统计参考文献段落", "suggestion": "补充参考文献"},
        ],
    }
    md = render_skill_markdown(skill_name="custom_rule_v1", description=SKILL_DESCRIPTION_FIXED, rule_content=content)
    assert md.startswith("---")
    assert "name:" in md
    assert "description:" in md
    assert "# 论文格式审查技能" in md
    assert "## 自动化检查（硬规则）" in md
    assert "docx_normal_size_pt" in md
    assert "## LLM 辅助检查（软规则）" in md
    assert "参考文献数量应不少于 15" in md

