"""
HTML 邮件渲染模块 - 生成适合邮件阅读的 HTML 内容
"""

from datetime import datetime
from typing import Dict, List


def render_email_html(
    today_str: str,
    summaries: List[Dict],
    ranked_items: List[Dict],
    grouped_items: Dict[str, List[Dict]],
    useful_tips: List[Dict],
    english_sentence: Dict,
    has_content: bool,
) -> str:
    """渲染邮件 HTML 正文"""
    parts = []

    # CSS
    parts.append("""<html><head><meta charset="utf-8"><style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 680px; margin: 0 auto; padding: 20px; color: #333; background: #f8f9fa; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 24px; }
.header h1 { margin: 0 0 8px 0; font-size: 24px; }
.header p { margin: 4px 0; opacity: 0.9; font-size: 14px; }
.section { background: white; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.section h2 { margin: 0 0 12px 0; font-size: 18px; color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 6px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #f0f0ff; text-align: left; padding: 8px 10px; font-weight: 600; }
td { padding: 8px 10px; border-bottom: 1px solid #eee; vertical-align: top; }
.item { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #f0f0f0; }
.item:last-child { border-bottom: none; }
.item-title { font-weight: 600; font-size: 14px; color: #333; }
.item-meta { font-size: 12px; color: #888; margin: 4px 0; }
.item-summary { font-size: 13px; color: #555; margin: 4px 0; }
.item-link a { color: #667eea; font-size: 12px; text-decoration: none; }
.tag { display: inline-block; background: #e8e8ff; color: #667eea; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-right: 4px; }
.tip { padding: 8px 0; font-size: 13px; }
.tip strong { color: #764ba2; }
.english-box { background: #f0f0ff; border-left: 3px solid #667eea; padding: 12px 16px; border-radius: 4px; margin: 8px 0; }
.english-box .cn { font-size: 14px; color: #555; }
.english-box .en { font-size: 16px; color: #333; font-weight: 500; margin: 6px 0; }
.english-box .struct { font-size: 12px; color: #999; margin-top: 4px; }
.footer { text-align: center; color: #bbb; font-size: 11px; margin-top: 24px; padding: 16px; }
.no-content { text-align: center; color: #999; padding: 40px; font-size: 15px; }
</style></head><body>""")

    # Header
    parts.append('<div class="header">')
    parts.append(f'<h1>📰 时报 · {today_str}</h1>')
    parts.append(f'<p>自动生成 · 信息来源：RSS / 公开信息源</p>')
    parts.append('</div>')

    if not has_content:
        parts.append('<div class="section no-content">')
        parts.append('<p>😴 本次未获取到新内容。</p>')
        parts.append('<p>请检查 RSS 源配置或网络连接。</p>')
        parts.append('</div>')
        parts.append('</body></html>')
        return "\n".join(parts)

    # Today's Highlights
    if summaries:
        parts.append('<div class="section">')
        parts.append('<h2>🔥 今日重点</h2>')
        parts.append('<table><tr><th>新闻</th><th>为什么重要</th><th>对我有什么用</th></tr>')
        for s in summaries:
            title = s["title"][:60]
            imp = s["importance"][:60]
            val = s["personal_value"][:60]
            parts.append(f'<tr><td><strong>{title}</strong></td><td>{imp}</td><td>{val}</td></tr>')
        parts.append('</table></div>')

    # Timeline
    parts.append('<div class="section">')
    parts.append('<h2>📋 时间线</h2>')
    for item in ranked_items[:20]:
        pub = item.get("published")
        time_tag = pub.strftime("%H:%M") if pub and isinstance(pub, datetime) else "--:--"
        cat = item.get("category", "未分类")
        title = item.get("title", "")
        summary = (item.get("summary", "") or "")[:120]
        source = item.get("source_name", "")
        link = item.get("link", "")

        parts.append('<div class="item">')
        parts.append(f'<div class="item-title">{title}</div>')
        parts.append(f'<div class="item-meta"><span class="tag">{time_tag}</span> <span class="tag">{cat}</span> {source}</div>')
        if summary:
            parts.append(f'<div class="item-summary">{summary}</div>')
        if link:
            parts.append(f'<div class="item-link"><a href="{link}">阅读原文 →</a></div>')
        parts.append('</div>')
    parts.append('</div>')

    # Category Snapshot
    cat_order = ["国内大事", "国际大事", "财经商业", "科技与AI", "设计与创意", "英语与学习", "机会与副业", "社会民生"]
    for cat_name in cat_order:
        items = grouped_items.get(cat_name, [])
        if not items:
            continue
        parts.append('<div class="section">')
        parts.append(f'<h2>📂 {cat_name}</h2>')
        for item in items:
            title = item.get("title", "")
            summary = (item.get("summary", "") or "")[:120]
            pub = item.get("published")
            time_str = pub.strftime("%H:%M") if pub and isinstance(pub, datetime) else ""
            source = item.get("source_name", "")
            link = item.get("link", "")
            parts.append('<div class="item">')
            parts.append(f'<div class="item-title">{title}</div>')
            if time_str:
                parts.append(f'<div class="item-meta">{time_str} · {source}</div>')
            if summary:
                parts.append(f'<div class="item-summary">{summary}</div>')
            if link:
                parts.append(f'<div class="item-link"><a href="{link}">阅读原文 →</a></div>')
            parts.append('</div>')
        parts.append('</div>')

    # Useful Tips
    if useful_tips:
        parts.append('<div class="section">')
        parts.append('<h2>💡 对我有用</h2>')
        for tip in useful_tips:
            parts.append(f'<div class="tip"><strong>{tip["label"]}</strong>：{tip["tip"]}</div>')
        parts.append('</div>')

    # English Sentence
    parts.append('<div class="section">')
    parts.append('<h2>📖 今日一句英文</h2>')
    parts.append('<div class="english-box">')
    parts.append(f'<div class="cn">中文：{english_sentence.get("chinese", "")}</div>')
    parts.append(f'<div class="en">English：{english_sentence.get("english", "")}</div>')
    parts.append(f'<div class="struct">结构：{english_sentence.get("structure", "")}</div>')
    parts.append(f'<div class="struct">模板：{english_sentence.get("template", "")}</div>')
    parts.append('</div></div>')

    # Footer
    parts.append('<div class="footer">')
    parts.append('<p>🤖 由 obsidian-shibao-bot 自动生成 · 每日更新</p>')
    parts.append(f'<p>{today_str}</p>')
    parts.append('</div>')

    parts.append('</body></html>')
    return "\n".join(parts)
