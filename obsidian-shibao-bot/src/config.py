"""
配置加载模块 - 读取 config.yaml
"""

import os
import yaml
from typing import Any, Dict, List, Optional


class Config:
    """应用配置"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._data: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}
    
    @property
    def vault_path(self) -> str:
        return self._data.get("vault_path", "")
    
    @property
    def root_folder(self) -> str:
        return self._data.get("root_folder", "时报")
    
    @property
    def timezone(self) -> str:
        return self._data.get("timezone", "Asia/Shanghai")
    
    @property
    def daily_run_time(self) -> str:
        return self._data.get("daily_run_time", "08:30")
    
    @property
    def max_items_per_day(self) -> int:
        return int(self._data.get("max_items_per_day", 36))
    
    @property
    def max_items_per_category(self) -> int:
        return int(self._data.get("max_items_per_category", 8))
    
    @property
    def summary_top_n(self) -> int:
        return int(self._data.get("summary_top_n", 6))
    
    @property
    def safe_write_config(self) -> Dict[str, Any]:
        return self._data.get("safe_write", {})
    
    @property
    def categories(self) -> List[Dict[str, Any]]:
        return self._data.get("categories", [])
    
    @property
    def category_names(self) -> List[str]:
        return [c["name"] for c in self.categories]
    
    @property
    def rss_sources(self) -> Dict[str, List[str]]:
        return self._data.get("rss_sources", {})
    
    @property
    def important_keywords(self) -> List[str]:
        return self._data.get("important_keywords", [])
    
    @property
    def content_preferences(self) -> Dict[str, Any]:
        return self._data.get("content_preferences", {})
    
    @property
    def source_policy(self) -> Dict[str, Any]:
        return self._data.get("source_policy", {})
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()
