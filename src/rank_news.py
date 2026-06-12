"""
新闻排序模块
"""

from datetime import datetime
from typing import Dict, List
from src.logger import get_logger


class NewsRanker:
    """新闻排序器 - 根据时间、关键词、分类优先级排序"""

    def __init__(self, important_keywords, category_priority):
        self.important_keywords = [kw.lower() for kw in important_keywords]
        self.category_priority = category_priority

    def rank_items(self, items):
        """排序所有条目，返回按权重降序排列的列表"""
        all_items = []
        for category, cat_items in items.items():
            for item in cat_items:
                item["_score"] = self._calculate_score(item, category)
                all_items.append(item)
        all_items.sort(key=lambda x: x["_score"], reverse=True)
        return all_items

    def _calculate_score(self, item, category):
        score = 0.0

        # 1. 分类优先级 (0-10)
        cat_priority = self.category_priority.get(category, 5)
        score += cat_priority * 2

        # 2. 时间分数 (0-10)
        published = item.get("published")
        if published and isinstance(published, datetime):
            age_hours = (datetime.now().astimezone() - published.astimezone()).total_seconds() / 3600
            if age_hours < 1:
                score += 10
            elif age_hours < 6:
                score += 8
            elif age_hours < 24:
                score += 6
            elif age_hours < 72:
                score += 4
            else:
                score += 2
        else:
            score += 1

        # 3. 关键词分数 (0-10)
        title = (item.get("title", "") or "").lower()
        summary = (item.get("summary", "") or "").lower()
        text = title + " " + summary
        keyword_matches = sum(1 for kw in self.important_keywords if kw in text)
        score += min(keyword_matches * 2, 10)

        return score

    @staticmethod
    def apply_limits(ranked_items, max_per_category, max_total):
        """应用分类上限和总数上限"""
        limited = {}
        category_count = {}
        total_count = 0

        for item in ranked_items:
            cat = item.get("category", "未分类")
            if category_count.get(cat, 0) >= max_per_category:
                continue
            if total_count >= max_total:
                break
            if cat not in limited:
                limited[cat] = []
            limited[cat].append(item)
            category_count[cat] = category_count.get(cat, 0) + 1
            total_count += 1

        return limited