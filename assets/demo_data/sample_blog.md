---
title: "用Python和n8n搭建自动化工作流：从手动到自动的实战指南"
date: 2025-01-15
author: "技术博主"
tags: ["Python", "n8n", "自动化", "工作流", "效率工具"]
---

# 用Python和n8n搭建自动化工作流：从手动到自动的实战指南

## 引言

作为一名开发者，我每天都要处理大量重复性任务：数据同步、报告生成、邮件发送……这些任务占用了我至少2小时/天的工作时间。直到我发现了n8n这个开源自动化工具，配合Python脚本，我终于把这些繁琐的工作交给了机器。

## 什么是n8n？

n8n是一个开源的工作流自动化工具，类似于Zapier和Make，但它是自托管的，数据完全由你自己掌控。它支持200+种集成，从GitHub、Slack到Google Sheets，几乎覆盖了开发者日常使用的所有工具。

**核心优势：**
- 完全开源，可自托管
- 可视化工作流编排
- 支持自定义JavaScript/Python代码节点
- 比Zapier便宜90%（自托管成本约$5/月）

## 实战案例：自动化周报生成

### 问题背景

我们团队每周一都要花1小时整理上周的GitHub提交、Jira任务和Slack讨论，然后写成周报发给全员。这个过程极其枯燥且容易遗漏。

### 解决方案

我用n8n搭建了一个全自动周报生成流水线：

```python
# 数据聚合脚本（n8n Function节点）
import json
from datetime import datetime, timedelta

def aggregate_weekly_data():
    """聚合上周的所有数据源"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # 获取GitHub提交统计
    github_commits = get_github_commits(start_date, end_date)

    # 获取Jira任务完成情况
    jira_tasks = get_jira_completed_tasks(start_date, end_date)

    # 聚合数据
    report = {
        "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
        "github_summary": f"本周共 {github_commits['total']} 次提交，涉及 {github_commits['authors']} 位开发者",
        "jira_summary": f"完成 {jira_tasks['completed']} 个任务，关闭 {jira_tasks['closed']} 个Bug",
        "highlights": github_commits.get('highlights', [])
    }

    return report
```

### n8n工作流设计

```
[定时触发器] → [GitHub API] → [Jira API] → [Python聚合] → [Markdown格式化] → [邮件发送]
     (每周一9:00)    (获取提交)    (获取任务)   (数据处理)    (生成报告)    (发给团队)
```

整个流程从原来的1小时手动整理，变成了完全自动化。现在周一早上9点，团队的邮箱里准时收到周报。

## 踩坑记录

**问题1：n8n的Function节点内存限制**

默认Function节点只能使用少量内存，处理大数据集会报错。解决方法是在docker-compose中增加内存限制：

```yaml
services:
  n8n:
    image: n8nio/n8n
    environment:
      - N8N_DEFAULT_BINARY_DATA_MODE=filesystem
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
```

**问题2：API速率限制**

GitHub API默认每小时只能调用60次（未认证）。解决方法是使用Personal Access Token，将限制提升到5000次/小时。

```python
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
```

**问题3：时区问题**

n8n默认使用UTC时区，导致定时任务在错误的时间触发。需要在环境变量中设置时区：

```yaml
environment:
  - GENERIC_TIMEZONE=Asia/Shanghai
  - TZ=Asia/Shanghai
```

## 效果对比

| 指标 | 手动方式 | 自动化后 |
|:---|:---|:---|
| 时间消耗 | 60分钟/周 | 0分钟/周 |
| 遗漏率 | 约15% | 0% |
| 数据准确性 | 依赖人工核对 | 100% API直接获取 |
| 可扩展性 | 每增加一个数据源都要额外时间 | 拖拽添加新节点即可 |

## 扩展思路

这个工作流可以进一步扩展：

1. **添加Slack讨论热点**：通过Slack API获取上周讨论最多的频道和话题
2. **自动生成图表**：用Python的matplotlib生成提交频率图、任务完成趋势图
3. **智能摘要**：接入GPT-4，自动为每个PR生成一句话摘要
4. **异常预警**：如果某周提交数为0或Bug关闭数为0，自动@相关负责人

## 总结

自动化不是目的，解放时间才是。n8n + Python的组合让我每周多出4小时专注于真正有价值的工作——写代码和解决问题。

如果你也在被重复性任务困扰，强烈推荐试试这个组合。初期搭建可能需要1-2小时，但回报是长期的。

**下一步行动：**
- 访问 [n8n官网](https://n8n.io) 了解基础概念
- 用Docker本地部署一个实例：`docker run -it --rm -p 5678:5678 n8nio/n8n`
- 从最简单的定时邮件开始，逐步扩展你的工作流

你平时最常被哪些重复性任务困扰？欢迎在评论区分享，也许我可以帮你设计一个自动化方案。
