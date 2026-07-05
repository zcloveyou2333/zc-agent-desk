from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from importlib.resources import files
from typing import Any

from .base import WorkflowResult


class KeywordAnalysisWorkflow:
    name = "关键词分析"
    REQUIREMENT_TYPES = (
        "品类需求", "属性需求", "人群需求", "风格需求",
        "场景需求", "功能需求", "品牌需求", "定制需求",
    )
    SUPPORTED_CATEGORIES = ("飘窗垫", "办公背包")

    def matches(self, message: str) -> bool:
        return bool(
            re.search(r"关键词(?:需求|分析)", message)
            or re.search(r"分析.*关键词", message)
        )

    def extract_parameters(self, message: str) -> dict[str, str | None]:
        iso = re.search(r"(20\d{2})[-/](0?[1-9]|1[0-2])", message)
        chinese = re.search(r"(20\d{2})年(0?[1-9]|1[0-2])月", message)
        month_only = re.search(r"(?<!年)(?<!\d)(0?[1-9]|1[0-2])月", message)
        if iso:
            year_month = f"{iso.group(1)}-{int(iso.group(2)):02d}"
        elif chinese:
            year_month = f"{chinese.group(1)}-{int(chinese.group(2)):02d}"
        elif month_only:
            year_month = f"{datetime.now(UTC).year}-{int(month_only.group(1)):02d}"
        else:
            year_month = None
        category = next((item for item in self.SUPPORTED_CATEGORIES if item in message), None)
        return {"year_month": year_month, "category_name": category}

    def load_rows(self, category_name: str, year_month: str) -> list[dict[str, Any]]:
        path = files("zc_agent_desk.workflows").joinpath("synthetic_keywords.json")
        rows = json.loads(path.read_text(encoding="utf-8"))
        return [
            row for row in rows
            if row["category"] == category_name and row["month"] == year_month
        ]

    def analyze(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        requirements = {item: [] for item in self.REQUIREMENT_TYPES}
        for row in rows:
            requirement_type = row.get("requirement_type")
            if requirement_type in requirements:
                requirements[requirement_type].append(dict(row))
        for requirement_type in requirements:
            requirements[requirement_type] = sorted(
                requirements[requirement_type],
                key=lambda item: item["search_popularity"],
                reverse=True,
            )[:20]
        totals = {
            name: sum(item["search_popularity"] for item in items)
            for name, items in requirements.items()
        }
        grand_total = sum(totals.values())
        summary = [
            {
                "requirement_type": name,
                "search_popularity": totals[name],
                "share": round(totals[name] / grand_total * 100, 2) if grand_total else 0,
            }
            for name in self.REQUIREMENT_TYPES
        ]
        all_rows = [item for items in requirements.values() for item in items]
        high_growth = sorted(
            [
                item for item in all_rows
                if item["search_popularity"] >= 10_000 and item["mom_growth"] >= 15
            ],
            key=lambda item: (item["mom_growth"], item["search_popularity"]),
            reverse=True,
        )
        return {"requirements": requirements, "summary": summary, "high_growth": high_growth}

    def execute(self, message: str) -> WorkflowResult:
        params = self.extract_parameters(message)
        steps = [
            {"tool": "workflow.keyword.identify", "label": "识别关键词分析 Workflow", "result": {"workflow": self.name}},
            {"tool": "workflow.keyword.extract", "label": "提取月份与类目", "result": params},
        ]
        missing = [label for key, label in (("year_month", "月份"), ("category_name", "类目")) if not params[key]]
        if missing:
            supported = "、".join(self.SUPPORTED_CATEGORIES)
            content = f"请补充{'和'.join(missing)}。示例：分析 2026-06 飘窗垫的关键词需求。支持的演示类目：{supported}。"
            return WorkflowResult(content=content, steps=steps, clarification=True)

        rows = self.load_rows(str(params["category_name"]), str(params["year_month"]))
        steps.append({"tool": "workflow.keyword.query", "label": "查询合成关键词数据", "result": {"row_count": len(rows)}})
        if not rows:
            content = f"没有找到 {params['category_name']} 在 {params['year_month']} 的合成数据。当前演示月份为 2026-06。"
            return WorkflowResult(content=content, steps=steps, clarification=True)

        analysis = self.analyze(rows)
        steps.extend([
            {"tool": "workflow.keyword.classify", "label": "分类八大需求", "result": {"requirement_count": 8}},
            {"tool": "workflow.keyword.trends", "label": "计算趋势与高增长词根", "result": {"high_growth_count": len(analysis["high_growth"])}},
        ])
        strongest = max(analysis["summary"], key=lambda item: item["share"])
        growth = analysis["high_growth"][0] if analysis["high_growth"] else None
        content = (
            f"## {params['category_name']} · {params['year_month']} 关键词分析\n\n"
            f"八大需求中，**{strongest['requirement_type']}**搜索人气最高，占比 {strongest['share']:.2f}%。"
        )
        if growth:
            content += f" 高增长词根首位是“{growth['word_root']}”，环比增长 {growth['mom_growth']:.1f}%。"
        content += "\n\n**行动建议**：优先围绕高需求方向配置核心款，并用高增长词根验证趋势款卖点。"
        steps.append({"tool": "workflow.keyword.render", "label": "生成分析结果", "result": {"top_requirement": strongest["requirement_type"]}})
        return WorkflowResult(content=content, steps=steps)
