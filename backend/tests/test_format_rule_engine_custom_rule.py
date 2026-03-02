from app.services.format_rule_engine import FormatRuleEngine


def test_custom_rule_exec_rules_are_applied_and_reported():
    paper = "标题\n\n摘要\n关键词：A；B；C\n\n目录\n\n参考文献\n[1] x\n"
    snapshot = {"has_header": False, "has_footer": True, "has_page_number": False, "styles": {"Normal": {"font": "宋体", "size_pt": 10.5, "line_spacing_pt": 20.0}}}
    custom = {
        "mode": "augment",
        "executable_rules": [
            {
                "id": "need_page_number",
                "severity": "major",
                "check_type": "docx_require_page_number",
                "params": {},
                "description": "正文必须有页码",
                "suggestion": "插入页码字段 PAGE",
            }
        ],
    }
    out = FormatRuleEngine.analyze(
        paper_title="标题",
        abstract="摘要",
        paper_content=paper,
        full_text=paper,
        source_type="docx",
        docx_style_snapshot=snapshot,
        custom_rule_content=custom,
    )
    assert out["auto_metrics"]["custom_exec_rules_count"] == 1
    assert out["auto_metrics"]["custom_rule_mode"] == "augment"
    assert any("页码" in (x.get("description") or "") for x in out["rule_issues"])


def test_custom_rule_replace_mode_overrides_default_issues():
    paper = "标题\n\n"  # will trigger several default checks, but replace should keep only custom issues
    snapshot = {"has_header": False, "has_footer": False, "has_page_number": False, "styles": {}}
    custom = {
        "mode": "replace",
        "executable_rules": [
            {
                "id": "need_footer",
                "severity": "major",
                "check_type": "docx_require_footer",
                "params": {},
                "description": "必须有页脚",
                "suggestion": "添加页脚",
            }
        ],
    }
    out = FormatRuleEngine.analyze(
        paper_title="标题",
        abstract="",
        paper_content=paper,
        full_text=paper,
        source_type="docx",
        docx_style_snapshot=snapshot,
        custom_rule_content=custom,
    )
    assert out["auto_metrics"]["custom_rule_mode"] == "replace"
    assert len(out["rule_issues"]) == 1
    assert "页脚" in (out["rule_issues"][0].get("description") or "")

