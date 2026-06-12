"""
条目规范化模块 - 去重、时间规范化
"""

import json
import os
from typing import Dict, List
from src.utils import title_hash, normalize_datetime
from src.logger import get_logger


class SeenManager:
    """已见条目管理器 - 防止重复处理"""

    def __init__(self, state_dir):
        self.state_dir = state_dir
        self.state_file = os.path.join(state_dir, "seen.json")
        self._data = {"urls": [], "guids": [], "title_hashes": []}
        self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {"urls": [], "guids": [], "title_hashes": []}

    def _save(self):
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def is_seen(self, url, guid, title):
        h = title_hash(title)
        return url in self._data["urls"] or guid in self._data["guids"] or h in self._data["title_hashes"]

    def mark_seen(self, url, guid, title):
        h = title_hash(title)
        if url not in self._data["urls"]:
            self._data["urls"].append(url)
        if guid not in self._data["guids"]:
            self._data["guids"].append(guid)
        if h not in self._data["title_hashes"]:
            self._data["title_hashes"].append(h)
        self._save()

    def cleanup(self, max_items=10000):
        for key in self._data:
            if len(self._data[key]) > max_items:
                self._data[key] = self._data[key][-max_items:]
        self._save()


def normalize_items(raw_items, seen_manager, tz_name="Asia/Shanghai"):
    logger = get_logger()
    total_before = sum(len(items) for items in raw_items.values())
    logger.info(f"去重前总条目数: {total_before}")
    result = {}
    total_after = 0
    total_seen = 0
    for category, items in raw_items.items():
        normalized = []
        for item in items:
            if item.get("published"):
                item["published"] = normalize_datetime(item["published"], tz_name)
            url = item.get("link", "")
            guid = item.get("guid", "")
            title = item.get("title", "")
            if not url and not guid:
                continue
            if seen_manager.is_seen(url, guid, title):
                total_seen += 1
                continue
            seen_manager.mark_seen(url, guid, title)
            normalized.append(item)
        result[category] = normalized
        total_after += len(normalized)
    logger.info(f"去重后总条目数: {total_after} (已过滤 {total_seen} 条重复)")
    return result