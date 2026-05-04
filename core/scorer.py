"""
质量评分系统：9维度评分 + 自动重试
移植自 Content Repurser 的质量控制理念
"""

import json
import re
from typing import Dict, Any, Optional
from core.generator import AIGenerator


class QualityScorer:
    """内容质量评分器"""

    # 评分维度定义
    DIMENSIONS = {
        "information_completeness": {"name": "信息完整性", "weight": 0.15},
        "platform_fit": {"name": "平台适配度", "weight": 0.15},
        "fluency": {"name": "语言流畅度", "weight": 0.15},
        "technical_accuracy": {"name": "技术准确性", "weight": 0.15},
        "attractiveness": {"name": "吸引力", "weight": 0.10},
        "readability": {"name": "可读性", "weight": 0.10},
        "style_consistency": {"name": "风格一致性", "weight": 0.10},
        "cta_completeness": {"name": "CTA完整性", "weight": 0.05},
        "originality": {"name": "原创性", "weight": 0.05},
    }

    def __init__(self, ai_generator: Optional[AIGenerator] = None):
        self.ai_generator = ai_generator

    def score(
        self,
        platform: str,
        generated_content: dict,
        original_key_points: str,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        对生成的内容进行质量评分

        Args:
            platform: 目标平台
            generated_content: 生成的内容
            original_key_points: 原文关键观点
            use_ai: 是否使用AI进行评分（否则使用规则评分）

        Returns:
            评分结果字典
        """
        if use_ai and self.ai_generator:
            return self._ai_score(platform, generated_content, original_key_points)
        else:
            return self._rule_score(platform, generated_content, original_key_points)

    def _ai_score(
        self,
        platform: str,
        generated_content: dict,
        original_key_points: str,
    ) -> Dict[str, Any]:
        """使用AI进行质量评分"""
        from config.prompts import QUALITY_SCORE_PROMPT

        # 格式化生成内容
        if platform == "x":
            content_text = "\n".join(generated_content.get("tweets", []))
        elif platform == "xiaohongshu":
            content_text = f"标题: {generated_content.get('title', '')}\n\n正文: {generated_content.get('content', '')}"
        else:
            content_text = generated_content.get("content", "")

        prompt = QUALITY_SCORE_PROMPT.format(
            original_key_points=original_key_points,
            platform=platform,
            generated_content=content_text,
        )

        try:
            response = self.ai_generator._call_ai(prompt, max_tokens=2000)

            # 解析JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return self._format_score_result(data)
        except Exception as e:
            print(f"AI评分失败，回退到规则评分: {e}")

        return self._rule_score(platform, generated_content, original_key_points)

    def _rule_score(
        self,
        platform: str,
        generated_content: dict,
        original_key_points: str,
    ) -> Dict[str, Any]:
        """使用规则进行质量评分"""
        scores = {}

        # 提取生成内容的文本
        if platform == "x":
            content_text = "\n".join(generated_content.get("tweets", []))
        elif platform == "xiaohongshu":
            content_text = f"{generated_content.get('title', '')}\n{generated_content.get('content', '')}"
        else:
            content_text = generated_content.get("content", "")

        # 1. 信息完整性
        key_points_count = len([p for p in original_key_points.split("\n") if p.strip().startswith("-")])
        covered_points = sum(1 for p in original_key_points.split("\n") if p.strip() and any(kw in content_text for kw in p.strip().split()[:3]))
        scores["information_completeness"] = min(10, max(5, covered_points / max(key_points_count, 1) * 10))

        # 2. 平台适配度
        if platform == "x":
            tweets = generated_content.get("tweets", [])
            char_ok = all(len(t) <= 280 for t in tweets)
            scores["platform_fit"] = 9 if char_ok else 6
        elif platform == "xiaohongshu":
            has_emoji = any(ord(c) > 0x1F300 for c in content_text)
            has_tags = len(generated_content.get("tags", [])) >= 5
            scores["platform_fit"] = 9 if (has_emoji and has_tags) else 7
        else:
            scores["platform_fit"] = 8  # 知乎默认较好

        # 3. 语言流畅度
        scores["fluency"] = 8 if len(content_text) > 100 else 6

        # 4. 技术准确性
        has_code = "```" in content_text or "`" in content_text
        scores["technical_accuracy"] = 8 if has_code else 7

        # 5. 吸引力
        first_line = content_text.split("\n")[0] if content_text else ""
        has_hook = any(c in first_line for c in ["!", "！", "?", "？", "🔥", "💡", "🚀"])
        scores["attractiveness"] = 9 if has_hook else 7

        # 6. 可读性
        paragraphs = [p for p in content_text.split("\n\n") if p.strip()]
        avg_para_len = sum(len(p) for p in paragraphs) / max(len(paragraphs), 1)
        scores["readability"] = 9 if avg_para_len < 200 else 7

        # 7. 风格一致性
        scores["style_consistency"] = 7  # 默认中等

        # 8. CTA完整性
        has_cta = any(kw in content_text.lower() for kw in ["关注", "收藏", "评论", "follow", "share", "like", "bookmark"])
        scores["cta_completeness"] = 9 if has_cta else 5

        # 9. 原创性
        scores["originality"] = 8  # 默认较好

        return self._format_score_result({"scores": scores, "suggestions": []})

    def _format_score_result(self, data: dict) -> Dict[str, Any]:
        """格式化评分结果"""
        scores = data.get("scores", {})

        # 确保所有维度都有分数
        for key in self.DIMENSIONS:
            if key not in scores:
                scores[key] = 7.0

        # 计算加权总分
        total = 0
        for key, config in self.DIMENSIONS.items():
            score = float(scores.get(key, 7.0))
            total += score * config["weight"]

        # 生成改进建议
        suggestions = data.get("suggestions", [])
        if not suggestions:
            suggestions = self._generate_suggestions(scores)

        return {
            "total_score": round(total, 1),
            "scores": {config["name"]: round(float(scores.get(key, 7.0)), 1) for key, config in self.DIMENSIONS.items()},
            "suggestions": suggestions[:3],  # 最多返回3条建议
            "passed": total >= 7.0,
            "excellent": total >= 8.5,
        }

    def _generate_suggestions(self, scores: dict) -> list:
        """基于分数生成改进建议"""
        suggestions = []

        if scores.get("information_completeness", 7) < 7:
            suggestions.append("建议补充更多原文核心技术点")
        if scores.get("platform_fit", 7) < 7:
            suggestions.append("建议调整内容以更好适配目标平台风格")
        if scores.get("attractiveness", 7) < 7:
            suggestions.append("建议优化开头以提高吸引力")
        if scores.get("cta_completeness", 7) < 7:
            suggestions.append("建议添加行动引导语（关注/收藏/评论）")
        if scores.get("readability", 7) < 7:
            suggestions.append("建议缩短段落长度，增加留白")

        return suggestions if suggestions else ["内容质量良好，可进一步优化细节"]
