from app.services.format_rule_engine import FormatRuleEngine


def test_custom_exec_rule_overrides_default_when_replace():
    content = {
        "mode": "replace",
        "executable_rules": [
            {
                "id": "title30",
                "severity": "major",
                "check_type": "title_cn_max_chars",
                "params": {"max": 30},
                "description": "标题中文字符数不超过 30",
                "suggestion": "缩短标题",
            }
        ],
        "llm_rules": [],
    }
    res = FormatRuleEngine.analyze(
        paper_title="这是一个用于测试的超长中文标题" * 4,
        abstract="这是摘要",
        paper_content="正文",
        full_text=None,
        source_type="text",
        docx_style_snapshot=None,
        custom_rule_content=content,
    )
    issues = res.get("rule_issues") or []
    assert isinstance(issues, list)
    assert len(issues) == 1
    assert issues[0]["position"] == "封面/标题"


def test_custom_exec_rule_augments_default_when_augment():
    content = {
        "mode": "augment",
        "executable_rules": [
            {
                "id": "refs20",
                "severity": "major",
                "check_type": "references_min_count",
                "params": {"min": 20},
                "description": "参考文献不少于 20 条",
                "suggestion": "补充参考文献",
            }
        ],
        "llm_rules": [],
    }
    full_text = "参考文献\n[1] A\n[2] B\n[3] C\n"
    res = FormatRuleEngine.analyze(
        paper_title="短标题",
        abstract="摘要" * 200,
        paper_content=full_text,
        full_text=full_text,
        source_type="text",
        docx_style_snapshot=None,
        custom_rule_content=content,
    )
    issues = res.get("rule_issues") or []
    assert any("参考文献不少于 20 条" in (it.get("description") or "") for it in issues)
