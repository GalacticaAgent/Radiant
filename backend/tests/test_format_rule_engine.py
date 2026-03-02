from app.services.format_rule_engine import FormatRuleEngine


def test_rules_detect_reference_and_keywords_issues():
    text = "\n".join(
        [
            "摘要",
            "这是一个摘要。",
            "关键词：机器学习；异常检测",
            "正文中引用如[1]所示。",
            "参考文献",
            "[1] Foo. Bar[J]. Journal, 2022(1):1-2.",
        ]
    )
    res = FormatRuleEngine.analyze(
        paper_title="长" * 40,
        abstract="这是一个摘要。",
        paper_content=text,
        full_text=text,
        source_type="text",
        docx_style_snapshot=None,
    )
    issues = res["rule_issues"]
    assert any("标题" in x.get("position", "") for x in issues)
    assert any("关键词数量" in x.get("description", "") for x in issues)
    assert any("参考文献条目" in x.get("description", "") for x in issues)


def test_rules_accept_reasonable_keywords_count():
    text = "\n".join(
        [
            "摘要",
            "这是一个摘要。",
            "关键词：A；B；C",
            "参考文献",
            "[1] Foo. 2022.",
            "[2] Bar. 2023.",
            "[3] Baz. 2024.",
            "[4] Qux. 2020.",
            "[5] Quux. 2019.",
            "[6] Corge. 2018.",
            "[7] Grault. 2017.",
            "[8] Garply. 2021.",
            "[9] Waldo. 2022.",
            "[10] Fred. 2020.",
            "[11] Plugh. 2019.",
            "[12] Xyzzy. 2023.",
            "[13] Thud. 2024.",
            "[14] 中文作者. 2022.",
            "[15] 中文作者. 2023.",
        ]
    )
    res = FormatRuleEngine.analyze(
        paper_title="短标题",
        abstract="这是一个摘要。",
        paper_content=text,
        full_text=text,
        source_type="text",
        docx_style_snapshot=None,
    )
    issues = res["rule_issues"]
    assert not any("关键词数量" in x.get("description", "") for x in issues)
