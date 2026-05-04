"""
内容提取模块单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.extractor import (
    extract_code_blocks,
    extract_key_points,
    extract_from_markdown,
    extract_content,
    ExtractedContent,
)


def test_extract_code_blocks():
    """测试代码块提取"""
    text = """
这是一个Python示例：
```python
def hello():
    print("Hello, World!")
```

还有一个JavaScript示例：
```js
const x = 1;
```

行内代码：`pip install requests`
"""
    blocks = extract_code_blocks(text)
    assert len(blocks) >= 2, f"应至少提取2个代码块，实际提取{len(blocks)}个"
    print("[PASS] Code block extraction test")


def test_extract_key_points():
    """Test key point extraction"""
    text = """
First paragraph: Python is one of the most popular programming languages today.

Second paragraph: Automated workflows can significantly improve development efficiency.

Third paragraph: n8n is an open-source automation tool.
"""
    points = extract_key_points(text, max_points=3)
    assert "Python" in points or "automated" in points or "n8n" in points
    print("[PASS] Key point extraction test")


def test_extract_from_markdown():
    """Test Markdown parsing"""
    md = """---
title: Test Article
author: Test Author
tags: [python, automation]
---

# This is the title

This is body content with some technical details.

```python
def test():
    pass
```
"""
    result = extract_from_markdown(md)
    assert result.title == "Test Article"
    assert result.author == "Test Author"
    assert len(result.code_snippets) >= 1
    print("[PASS] Markdown parsing test")


def test_extracted_content_to_dict():
    """Test content object serialization"""
    content = ExtractedContent(
        title="Test",
        content="Test content",
        code_snippets=["code1", "code2"],
    )
    d = content.to_dict()
    assert d["title"] == "Test"
    assert d["code_snippets_count"] == 2
    print("[PASS] Content object serialization test")


if __name__ == "__main__":
    test_extract_code_blocks()
    test_extract_key_points()
    test_extract_from_markdown()
    test_extracted_content_to_dict()
    print("\nAll tests passed!")
