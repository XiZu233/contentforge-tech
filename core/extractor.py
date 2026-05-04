"""
内容提取模块：支持RSS/URL/Markdown三种输入方式
自动识别代码块，保留技术博客的核心资产
"""

import re
import requests
import feedparser
import frontmatter
from typing import Optional
from urllib.parse import urlparse


try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class ExtractedContent:
    """提取后的内容数据结构"""

    def __init__(
        self,
        title: str = "",
        content: str = "",
        summary: str = "",
        code_snippets: list = None,
        key_points: str = "",
        source_url: str = "",
        published_date: str = "",
        author: str = "",
        tags: list = None,
    ):
        self.title = title
        self.content = content
        self.summary = summary
        self.code_snippets = code_snippets or []
        self.key_points = key_points
        self.source_url = source_url
        self.published_date = published_date
        self.author = author
        self.tags = tags or []

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "summary": self.summary,
            "code_snippets_count": len(self.code_snippets),
            "key_points": self.key_points,
            "source_url": self.source_url,
            "published_date": self.published_date,
            "author": self.author,
            "tags": self.tags,
        }


def extract_code_blocks(text: str) -> list:
    """从文本中提取代码块"""
    # Markdown代码块: ```language\ncode\n```
    pattern = r"```[\w]*\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)

    # 行内代码: `code`
    inline_pattern = r"`([^`]+)`"
    inline_matches = re.findall(inline_pattern, text)

    # 过滤掉太短的行内代码（小于5字符的通常不是有意义的代码）
    inline_matches = [m for m in inline_matches if len(m) >= 5]

    return matches + inline_matches[:10]  # 最多返回10个代码片段


def extract_key_points(text: str, max_points: int = 5) -> str:
    """从文本中提取关键观点（简单实现：提取每个段落的第一句）"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    key_points = []

    for para in paragraphs[:max_points]:
        # 取段落的第一句话
        sentences = re.split(r"[。！？.!?]", para)
        if sentences and sentences[0].strip():
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 10:  # 过滤太短的句子
                key_points.append(first_sentence)

    return "\n".join([f"- {p}" for p in key_points[:max_points]])


def extract_from_rss(rss_url: str) -> list:
    """从RSS Feed提取内容"""
    feed = feedparser.parse(rss_url)
    results = []

    for entry in feed.entries[:1]:  # 默认取最新一条
        title = entry.get("title", "")
        link = entry.get("link", "")
        summary = entry.get("summary", entry.get("description", ""))
        content = entry.get("content", [{}])[0].get("value", summary)
        published = entry.get("published", "")
        author = entry.get("author", "")
        tags = [tag.term for tag in entry.get("tags", [])]

        # 清理HTML标签
        if BS4_AVAILABLE:
            soup = BeautifulSoup(content, "html.parser")
            clean_content = soup.get_text(separator="\n", strip=True)
            clean_summary = BeautifulSoup(summary, "html.parser").get_text(strip=True)
        else:
            clean_content = re.sub(r"<[^>]+>", "", content)
            clean_summary = re.sub(r"<[^>]+>", "", summary)

        code_snippets = extract_code_blocks(clean_content)
        key_points = extract_key_points(clean_content)

        results.append(ExtractedContent(
            title=title,
            content=clean_content,
            summary=clean_summary,
            code_snippets=code_snippets,
            key_points=key_points,
            source_url=link,
            published_date=published,
            author=author,
            tags=tags,
        ))

    return results


def extract_from_url(url: str) -> ExtractedContent:
    """从URL提取内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        title = ""
        if BS4_AVAILABLE:
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

        # 使用readability提取正文
        if READABILITY_AVAILABLE:
            doc = Document(html)
            content_html = doc.summary()
            if BS4_AVAILABLE:
                content_soup = BeautifulSoup(content_html, "html.parser")
                content = content_soup.get_text(separator="\n", strip=True)
            else:
                content = re.sub(r"<[^>]+>", "", content_html)
        else:
            # Fallback: 使用BeautifulSoup提取所有段落
            if BS4_AVAILABLE:
                soup = BeautifulSoup(html, "html.parser")
                paragraphs = soup.find_all("p")
                content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
            else:
                content = ""

        code_snippets = extract_code_blocks(content)
        key_points = extract_key_points(content)

        return ExtractedContent(
            title=title,
            content=content,
            summary=content[:300] + "..." if len(content) > 300 else content,
            code_snippets=code_snippets,
            key_points=key_points,
            source_url=url,
        )

    except requests.RequestException as e:
        raise ValueError(f"无法获取URL内容: {e}")


def extract_from_markdown(md_text: str) -> ExtractedContent:
    """从Markdown文本提取内容"""
    try:
        post = frontmatter.loads(md_text)
        metadata = post.metadata
        content = post.content
    except Exception:
        metadata = {}
        content = md_text

    title = metadata.get("title", "")
    author = metadata.get("author", "")
    tags = metadata.get("tags", [])
    published_date = metadata.get("date", "")

    # 清理Markdown语法（简化版）
    clean_content = content
    # 移除图片链接
    clean_content = re.sub(r"!\[.*?\]\(.*?\)", "", clean_content)
    # 移除普通链接，保留文本
    clean_content = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean_content)
    # 移除标题标记
    clean_content = re.sub(r"^#{1,6}\s*", "", clean_content, flags=re.MULTILINE)
    # 移除粗体/斜体标记
    clean_content = re.sub(r"\*{1,2}(.*?)\*{1,2}", r"\1", clean_content)

    code_snippets = extract_code_blocks(content)
    key_points = extract_key_points(clean_content)

    # 生成摘要（前200字符）
    summary = clean_content[:200].strip()
    if len(clean_content) > 200:
        summary += "..."

    return ExtractedContent(
        title=title,
        content=clean_content,
        summary=summary,
        code_snippets=code_snippets,
        key_points=key_points,
        author=author,
        tags=tags,
        published_date=str(published_date),
    )


def extract_content(source: str, source_type: Optional[str] = None) -> ExtractedContent:
    """
    统一入口：自动识别输入类型并提取内容

    Args:
        source: RSS URL / 博客URL / Markdown文本
        source_type: 可选，强制指定类型 ('rss', 'url', 'markdown')

    Returns:
        ExtractedContent 对象
    """
    if source_type is None:
        # 自动识别类型
        if source.startswith("http://") or source.startswith("https://"):
            if "/feed" in source or source.endswith(".xml") or "rss" in source.lower():
                results = extract_from_rss(source)
                return results[0] if results else ExtractedContent()
            else:
                return extract_from_url(source)
        elif source.strip().startswith("---") or "# " in source[:1000]:
            return extract_from_markdown(source)
        else:
            # 默认当作Markdown处理
            return extract_from_markdown(source)
    else:
        if source_type == "rss":
            results = extract_from_rss(source)
            return results[0] if results else ExtractedContent()
        elif source_type == "url":
            return extract_from_url(source)
        elif source_type == "markdown":
            return extract_from_markdown(source)
        else:
            raise ValueError(f"不支持的source_type: {source_type}")
