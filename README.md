# 🔥 ContentForge Tech

技术博客 → 多平台社交内容一键生成器

基于 [Marketing Engineer 岗位调研报告](https://github.com/yourname/marketing-engineer-guide) 中的 **ContentForge** 项目二次开发，专为技术博主设计。

## ✨ 核心功能

| 功能 | 说明 |
|:---|:---|
| **多源输入** | 支持 URL、RSS Feed、Markdown 文本/文件三种输入方式 |
| **三平台输出** | 一键生成适配 X(Twitter)、知乎、小红书的社交内容 |
| **AI重写** | 使用 Claude/GPT 完全重写内容，非简单摘要 |
| **风格定制** | 上传历史帖子，AI学习你的写作风格 |
| **质量评分** | 9维度质量评分系统（移植自 Content Repurposer） |
| **代码保留** | 智能识别技术博客中的代码块，在转换中保留核心代码 |
| **一键复制** | 生成结果一键复制，直接粘贴到目标平台 |

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourname/contentforge-tech.git
cd contentforge-tech
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 4. 启动应用（选择一种方式）

**方式A：本地Python（开发）**

```bash
streamlit run app.py
```

**方式B：Docker Compose（推荐部署）**

```bash
docker-compose up -d
```

**方式C：一键部署脚本**

```bash
# Linux/macOS
./scripts/deploy.sh setup

# Windows PowerShell
.\scripts\deploy.ps1 setup
```

详细部署指南请参考 [DEPLOY.md](DEPLOY.md)。

访问 `http://localhost:8501` 即可使用。

## 📖 使用方式

### Web界面（推荐）

1. 在侧边栏选择目标平台（X / 知乎 / 小红书）
2. 选择输入方式（URL / RSS / Markdown）
3. 粘贴内容或上传文件
4. 点击「生成多平台内容」
5. 在Tab中查看各平台生成结果，一键复制

### CLI命令行

```bash
# 从URL生成
python main.py --url https://example.com/blog-post --platforms x zhihu

# 从RSS生成
python main.py --rss https://example.com/feed.xml --platforms x zhihu xiaohongshu

# 从Markdown文件生成
python main.py --file post.md --platforms xiaohongshu --score

# 带风格参考
python main.py --url https://example.com/post --style-file my_posts.txt
```

## 🏗️ 技术架构

```
输入层          处理层              输出层
─────────────────────────────────────────────
URL         →   内容提取      →   X线程帖
RSS Feed    →   AI生成引擎    →   知乎文章
Markdown    →   平台适配器    →   小红书笔记
            →   质量评分器
```

### 核心模块

| 模块 | 文件 | 职责 |
|:---|:---|:---|
| 内容提取 | `core/extractor.py` | RSS/URL/Markdown解析，代码块识别 |
| AI生成 | `core/generator.py` | Claude/OpenAI API调用，风格学习 |
| 平台适配 | `core/adapter.py` | 字符限制、格式调整、emoji注入 |
| 质量评分 | `core/scorer.py` | 9维度评分，自动重试 |

### 参考开源项目

本项目在以下开源项目基础上融合二次开发：

- [OpenContentGenerator](https://github.com/habeebmoosa/OpenContentGenerator) — UI设计理念
- [Content Repurposer](https://github.com/p4r4d0xb0x/content-repurposer) — 9点质量评分系统
- [LinkedInConnect](https://github.com/MartinPaulEve/LinkedInConnect) — Feed解析链
- [n8n Content Repurposer](https://github.com/ivansiyanko/n8n-content-repurposer) — 工作流设计

## 🎯 平台适配策略

### X / Twitter
- 自动生成5-8条推文线程
- 首帖设计hook吸引点击
- 代码片段单独成帖
- 自动添加技术hashtag

### 知乎
- Markdown格式保留代码块
- 结构：引言→背景→方案→代码→总结
- 关键概念自动加粗
- 结尾互动引导

### 小红书
- catchy标题 + emoji
- 口语化技术表达
- 自动生成5-8个标签
- 配图提示词生成

## 📊 质量评分维度

| 维度 | 权重 | 说明 |
|:---|:---|:---|
| 信息完整性 | 15% | 是否遗漏核心技术点 |
| 平台适配度 | 15% | 是否符合平台内容习惯 |
| 语言流畅度 | 15% | 是否自然，无AI痕迹 |
| 技术准确性 | 15% | 代码、术语是否正确 |
| 吸引力 | 10% | 首句/标题是否有hook |
| 可读性 | 10% | 段落、格式是否友好 |
| 风格一致性 | 10% | 是否符合用户风格 |
| CTA完整性 | 5% | 是否有行动引导 |
| 原创性 | 5% | 是否避免过度重复 |

## 💰 成本估算

| 项目 | 费用 |
|:---|:---|
| Claude API | ~$0.02-0.05 / 篇 |
| OpenAI API (备用) | ~$0.01-0.03 / 篇 |
| Streamlit Cloud部署 | 免费 |
| **月度总成本** | **~$1-5**（按每周2-3篇计算） |

## 🛠️ 开发计划

- [x] Phase 1：核心引擎（提取/生成/适配/评分）
- [x] Phase 2：Streamlit Web界面
- [ ] Phase 3：GitHub Action自动触发
- [ ] Phase 4：多语言支持（英文博客→中文平台）
- [ ] Phase 5：批量处理（RSS历史文章批量转换）

## 🤝 贡献

欢迎提交 Issue 和 PR！

特别欢迎以下方向的贡献：
- 新的社交平台适配器（微信公众号、掘金、CSDN等）
- 更智能的风格学习算法
- 批量处理功能
- 更多语言的Prompt模板

## 📄 License

MIT License

## 🙏 致谢

本项目源于 [Marketing Engineer 岗位调研与新人求职完全指南](https://github.com/yourname/marketing-engineer-guide) 中的 ContentForge 项目建议，是报告第4章「项目作品集设计指南」的实战落地。
