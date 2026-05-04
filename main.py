#!/usr/bin/env python3
"""
ContentForge Tech - CLI入口
将技术博客内容转换为多平台社交帖子

用法：
    python main.py --url <博客链接> --platforms x zhihu xiaohongshu
    python main.py --rss <RSS地址> --platforms x zhihu
    python main.py --markdown <文件路径> --platforms xiaohongshu
"""

import argparse
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import extract_content
from core.generator import AIGenerator
from core.adapter import PlatformAdapter
from core.scorer import QualityScorer


def main():
    parser = argparse.ArgumentParser(
        description="ContentForge Tech - 技术博客多平台内容生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --url https://example.com/blog-post --platforms x zhihu
  python main.py --rss https://example.com/feed.xml --platforms x zhihu xiaohongshu
  python main.py --file post.md --platforms xiaohongshu
        """
    )

    # 输入源参数（互斥）
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--url", help="博客文章URL")
    source_group.add_argument("--rss", help="RSS Feed地址")
    source_group.add_argument("--file", help="Markdown文件路径")
    source_group.add_argument("--text", help="直接输入Markdown文本")

    # 平台选择
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["x", "zhihu", "xiaohongshu"],
        default=["x", "zhihu", "xiaohongshu"],
        help="目标平台（默认：x zhihu xiaohongshu）",
    )

    # AI模型选择
    parser.add_argument(
        "--model",
        choices=["claude", "openai"],
        default="claude",
        help="AI模型（默认：claude）",
    )

    # 风格参考
    parser.add_argument(
        "--style-file",
        help="风格参考文件路径（包含3-5篇历史帖子的文本）",
    )

    # 评分选项
    parser.add_argument(
        "--score",
        action="store_true",
        help="启用质量评分",
    )

    # 输出选项
    parser.add_argument(
        "--output",
        "-o",
        help="输出文件路径（JSON格式）",
    )

    # 调试模式
    parser.add_argument(
        "--debug",
        action="store_true",
        help="显示调试信息",
    )

    args = parser.parse_args()

    # 检查API密钥
    if args.model == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
        print("错误：未设置 ANTHROPIC_API_KEY 环境变量")
        print("请复制 .env.example 为 .env 并填入你的API密钥")
        sys.exit(1)
    elif args.model == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("错误：未设置 OPENAI_API_KEY 环境变量")
        sys.exit(1)

    # 提取内容
    print("=" * 60)
    print("ContentForge Tech - 技术博客多平台内容生成器")
    print("=" * 60)
    print()

    try:
        if args.url:
            print(f"正在从URL提取内容: {args.url}")
            content = extract_content(args.url, "url")
        elif args.rss:
            print(f"正在从RSS提取内容: {args.rss}")
            content = extract_content(args.rss, "rss")
        elif args.file:
            print(f"正在从文件读取: {args.file}")
            with open(args.file, "r", encoding="utf-8") as f:
                md_text = f.read()
            content = extract_content(md_text, "markdown")
        elif args.text:
            print("正在处理输入文本...")
            content = extract_content(args.text, "markdown")

        print(f"标题: {content.title}")
        print(f"内容长度: {len(content.content)} 字符")
        print(f"代码片段: {len(content.code_snippets)} 个")
        print()

    except Exception as e:
        print(f"内容提取失败: {e}")
        sys.exit(1)

    # 初始化AI生成器
    print(f"初始化AI生成器（模型: {args.model}）...")
    try:
        generator = AIGenerator(model=args.model)
    except Exception as e:
        print(f"AI生成器初始化失败: {e}")
        sys.exit(1)

    # 加载风格参考
    if args.style_file:
        print(f"正在学习风格: {args.style_file}")
        try:
            with open(args.style_file, "r", encoding="utf-8") as f:
                reference_text = f.read()
            style = generator.learn_style(reference_text)
            if args.debug:
                print(f"风格配置: {json.dumps(style, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"风格学习失败: {e}")

    # 初始化评分器
    scorer = QualityScorer(ai_generator=generator) if args.score else None

    # 为每个平台生成内容
    results = {}

    for platform in args.platforms:
        print(f"\n{'=' * 60}")
        print(f"正在生成 {platform.upper()} 平台内容...")
        print("=" * 60)

        try:
            # 生成内容
            generated = generator.generate_for_platform(
                platform=platform,
                title=content.title,
                content=content.content,
                summary=content.summary,
                code_snippets=content.code_snippets,
                key_points=content.key_points,
            )

            # 平台适配
            adapter = PlatformAdapter(platform)
            adapted = adapter.adapt(generated)

            # 质量评分
            if scorer:
                print("正在进行质量评分...")
                score_result = scorer.score(
                    platform=platform,
                    generated_content=adapted,
                    original_key_points=content.key_points,
                    use_ai=True,
                )
                adapted["quality_score"] = score_result

                print(f"质量评分: {score_result['total_score']}/10")
                if score_result["suggestions"]:
                    print(f"改进建议: {'; '.join(score_result['suggestions'])}")

            results[platform] = adapted

            # 打印结果
            print(f"\n--- {platform.upper()} 生成结果 ---")
            if platform == "x":
                tweets = adapted.get("tweets", [])
                for i, tweet in enumerate(tweets, 1):
                    print(f"\n[{i}/{len(tweets)}] ({len(tweet)}字符)")
                    print(tweet)
                    print("-" * 40)
            elif platform == "xiaohongshu":
                print(f"\n标题: {adapted.get('title', '')}")
                print(f"\n正文:\n{adapted.get('content', '')}")
                print(f"\n标签: {' '.join(adapted.get('tags', []))}")
                print(f"\n配图提示词: {adapted.get('image_prompt', '')}")
            else:
                print(adapted.get("content", ""))

        except Exception as e:
            print(f"生成失败: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            continue

    # 保存结果
    if args.output:
        print(f"\n正在保存结果到: {args.output}")
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("保存完成")

    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
