"""
平台格式适配器：确保生成内容符合各平台规范
"""

from config.platforms import get_platform_config, detect_language


class PlatformAdapter:
    """平台内容适配器"""

    def __init__(self, platform: str):
        self.platform = platform
        self.config = get_platform_config(platform)

    def adapt(self, content: dict) -> dict:
        """
        适配内容到目标平台规范

        Args:
            content: 生成器输出的内容字典

        Returns:
            适配后的内容字典
        """
        if self.platform == "x":
            return self._adapt_x(content)
        elif self.platform == "zhihu":
            return self._adapt_zhihu(content)
        elif self.platform == "xiaohongshu":
            return self._adapt_xiaohongshu(content)
        else:
            return content

    def _adapt_x(self, content: dict) -> dict:
        """适配X/Twitter内容"""
        tweets = content.get("tweets", [])
        if not tweets:
            tweets = [content.get("content", "")]

        adapted_tweets = []
        char_limit = self.config["char_limit"]
        cn_char_limit = self.config["cn_char_limit"]

        for tweet in tweets:
            # 检测语言并应用对应字符限制
            lang = detect_language(tweet)
            limit = cn_char_limit if lang == "zh" else char_limit

            # 截断超长推文
            if len(tweet) > limit:
                tweet = tweet[:limit - 3] + "..."

            adapted_tweets.append(tweet)

        return {
            "tweets": adapted_tweets,
            "thread_count": len(adapted_tweets),
            "total_chars": sum(len(t) for t in adapted_tweets),
        }

    def _adapt_zhihu(self, content: dict) -> dict:
        """适配知乎内容"""
        text = content.get("content", "")

        # 确保Markdown代码块格式正确
        # 检查是否有未闭合的代码块
        code_block_count = text.count("```")
        if code_block_count % 2 != 0:
            text += "\n```"

        # 确保标题使用Markdown格式
        lines = text.split("\n")
        formatted_lines = []
        for line in lines:
            stripped = line.strip()
            # 检测类似标题的行并加粗
            if stripped and not stripped.startswith("#") and not stripped.startswith("*"):
                if len(stripped) < 50 and (stripped.endswith(":") or stripped.endswith("：")):
                    line = f"**{stripped}**"
            formatted_lines.append(line)

        text = "\n".join(formatted_lines)

        # 限制长度
        max_chars = self.config.get("char_limit", 20000)
        if len(text) > max_chars:
            text = text[:max_chars - 100] + "\n\n...（内容过长，已截断）"

        return {
            "content": text,
            "char_count": len(text),
            "has_code_blocks": "```" in text,
        }

    def _adapt_xiaohongshu(self, content: dict) -> dict:
        """适配小红书内容"""
        title = content.get("title", "")
        text = content.get("content", "")
        tags = content.get("tags", [])
        image_prompt = content.get("image_prompt", "")

        char_limit = self.config["char_limit"]
        title_max = self.config["title_max_length"]

        # 标题处理：预留emoji空间
        needs_emoji = not any(ord(c) > 0x1F300 for c in title)
        effective_max = title_max - 1 if needs_emoji else title_max
        if len(title) > effective_max:
            title = title[:effective_max]

        # 确保标题有emoji
        if needs_emoji:
            title = "💡" + title

        # 正文处理
        # 确保段落间有空行
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        formatted_paragraphs = []

        for para in paragraphs:
            # 确保段落有emoji
            if not any(ord(c) > 0x1F300 for c in para):
                # 根据内容类型添加emoji
                if "代码" in para or "python" in para.lower():
                    para = "💻 " + para
                elif "错误" in para or "bug" in para.lower():
                    para = "🐛 " + para
                elif "效率" in para or "优化" in para:
                    para = "🚀 " + para
                elif "注意" in para or "警告" in para:
                    para = "⚠️ " + para
                else:
                    para = "✨ " + para
            formatted_paragraphs.append(para)

        text = "\n\n".join(formatted_paragraphs)

        # 限制长度
        if len(text) > char_limit:
            text = text[:char_limit - 50] + "\n\n..."

        # 标签处理
        hashtags_range = self.config.get("hashtags_range", (5, 8))
        min_tags, max_tags = hashtags_range

        if len(tags) < min_tags:
            # 补充默认标签
            default_tags = ["程序员", "技术分享", "代码", "开发", "编程", "干货", "学习", "教程"]
            tags.extend(default_tags[:(min_tags - len(tags))])

        tags = tags[:max_tags]

        # 确保标签格式正确
        formatted_tags = []
        for tag in tags:
            tag = tag.strip().replace(" ", "").replace("#", "")
            if tag:
                formatted_tags.append(f"#{tag}")

        return {
            "title": title,
            "content": text,
            "tags": formatted_tags,
            "image_prompt": image_prompt,
            "char_count": len(text),
            "tag_count": len(formatted_tags),
        }
