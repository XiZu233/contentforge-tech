#!/usr/bin/env python3
"""
ContentForge Tech - Streamlit Web应用
将技术博客内容转换为多平台社交帖子

运行方式：streamlit run app.py
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import extract_content
from core.generator import AIGenerator
from core.adapter import PlatformAdapter
from core.scorer import QualityScorer
from core.models import UnifiedLLMClient, PROVIDERS


# ============= 页面配置 =============
st.set_page_config(
    page_title="ContentForge Tech",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============= 自定义CSS =============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

    :root {
        --vellum: #faf9f5;
        --ink: #141413;
        --onyx: #1f1e1d;
        --graphite: #3d3d3a;
        --dusty: #73726c;
        --stone: #9c9a92;
        --parchment: #dedcd1;
        --snow: #ffffff;
        --terra: #d97757;
        --radius: 9.6px;
    }

    .block-container { max-width: 900px; padding-top: 2rem; }

    .main-title {
        font-family: 'Lora', Georgia, serif;
        font-size: 2rem;
        font-weight: 400;
        color: var(--ink);
        letter-spacing: -0.5px;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 0.95rem;
        color: var(--graphite);
        margin-bottom: 2rem;
    }
    .platform-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .badge-x { background: #1a1a2e; color: white; }
    .badge-zhihu { background: #0066ff; color: white; }
    .badge-xiaohongshu { background: #ff2442; color: white; }
    .score-excellent { color: #1a8c5e; font-weight: 600; }
    .score-pass { color: #c47a2a; font-weight: 600; }
    .score-fail { color: var(--terra); font-weight: 600; }
    .content-card {
        background: var(--snow);
        border: 1px solid var(--parchment);
        border-radius: var(--radius);
        padding: 24px;
        margin: 12px 0;
    }
    .tweet-box {
        background: var(--snow);
        border: 1px solid var(--parchment);
        border-radius: var(--radius);
        padding: 16px;
        margin: 8px 0;
    }
    .tweet-number {
        color: var(--terra);
        font-weight: 600;
        font-size: 0.85rem;
    }
    .copy-btn { float: right; }

    /* Alert banner */
    .alert-banner {
        padding: 18px 20px;
        border-radius: var(--radius);
        margin-bottom: 28px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
        background: rgba(217, 119, 87, 0.06);
        border: 1px solid rgba(217, 119, 87, 0.12);
    }
    .alert-banner .title { font-weight: 500; margin-bottom: 6px; color: var(--ink); font-size: 14px; }
    .alert-banner .desc { font-size: 13px; color: var(--graphite); margin-bottom: 12px; line-height: 1.5; }
    .code-block {
        background: var(--snow);
        border: 1px solid var(--parchment);
        border-radius: var(--radius);
        padding: 14px 16px;
        font-family: 'SF Mono', Monaco, monospace;
        font-size: 12.5px;
        line-height: 1.7;
    }
    .code-block .comment { color: var(--stone); }
    .code-block .key { color: var(--terra); }
    .code-block .val { color: #1a8c5e; }

    /* Score ring */
    .score-ring {
        width: 64px; height: 64px; border-radius: 50%;
        background: conic-gradient(var(--terra) var(--score-pct), var(--parchment) var(--score-pct));
        display: flex; align-items: center; justify-content: center; position: relative; flex-shrink: 0;
    }
    .score-ring::after {
        content: ''; width: 52px; height: 52px; background: var(--snow); border-radius: 50%; position: absolute;
    }
    .score-ring-value {
        position: relative; z-index: 1;
        font-family: 'Lora', Georgia, serif; font-size: 18px; font-weight: 600; color: var(--terra);
    }

    /* Section label */
    .section-label {
        font-size: 11px; font-weight: 600; color: var(--dusty);
        text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px;
    }

    /* Sidebar width fix */
    [data-testid="stSidebar"] { min-width: 320px !important; max-width: 340px !important; }
</style>
""", unsafe_allow_html=True)


# ============= 初始化Session State =============
def init_session_state():
    defaults = {
        "generated_results": {},
        "extracted_content": None,
        "style_config": None,
        "api_status": {"claude": False, "openai": False},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============= 检查API状态 =============
def check_api_status():
    client = UnifiedLLMClient()
    status = {}
    for key in PROVIDERS:
        status[key] = client.is_available(key)
    st.session_state.api_status = status
    return status


# ============= 侧边栏配置 =============
def render_sidebar():
    with st.sidebar:
        st.markdown("### 配置")

        # API状态
        api_status = check_api_status()
        st.markdown("**API 状态**")

        # 显示所有 provider 状态
        provider_names = {
            "kimi": "Kimi",
            "gemini": "Gemini",
            "openai": "OpenAI",
            "local": "本地",
        }
        for key, name in provider_names.items():
            if api_status.get(key):
                st.success(f"{name}")
            else:
                st.error(f"{name}")

        available_count = sum(api_status.values())
        if available_count == 0:
            st.warning("请在 .env 文件中设置至少一个 API 密钥")
        else:
            st.caption(f"已配置 {available_count} 个模型，将按优先级自动降级")

        st.divider()

        # 本地模型开关
        st.markdown("**本地模型**")
        enable_local = st.checkbox(
            "启用 Ollama 本地模型",
            value=api_status.get("local", False),
            help="需先运行 ollama serve（默认 localhost:11434）",
        )

        # 构建优先级链
        priority_chain = []
        for key in ["kimi", "gemini", "openai"]:
            if api_status.get(key):
                priority_chain.append(key)
        if enable_local and api_status.get("local"):
            priority_chain.append("local")

        if not priority_chain:
            priority_chain = ["openai"]  # 兜底

        st.divider()

        # 平台选择
        st.markdown("**目标平台**")
        platforms = {}
        platforms["x"] = st.checkbox("X / Twitter", value=True)
        platforms["zhihu"] = st.checkbox("知乎", value=True)
        platforms["xiaohongshu"] = st.checkbox("小红书", value=True)

        selected_platforms = [k for k, v in platforms.items() if v]

        st.divider()

        # 高级选项
        with st.expander("高级选项"):
            enable_score = st.checkbox("启用质量评分", value=True)
            show_raw = st.checkbox("显示原始响应", value=False)

            st.markdown("**风格参考**")
            style_text = st.text_area(
                "粘贴3-5篇你的历史帖子（用---分隔）",
                height=150,
                help="AI会学习你的写作风格",
            )

        return priority_chain, selected_platforms, enable_score, show_raw, style_text


# ============= 主页面 =============
def render_header():
    st.markdown('<div class="main-title">ContentForge Tech</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">技术博客  多平台社交内容一键生成</div>', unsafe_allow_html=True)


def render_input_section():
    st.markdown("### 内容输入")

    input_method = st.radio(
        "选择输入方式",
        options=["URL链接", "RSS Feed", "Markdown文本", "Markdown文件"],
        horizontal=True,
    )

    source = None
    source_type = None

    if input_method == "URL链接":
        source = st.text_input("博客文章URL", placeholder="https://example.com/blog-post")
        source_type = "url"
    elif input_method == "RSS Feed":
        source = st.text_input("RSS Feed地址", placeholder="https://example.com/feed.xml")
        source_type = "rss"
    elif input_method == "Markdown文本":
        source = st.text_area(
            "粘贴Markdown内容",
            height=200,
            placeholder="# 文章标题\n\n你的技术博客内容...",
        )
        source_type = "markdown"
    elif input_method == "Markdown文件":
        uploaded_file = st.file_uploader("上传Markdown文件", type=["md", "markdown"])
        if uploaded_file:
            source = uploaded_file.read().decode("utf-8")
            source_type = "markdown"

    return source, source_type


def render_results(results: dict, enable_score: bool):
    """渲染生成结果"""
    if not results:
        return

    st.markdown("---")
    st.markdown("### 生成结果")

    # 平台标签
    platform_names = {"x": "X / Twitter", "zhihu": "知乎", "xiaohongshu": "小红书"}
    platform_badges = {
        "x": "badge-x",
        "zhihu": "badge-zhihu",
        "xiaohongshu": "badge-xiaohongshu",
    }

    # 创建Tab
    tabs = st.tabs([platform_names.get(p, p) for p in results.keys()])

    for tab, (platform, content) in zip(tabs, results.items()):
        with tab:
            # 质量评分
            if enable_score and "quality_score" in content:
                score = content["quality_score"]
                total = score.get("total_score", 0)

                score_class = "score-excellent" if total >= 8.5 else "score-pass" if total >= 7.0 else "score-fail"

                score_pct = int(total * 10)
                cols = st.columns([1, 3])
                with cols[0]:
                    st.markdown(f'''
                    <div style="display:flex;align-items:center;gap:18px;margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid var(--parchment);">
                        <div style="width:64px;height:64px;border-radius:50%;background:conic-gradient(#d97757 {score_pct}%, #dedcd1 {score_pct}%);display:flex;align-items:center;justify-content:center;position:relative;flex-shrink:0;">
                            <div style="width:52px;height:52px;background:#fff;border-radius:50%;position:absolute;"></div>
                            <span style="position:relative;z-index:1;font-family:'Lora',Georgia,serif;font-size:18px;font-weight:600;color:#d97757;">{total}</span>
                        </div>
                        <div>
                            <div style="font-weight:500;margin-bottom:4px;font-size:15px;">质量评分</div>
                            <div style="font-size:13px;color:#73726c;line-height:1.5;">信息完整性 · 平台适配度 · 语言流畅度 · 技术准确性</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                with cols[1]:
                    inner_cols = st.columns(2)
                    with inner_cols[0]:
                        if score.get("suggestions"):
                            st.markdown("**改进建议**")
                            for s in score["suggestions"]:
                                st.markdown(f"- {s}")
                    with inner_cols[1]:
                        with st.expander("详细评分"):
                            for name, value in score.get("scores", {}).items():
                                st.markdown(f"- {name}: {value}")

                st.divider()

            # 平台特定渲染
            if platform == "x":
                render_x_content(content)
            elif platform == "zhihu":
                render_zhihu_content(content)
            elif platform == "xiaohongshu":
                render_xiaohongshu_content(content)


def render_x_content(content: dict):
    """渲染X/Twitter内容"""
    tweets = content.get("tweets", [])
    if not tweets:
        st.info("暂无生成内容")
        return

    st.markdown(f"**线程帖数**: {len(tweets)}")
    st.markdown(f"**总字符数**: {content.get('total_chars', sum(len(t) for t in tweets))}")

    full_text = "\n\n---\n\n".join([f"[{i+1}/{len(tweets)}] {t}" for i, t in enumerate(tweets)])

    for i, tweet in enumerate(tweets, 1):
        with st.container():
            cols = st.columns([0.1, 0.9])
            with cols[0]:
                st.markdown(f'<div class="tweet-number">{i}</div>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f'<div class="tweet-box">{tweet}</div>', unsafe_allow_html=True)
                st.caption(f"{len(tweet)} 字符")

    # 一键复制全部
    st.divider()
    cols = st.columns([1, 1])
    with cols[0]:
        st.code(full_text, language="text")
    with cols[1]:
        st.markdown("**一键复制**")
        for i, tweet in enumerate(tweets, 1):
            st_copy_button(tweet, f"copy_x_{i}", f"复制 [{i}]")


def render_zhihu_content(content: dict):
    """渲染知乎内容"""
    text = content.get("content", "")
    if not text:
        st.info("暂无生成内容")
        return

    st.markdown(f"**字符数**: {content.get('char_count', len(text))}")
    st.markdown(f"**含代码块**: {'是' if content.get('has_code_blocks') else '否'}")

    st.divider()

    # 预览模式
    st.markdown("**预览**")
    st.markdown(text)

    st.divider()

    # Markdown源码
    with st.expander("查看Markdown源码"):
        st.code(text, language="markdown")
        st_copy_button(text, "copy_zhihu", "复制全部")


def render_xiaohongshu_content(content: dict):
    """渲染小红书内容"""
    title = content.get("title", "")
    text = content.get("content", "")
    tags = content.get("tags", [])
    image_prompt = content.get("image_prompt", "")

    if not title and not text:
        st.info("暂无生成内容")
        return

    # 标题
    st.markdown(f"### {title}")

    # 标签
    if tags:
        st.markdown(" ".join([f'`{tag}`' for tag in tags]))

    st.divider()

    # 正文
    st.markdown("**正文**")
    st.markdown(f'<div style="background: #faf9f5; padding: 16px; border-radius: 9.6px; border: 1px solid #dedcd1;">{text}</div>', unsafe_allow_html=True)

    st.caption(f"{content.get('char_count', len(text))} 字符")

    # 配图提示词
    if image_prompt:
        st.divider()
        st.markdown("**配图提示词**")
        st.info(image_prompt)
        st_copy_button(image_prompt, "copy_xhs_image", "复制提示词")

    st.divider()

    # 一键复制全部
    full_content = f"{title}\n\n{text}\n\n{' '.join(tags)}"
    st_copy_button(full_content, "copy_xhs", "复制全部内容")


def st_copy_button(text: str, key: str, label: str = "复制"):
    """Streamlit复制按钮"""
    # 使用HTML实现复制功能
    import html
    escaped_text = html.escape(text).replace("\n", "\\n")
    button_html = f"""
    <button
        onclick="navigator.clipboard.writeText('{escaped_text}'); this.innerText='已复制'; setTimeout(() => this.innerText='{label}', 2000);"
        style="
            background: #141413;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 9.6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 400;
            font-family: 'Inter', -apple-system, sans-serif;
            transition: all 0.2s ease;
        "
        onmouseover="this.style.background='#1f1e1d'"
        onmouseout="this.style.background='#141413'"
    >
        {label}
    </button>
    """
    st.markdown(button_html, unsafe_allow_html=True)


# ============= 主流程 =============
def main():
    render_header()

    # 侧边栏配置
    priority_chain, selected_platforms, enable_score, show_raw, style_text = render_sidebar()

    # 检查是否有可用API
    api_status = check_api_status()
    if not any(api_status.values()):
        st.markdown("""
        <div class="alert-banner">
            <div class="content">
                <div class="title">未检测到任何 API 密钥</div>
                <div class="desc">请在项目根目录创建 .env 文件并填入密钥</div>
                <div class="code-block">
                    <span class="comment"># .env 文件示例</span><br>
                    <span class="key">MODEL_PRIORITY</span>=<span class="val">kimi,gemini,openai</span><br>
                    <span class="key">KIMI_API_KEY</span>=<span class="val">your_key_here</span><br>
                    <span class="key">GEMINI_API_KEY</span>=<span class="val">your_key_here</span><br>
                    <span class="key">OPENAI_API_KEY</span>=<span class="val">your_key_here</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # 输入区
    source, source_type = render_input_section()

    # 生成按钮
    st.markdown("---")
    generate_clicked = st.button(
        "生成多平台内容",
        type="primary",
        use_container_width=True,
        disabled=not source or not selected_platforms,
    )

    if generate_clicked and source and selected_platforms:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # 步骤1：提取内容
            status_text.text("正在提取内容...")
            progress_bar.progress(0.2)

            extracted = extract_content(source, source_type)
            st.session_state.extracted_content = extracted

            # 显示提取信息
            cols = st.columns(4)
            with cols[0]:
                st.metric("标题", extracted.title[:30] + "..." if len(extracted.title) > 30 else extracted.title)
            with cols[1]:
                st.metric("内容长度", f"{len(extracted.content)} 字符")
            with cols[2]:
                st.metric("代码片段", len(extracted.code_snippets))
            with cols[3]:
                st.metric("关键观点", len([p for p in extracted.key_points.split("\n") if p.strip()]))

            # 步骤2：初始化生成器
            status_text.text("正在初始化AI引擎...")
            progress_bar.progress(0.3)

            generator = AIGenerator(providers=priority_chain)

            # 学习风格
            if style_text.strip():
                status_text.text("正在学习你的写作风格...")
                generator.learn_style(style_text)

            # 步骤3：为每个平台生成
            results = {}
            scorer = QualityScorer(ai_generator=generator) if enable_score else None

            for i, platform in enumerate(selected_platforms):
                progress = 0.3 + (0.6 * (i / len(selected_platforms)))
                status_text.text(f"正在生成 {platform.upper()} 平台内容... ({i+1}/{len(selected_platforms)})")
                progress_bar.progress(progress)

                # 生成
                generated = generator.generate_for_platform(
                    platform=platform,
                    title=extracted.title,
                    content=extracted.content,
                    summary=extracted.summary,
                    code_snippets=extracted.code_snippets,
                    key_points=extracted.key_points,
                )

                # 适配
                adapter = PlatformAdapter(platform)
                adapted = adapter.adapt(generated)

                # 评分
                if scorer:
                    score_result = scorer.score(
                        platform=platform,
                        generated_content=adapted,
                        original_key_points=extracted.key_points,
                        use_ai=True,
                    )
                    adapted["quality_score"] = score_result

                results[platform] = adapted

                # 显示原始响应（调试用）
                if show_raw:
                    with st.expander(f"[{platform}] 原始AI响应"):
                        st.code(generated.get("raw", "无原始数据"), language="text")

            # 保存结果
            st.session_state.generated_results = results

            progress_bar.progress(1.0)
            status_text.text("生成完成！")
            st.success(f"已为 {len(results)} 个平台生成内容")

        except Exception as e:
            st.error(f"生成失败: {e}")
            import traceback
            st.code(traceback.format_exc())

    # 显示结果
    if st.session_state.generated_results:
        render_results(st.session_state.generated_results, enable_score)

    # 页脚
    st.markdown("---")
    st.caption("ContentForge Tech  技术博客多平台内容生成器  Built with Streamlit + Claude API")


if __name__ == "__main__":
    main()
