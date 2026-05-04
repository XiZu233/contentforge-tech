"""
AI生成引擎：调用Claude/OpenAI API生成各平台内容
"""

import os
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from config.prompts import get_prompt, STYLE_LEARNING_PROMPT
from config.platforms import detect_language


class AIGenerator:
    """AI内容生成器"""

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("DEFAULT_AI_MODEL", "claude")
        self.anthropic_client = None
        self.openai_client = None
        self.style_config: Optional[Dict[str, Any]] = None

        # 初始化API客户端
        if self.model == "claude":
            self._init_anthropic()
        elif self.model == "openai":
            self._init_openai()
        else:
            # 默认先尝试Claude，失败时回退到OpenAI
            try:
                self._init_anthropic()
            except Exception:
                self._init_openai()

    def _init_anthropic(self):
        """初始化Anthropic客户端"""
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY未设置")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude"
        except ImportError:
            raise ImportError("请安装anthropic库: pip install anthropic")

    def _init_openai(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY未设置")
            self.openai_client = OpenAI(api_key=api_key)
            self.model = "openai"
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")

    def _call_claude(self, prompt: str, max_tokens: int = 4000) -> str:
        """调用Claude API"""
        if not self.anthropic_client:
            self._init_anthropic()

        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _call_openai(self, prompt: str, max_tokens: int = 4000) -> str:
        """调用OpenAI API"""
        if not self.openai_client:
            self._init_openai()

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def _call_ai(self, prompt: str, max_tokens: int = 4000) -> str:
        """统一调用AI API"""
        try:
            if self.model == "claude":
                return self._call_claude(prompt, max_tokens)
            else:
                return self._call_openai(prompt, max_tokens)
        except Exception as e:
            # 失败时回退到另一个模型
            print(f"主模型调用失败({self.model}): {e}，尝试回退...")
            if self.model == "claude":
                self.model = "openai"
                return self._call_openai(prompt, max_tokens)
            else:
                self.model = "claude"
                return self._call_claude(prompt, max_tokens)

    def learn_style(self, reference_texts: str) -> Dict[str, Any]:
        """
        分析参考文本的写作风格

        Args:
            reference_texts: 3-5篇历史帖子，用\n---\n分隔
        """
        prompt = STYLE_LEARNING_PROMPT.format(reference_texts=reference_texts)
        response = self._call_ai(prompt, max_tokens=2000)

        try:
            # 尝试解析JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                self.style_config = json.loads(json_match.group())
            else:
                self.style_config = {"raw": response}
        except json.JSONDecodeError:
            self.style_config = {"raw": response}

        return self.style_config

    def generate_for_platform(
        self,
        platform: str,
        title: str,
        content: str,
        summary: str = "",
        code_snippets: list = None,
        key_points: str = "",
    ) -> Dict[str, Any]:
        """
        为指定平台生成内容

        Args:
            platform: 'x', 'zhihu', 'xiaohongshu'
            title: 原文标题
            content: 原文内容
            summary: 摘要
            code_snippets: 代码片段列表
            key_points: 关键观点

        Returns:
            包含生成内容的字典
        """
        prompt_template = get_prompt(platform)

        # 格式化代码片段
        code_str = ""
        if code_snippets:
            for i, code in enumerate(code_snippets[:5], 1):  # 最多5个
                code_preview = code[:500] + "..." if len(code) > 500 else code
                code_str += f"\n代码片段{i}:\n```\n{code_preview}\n```\n"

        # 格式化关键观点
        key_points_str = key_points if key_points else extract_key_points_from_content(content)

        # 构建Prompt
        prompt = prompt_template.format(
            title=title,
            content=content[:8000],  # 限制内容长度避免token超限
            summary=summary,
            key_points=key_points_str,
            code_snippets=code_str,
            metrics="",  # 可扩展：从内容中提取关键数据
        )

        # 如果有风格配置，追加风格指令
        if self.style_config:
            style_instruction = self._build_style_instruction()
            prompt += f"\n\n风格要求：\n{style_instruction}"

        # 调用AI
        response = self._call_ai(prompt, max_tokens=4000)

        # 解析结果
        return self._parse_response(platform, response)

    def _build_style_instruction(self) -> str:
        """根据风格配置生成风格指令"""
        if not self.style_config:
            return ""

        instructions = []
        if "tone" in self.style_config:
            instructions.append(f"语气: {self.style_config['tone']}")
        if "emoji_usage" in self.style_config:
            instructions.append(f"emoji使用: {self.style_config['emoji_usage']}")
        if "average_sentence_length" in self.style_config:
            instructions.append(f"句长: {self.style_config['average_sentence_length']}")
        if "favorite_phrases" in self.style_config and self.style_config["favorite_phrases"]:
            phrases = ", ".join(self.style_config["favorite_phrases"][:3])
            instructions.append(f"常用语: {phrases}")

        return "\n".join(instructions)

    def _parse_response(self, platform: str, response: str) -> Dict[str, Any]:
        """解析AI返回的内容"""
        # 尝试提取JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if platform == "xiaohongshu":
                    return {
                        "title": data.get("title", ""),
                        "content": data.get("content", ""),
                        "tags": data.get("tags", []),
                        "image_prompt": data.get("image_prompt", ""),
                        "raw": response,
                    }
                return data
            except json.JSONDecodeError:
                pass

        # 尝试提取JSON数组（X平台）
        array_match = re.search(r"\[.*\]", response, re.DOTALL)
        if array_match and platform == "x":
            try:
                tweets = json.loads(array_match.group())
                return {"tweets": tweets, "raw": response}
            except json.JSONDecodeError:
                pass

        # 无法解析JSON，返回原始文本
        if platform == "x":
            # 尝试按行分割为线程
            lines = [line.strip() for line in response.split("\n") if line.strip()]
            return {"tweets": lines, "raw": response}
        elif platform == "xiaohongshu":
            return {
                "title": "",
                "content": response,
                "tags": [],
                "image_prompt": "",
                "raw": response,
            }
        else:
            return {"content": response, "raw": response}


def extract_key_points_from_content(content: str, max_points: int = 5) -> str:
    """从内容中提取关键观点"""
    import re
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    key_points = []

    for para in paragraphs[:max_points]:
        sentences = re.split(r"[。！？.!?]", para)
        if sentences and sentences[0].strip():
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 10:
                key_points.append(first_sentence)

    return "\n".join([f"- {p}" for p in key_points[:max_points]])
