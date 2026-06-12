import re
"""
规则摘要模块 - 不使用 AI API，基于规则生成摘要
"""

from typing import Dict, List
from src.logger import get_logger


def generate_summary(ranked_items, top_n=6, important_keywords=None):
    """生成今日重点摘要（最多 top_n 条）"""
    if not ranked_items:
        return []

    if important_keywords is None:
        important_keywords = []

    top_items = ranked_items[:top_n]
    summaries = []

    for item in top_items:
        title = item.get("title", "")
        summary_text = item.get("summary", "")
        category = item.get("category", "")
        one_line = _extract_one_line(summary_text, title)
        importance = _determine_importance(title, category, important_keywords)
        personal_value = _determine_personal_value(title, summary_text, category)

        summaries.append({
            "title": title,
            "link": item.get("link", ""),
            "source": item.get("source_name", ""),
            "category": category,
            "summary": one_line,
            "importance": importance,
            "personal_value": personal_value,
        })

    return summaries


def _extract_one_line(summary, title):
    if summary:
        for sep in ["。", "！", "？", ".", "!", "\n"]:
            if sep in summary:
                first = summary.split(sep)[0].strip()
                if len(first) > 10:
                    return first[:120]
        if len(summary) > 10:
            return summary[:120]
    return f"关注: {title[:80]}"


def _determine_importance(title, category, keywords):
    title_lower = title.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        # 短关键词（<=3 字符）用词边界匹配避免误触（如 Air 误匹配 AI）
        if len(kw) <= 3:
            if re.search(r'\b' + re.escape(kw_lower) + r'\b', title_lower):
                return f"涉及重要关键词「{kw}」"
        else:
            if kw_lower in title_lower:
                return f"涉及重要关键词「{kw}」"
    category_importance = {
        "科技与AI": "AI/科技行业发展动态",
        "设计与创意": "设计趋势与创新参考",
        "机会与副业": "潜在机会信息",
        "国内大事": "国内重要时事",
        "国际大事": "国际重要时事",
        "财经商业": "财经商业变化",
        "英语与学习": "英语学习资源",
        "社会民生": "社会热点关注",
    }
    return category_importance.get(category, "值得关注的信息")


def _determine_personal_value(title, summary, category):
    t = (title + " " + summary).lower()
    values = []
    # 短关键词用词边界匹配
    def match_word(word, text):
        if len(word) <= 3:
            return bool(re.search(r'\b' + re.escape(word) + r'\b', text))
        return word in text
    if any(match_word(kw, t) for kw in ["ai", "人工智能", "chatgpt", "openai", "大模型"]):
        values.append("可用于 AI 学习")
    if any(match_word(kw, t) for kw in ["设计", "视觉", "ui", "ux", "创意", "审美", "色彩", "字体"]):
        values.append("对视觉传达专业有参考价值")
    if any(match_word(kw, t) for kw in ["英语", "雅思", "词汇", "语法", "句子"]):
        values.append("可用于英语学习")
    if any(match_word(kw, t) for kw in ["兼职", "副业", "赚钱", "实习", "就业", "招聘", "比赛", "奖项"]):
        values.append("可关注兼职/副业机会")
    if not values:
        if category == "设计与创意":
            values.append("可收集到设计灵感库")
        elif category == "英语与学习":
            values.append("可融入日常英语学习")
        elif category == "科技与AI":
            values.append("可加深对 AI 行业理解")
        else:
            values.append("可拓宽知识面")
    return "；".join(values)


def generate_useful_tips(ranked_items):
    tips = []
    categories_found = set(item.get("category", "") for item in ranked_items)

    category_tips = {
        "科技与AI": ("AI学习", "关注 AI 行业动态，尝试将新技术应用到设计工具链中"),
        "设计与创意": ("视觉设计", "观察设计趋势变化，收集值得参考的案例到灵感库"),
        "英语与学习": ("英语学习", "积累今日出现的实用表达，逐步提升英语阅读能力"),
        "机会与副业": ("赚钱机会", "留意此类信息，但不要冲动投入，先观察了解"),
        "国内大事": ("知识积累", "了解国内重要新闻，保持对社会环境的认知"),
        "国际大事": ("知识积累", "了解国际形势变化，培养全球视野"),
        "财经商业": ("经济认知", "了解商业动态，培养经济思维能力"),
        "社会民生": ("社会认知", "关注民生变化，理解社会运行"),
    }

    for cat in ["科技与AI", "设计与创意", "英语与学习", "机会与副业", "国内大事", "国际大事", "财经商业", "社会民生"]:
        if cat in categories_found:
            label, tip = category_tips.get(cat, ("信息", "保持关注"))
            tips.append({"label": label, "tip": tip})

    return tips


def generate_english_sentence(ranked_items):
    """根据当天内容生成一句 A2-B1 难度英文句子"""
    if not ranked_items:
        return {
            "chinese": "今天没有获取到新内容。",
            "english": "No new content was fetched today.",
            "structure": "被动语态: [Subject] + was/were + [past participle]",
            "template": "No new [something] was/were [verb] today.",
        }

    top = ranked_items[0]
    title = top.get("title", "")
    category = top.get("category", "")

    category_sentences = {
        "科技与AI": {
            "chinese": "今天有关于人工智能的重要新闻。",
            "english": "There is important news about artificial intelligence today.",
            "structure": "There be 句型: There is/are + [名词] + [修饰语]",
            "template": "There is/are [adjective] [noun] about [topic] today.",
        },
        "设计与创意": {
            "chinese": "这个设计看起来很有趣。",
            "english": "This design looks very interesting.",
            "structure": "系动词 + 形容词: [主语] + looks/seems + [形容词]",
            "template": "This [noun] looks/seems [adjective].",
        },
        "英语与学习": {
            "chinese": "我今天学习了新的英语单词。",
            "english": "I learned some new English words today.",
            "structure": "一般过去时: [主语] + [过去式动词] + [宾语]",
            "template": "I learned [something] today.",
        },
    }

    default = {
        "chinese": "今天的新闻头条是：" + title[:50],
        "english": f"The headline today is: {title[:80]}",
        "structure": "简单主谓宾: [主语] + is + [表语/宾语]",
        "template": "The [topic] today is [description].",
    }

    return category_sentences.get(category, default)