from __future__ import annotations

from zc_agent_desk.workflows import default_registry
from zc_agent_desk.workflows.keyword_analysis import KeywordAnalysisWorkflow


def test_registry_matches_keyword_analysis_without_misclassifying_chat() -> None:
    registry = default_registry()

    workflow = registry.match("分析 2026年6月飘窗垫的关键词需求")

    assert workflow is not None
    assert workflow.name == "关键词分析"
    assert registry.match("你好，记住我叫小雁") is None


def test_extracts_iso_chinese_and_current_year_months() -> None:
    workflow = KeywordAnalysisWorkflow()

    assert workflow.extract_parameters("分析 2026-06 飘窗垫的关键词需求") == {
        "year_month": "2026-06",
        "category_name": "飘窗垫",
    }
    assert workflow.extract_parameters("分析 2026年6月办公背包关键词") == {
        "year_month": "2026-06",
        "category_name": "办公背包",
    }
    assert workflow.extract_parameters("分析6月飘窗垫关键词") == {
        "year_month": "2026-06",
        "category_name": "飘窗垫",
    }


def test_missing_parameters_return_clarification() -> None:
    result = KeywordAnalysisWorkflow().execute("帮我做关键词需求分析")

    assert result.clarification is True
    assert "月份" in result.content
    assert "类目" in result.content


def test_analysis_covers_eight_types_and_calculates_growth() -> None:
    workflow = KeywordAnalysisWorkflow()
    rows = workflow.load_rows("飘窗垫", "2026-06")

    analysis = workflow.analyze(rows)

    assert set(analysis["requirements"]) == set(workflow.REQUIREMENT_TYPES)
    assert all(len(items) <= 20 for items in analysis["requirements"].values())
    assert all(
        items == sorted(items, key=lambda item: item["search_popularity"], reverse=True)
        for items in analysis["requirements"].values()
    )
    assert abs(sum(item["share"] for item in analysis["summary"]) - 100) <= 0.1
    assert analysis["high_growth"]
    assert all(
        item["search_popularity"] >= 10_000 and item["mom_growth"] >= 15
        for item in analysis["high_growth"]
    )


def test_execute_returns_six_observable_steps_and_deterministic_report() -> None:
    result = KeywordAnalysisWorkflow().execute("分析 2026-06 飘窗垫的关键词需求")

    assert result.clarification is False
    assert len(result.steps) == 6
    assert [step["label"] for step in result.steps] == [
        "识别关键词分析 Workflow",
        "提取月份与类目",
        "查询合成关键词数据",
        "分类八大需求",
        "计算趋势与高增长词根",
        "生成分析结果",
    ]
    assert "关键词分析" in result.content
    assert "飘窗垫" in result.content
    assert "行动建议" in result.content
