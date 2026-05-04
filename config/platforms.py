"""
三平台配置：字符限制、格式规则、特殊处理
"""

PLATFORMS = {
    "x": {
        "name": "X / Twitter",
        "char_limit": 280,
        "cn_char_limit": 140,
        "supports_thread": True,
        "max_thread_posts": 25,
        "format": "plain_text",
        "code_handling": "truncate_or_screenshot",
        "hashtags_max": 3,
        "features": ["thread", "hashtag", "mention"],
    },
    "zhihu": {
        "name": "知乎",
        "char_limit": 20000,
        "format": "markdown",
        "code_handling": "preserve_full",
        "features": ["markdown", "code_block", "formula", "image"],
        "sections": ["引言", "问题背景", "核心方案", "代码示例", "注意事项", "总结"],
    },
    "xiaohongshu": {
        "name": "小红书",
        "char_limit": 1000,
        "format": "structured",
        "code_handling": "simplify_or_screenshot",
        "features": ["emoji", "hashtag", "image_prompt"],
        "title_max_length": 20,
        "optimal_content_length": 600,
        "hashtags_range": (5, 8),
    },
}


def get_platform_config(platform: str) -> dict:
    """获取平台配置"""
    if platform not in PLATFORMS:
        raise ValueError(f"不支持的平台: {platform}。支持: {list(PLATFORMS.keys())}")
    return PLATFORMS[platform]


def detect_language(text: str) -> str:
    """简单检测文本主语言"""
    cn_chars = sum(1 for c in text if "一" <= c <= "鿿")
    total_chars = len(text.strip())
    if total_chars == 0:
        return "en"
    return "zh" if cn_chars / total_chars > 0.3 else "en"
