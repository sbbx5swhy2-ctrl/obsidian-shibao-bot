"""
Markdown 生成模块
"""

from datetime import datetime
from src.utils import get_today_str, get_now_local
from src.safety import MARKER_START, MARKER_END


def render_daily_markdown(
    today_str, now_local, summaries, ranked_items,
    grouped_items, useful_tips, english_sentence,
    has_content, timezone="Asia/Shanghai"
):
    """渲染每日 Markdown 文件内容"""
    time_str = now_local.strftime("%Y-%m-%d %H:%M")
    
    lines = []
    lines.append("---")
    lines.append(f'title: "时报｜{today_str}"')
    lines.append(f"date: {today_str}")
    lines.append(f"created: {time_str}")
    lines.append(f"updated: {time_str}")
    lines.append("tags:")
    lines.append("  - 时报")
    lines.append("  - 每日信息")
    lines.append("  - 自动化")
    lines.append("  - AI学习")
    lines.append("  - 视觉传达")
    lines.append("---")
    lines.append("")
    lines.append(f"# 时报｜{today_str}")
    lines.append("")
    lines.append(f"> 自动生成时间：{time_str}")
    lines.append("> 信息来源：RSS / 公开信息源")
    lines.append("> 说明：本文件会自动更新，但「我的记录」区域不会被覆盖。")
    lines.append("> 使用方式：先看「今日重点」，再看「对我有用」。")
    lines.append("")
    lines.append(MARKER_START)
    lines.append("")
    
    if not has_content:
        lines.append("## 今日重点")
        lines.append("")
        lines.append("本次未获取到新内容。")
        lines.append("")
        lines.append("请检查：")
        lines.append("1. config.yaml 中是否配置了 RSS 源")
        lines.append("2. 网络连接是否正常")
        lines.append("3. 查看日志文件了解详情")
        lines.append("")
        lines.append(MARKER_END)
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 我的记录")
        lines.append("")
        lines.append("这里是我手动记录的内容。自动化脚本不能覆盖这一部分。")
        return "\n".join(lines)
    
    # 今日重点
    lines.append("## 今日重点")
    lines.append("")
    lines.append("| 重点 | 为什么重要 | 对我有什么用 |")
    lines.append("|---|---|---|")
    for s in summaries:
        title_clean = s["title"][:60].replace("|", "\\|")
        imp = s["importance"][:60].replace("|", "\\|")
        val = s["personal_value"][:60].replace("|", "\\|")
        lines.append(f"| {title_clean} | {imp} | {val} |")
    lines.append("")
    
    # 时间线
    lines.append("## 时间线")
    lines.append("")
    for item in ranked_items[:20]:
        pub = item.get("published")
        time_tag = ""
        if pub and isinstance(pub, datetime):
            time_tag = pub.strftime("%H:%M")
        else:
            time_tag = "--:--"
        cat = item.get("category", "未分类")
        title = item.get("title", "")
        summary = (item.get("summary", "") or "")[:120]
        source = item.get("source_name", "")
        link = item.get("link", "")
        lines.append(f"### {time_tag}｜{cat}")
        lines.append("")
        lines.append(f"- **{title}**")
        if summary:
            lines.append(f"  - 摘要：{summary}")
        lines.append(f"  - 来源：{source}")
        lines.append(f"  - 链接：{link}")
        lines.append("")
    
    # 分类速览
    lines.append("## 分类速览")
    lines.append("")
    cat_order = ["国内大事", "国际大事", "财经商业", "科技与AI", "设计与创意", "英语与学习", "机会与副业", "社会民生"]
    for cat_name in cat_order:
        items = grouped_items.get(cat_name, [])
        if not items:
            continue
        lines.append(f"### {cat_name}")
        lines.append("")
        for item in items:
            title = item.get("title", "")
            summary = (item.get("summary", "") or "")[:120]
            pub = item.get("published")
            time_str = ""
            if pub and isinstance(pub, datetime):
                time_str = pub.strftime("%H:%M")
            source = item.get("source_name", "")
            link = item.get("link", "")
            lines.append(f"- **{title}**")
            if summary:
                lines.append(f"  - 摘要：{summary}")
            if time_str:
                lines.append(f"  - 时间：{time_str}")
            lines.append(f"  - 来源：{source}")
            lines.append(f"  - 链接：{link}")
            lines.append("")
    
    # 对我有用
    lines.append("## 对我有用")
    lines.append("")
    lines.append("根据今天的信息，以下是对我有实际价值的提醒：")
    lines.append("")
    for tip in useful_tips:
        lines.append(f"- **{tip['label']}**：{tip['tip']}")
    lines.append("")
    
    # 今日一句英文
    lines.append("## 今日一句英文")
    lines.append("")
    lines.append(f"- 中文：{english_sentence.get('chinese', '')}")
    lines.append(f"- 英文：{english_sentence.get('english', '')}")
    lines.append(f"- 结构：{english_sentence.get('structure', '')}")
    lines.append(f"- 可替换模板：{english_sentence.get('template', '')}")
    lines.append("")
    
    lines.append(MARKER_END)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 我的记录")
    lines.append("")
    lines.append("这里是我手动记录的内容。自动化脚本不能覆盖这一部分。")
    
    return "\n".join(lines)


def render_index_md():
    """渲染时报首页 Markdown"""
    lines = []
    lines.append("---")
    lines.append('title: "时报首页"')
    lines.append("tags:")
    lines.append("  - 时报")
    lines.append("  - 信息管理")
    lines.append("---")
    lines.append("")
    lines.append("# 时报首页")
    lines.append("")
    lines.append("## 最近时报")
    lines.append("")
    lines.append("```dataview")
    lines.append("TABLE date AS 日期, file.mtime AS 更新时间")
    lines.append('FROM "时报"')
    lines.append('WHERE file.name != "时报首页"')
    lines.append("SORT file.name DESC")
    lines.append("LIMIT 30")
    lines.append("```")
    lines.append("")
    lines.append("## 使用说明")
    lines.append("")
    lines.append("- 每天的信息会自动进入 `时报/YYYY/MM/YYYY-MM-DD.md`")
    lines.append("- 自动生成区域可以更新")
    lines.append("- 「我的记录」区域不会被覆盖")
    lines.append("- 如果没有看到新文件，先检查自动任务和日志")
    lines.append("")
    lines.append("## 分类")
    lines.append("")
    lines.append("- 国内大事")
    lines.append("- 国际大事")
    lines.append("- 财经商业")
    lines.append("- 科技与AI")
    lines.append("- 设计与创意")
    lines.append("- 英语与学习")
    lines.append("- 机会与副业")
    lines.append("- 社会民生")
    lines.append("")
    lines.append("注意：")
    lines.append("- 如果 Dataview 插件没装，上面的查询不会显示表格，但文件本身仍然正常。")
    return "\n".join(lines)