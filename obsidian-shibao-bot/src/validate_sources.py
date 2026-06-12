"""
RSS 源验证模块 - 检查 RSS 源是否可用
"""

import feedparser
from typing import Dict, List, Tuple
from src.logger import get_logger


def validate_source(url, timeout=10):
    """验证单个 RSS 源是否可用，返回 (是否可用, 信息)"""
    try:
        feed = feedparser.parse(url)
        if feed.entries:
            return True, f"成功，获取到 {len(feed.entries)} 条条目"
        if feed.bozo and feed.bozo_exception:
            return False, f"解析失败: {feed.bozo_exception}"
        return False, "无条目返回"
    except Exception as e:
        return False, f"抓取异常: {e}"


def validate_all_sources(rss_sources):
    """验证所有 RSS 源"""
    results = {}
    for category, urls in rss_sources.items():
        cat_results = []
        for url in urls:
            ok, msg = validate_source(url)
            cat_results.append((url, ok, msg))
        results[category] = cat_results
    return results


def print_validation_results(results):
    """打印验证结果"""
    logger = get_logger()
    for category, items in results.items():
        logger.info(f"=== {category} ===")
        for url, ok, msg in items:
            status = "✓" if ok else "✗"
            logger.info(f"  {status} {url}")
            logger.info(f"     {msg}")