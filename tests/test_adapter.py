"""
平台适配器单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.adapter import PlatformAdapter


def test_x_adapter():
    """测试X平台适配"""
    adapter = PlatformAdapter("x")

    # 测试线程适配
    content = {
        "tweets": [
            "这是一条很长的推文，需要测试字符限制功能是否正常工作" + "x" * 300,
            "第二条推文",
        ]
    }
    result = adapter.adapt(content)
    tweets = result["tweets"]

    # 检查字符限制
    for tweet in tweets:
        assert len(tweet) <= 280, f"推文超长: {len(tweet)}字符"

    print("[PASS] X platform adapter test")


def test_zhihu_adapter():
    """Test Zhihu adapter"""
    adapter = PlatformAdapter("zhihu")

    content = {
        "content": "Body text\n\n```python\ndef test():\n    pass\n"
    }
    result = adapter.adapt(content)

    assert "content" in result
    print("[PASS] Zhihu adapter test")


def test_xiaohongshu_adapter():
    """Test Xiaohongshu adapter"""
    adapter = PlatformAdapter("xiaohongshu")

    content = {
        "title": "This is a very long title that needs to be truncated",
        "content": "Body content\n\nSecond paragraph",
        "tags": ["Python", "Automation"],
        "image_prompt": "A technical illustration",
    }
    result = adapter.adapt(content)

    # Check title length
    assert len(result["title"]) <= 20, f"Title too long: {len(result['title'])} chars"

    # Check emoji
    assert any(ord(c) > 0x1F300 for c in result["title"]), "Title should contain emoji"

    # Check tag count
    assert 5 <= result["tag_count"] <= 8, f"Tag count out of range: {result['tag_count']}"

    print("[PASS] Xiaohongshu adapter test")


if __name__ == "__main__":
    test_x_adapter()
    test_zhihu_adapter()
    test_xiaohongshu_adapter()
    print("\nAll adapter tests passed!")
