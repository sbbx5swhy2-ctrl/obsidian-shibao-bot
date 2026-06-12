"""
RSS 抓取模块 - 使用 requests 带超时，避免卡死
"""

import feedparser
import time
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from src.logger import get_logger

REQUEST_TIMEOUT = 12  # seconds per feed
USER_AGENT = "obsidian-shibao-bot/1.0 (RSS Reader)"


class RSSFetcher:
    """RSS 源抓取器"""

    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = timeout
        self.errors: List[Tuple[str, str]] = []

    def fetch_feed(self, url: str) -> Optional[Dict[str, Any]]:
        """抓取单个 RSS feed，返回解析后的字典，失败返回 None"""
        try:
            resp = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": USER_AGENT},
                allow_redirects=True,
            )
            resp.raise_for_status()
            content = resp.content
            feed = feedparser.parse(content)
        except requests.Timeout:
            logger = get_logger()
            logger.warning(f"RSS 超时 [{url}]")
            self.errors.append((url, "timeout"))
            return None
        except requests.RequestException as e:
            logger = get_logger()
            logger.warning(f"RSS 请求失败 [{url}]: {e}")
            self.errors.append((url, str(e)))
            return None
        except Exception as e:
            logger = get_logger()
            logger.warning(f"RSS 解析失败 [{url}]: {e}")
            self.errors.append((url, str(e)))
            return None

        if not feed.entries:
            if feed.bozo and feed.bozo_exception:
                logger = get_logger()
                logger.warning(f"RSS 解析异常 [{url}]: {feed.bozo_exception}")
            else:
                logger = get_logger()
                logger.info(f"RSS 无条目 [{url}]")
            return None

        return {
            "url": url,
            "feed_title": feed.feed.get("title", ""),
            "feed_link": feed.feed.get("link", ""),
            "entries": feed.entries,
        }

    def fetch_all(self, rss_sources: Dict[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
        """按分类抓取所有 RSS 源"""
        self.errors = []
        result: Dict[str, List[Dict[str, Any]]] = {}
        logger = get_logger()

        for category, urls in rss_sources.items():
            category_entries = []
            for url in urls:
                if not url or not url.strip():
                    continue
                logger.info(f"抓取 [{category}] {url[:60]}...")
                feed_data = self.fetch_feed(url.strip())
                if feed_data:
                    count = len(feed_data["entries"])
                    logger.info(f"  -> {count} 条")
                    for entry in feed_data["entries"]:
                        category_entries.append(self._extract_entry(entry, category, feed_data))
                time.sleep(0.3)
            if category_entries:
                result[category] = category_entries

        return result

    def _extract_entry(self, entry, category, feed_data):
        """从 feedparser 条目中提取标准化字段"""
        title = entry.get("title", "(无标题)")
        link = entry.get("link", entry.get("id", ""))
        guid = entry.get("id", link)

        summary = ""
        if hasattr(entry, "summary"):
            summary = entry.summary
        elif hasattr(entry, "description"):
            summary = entry.description
        elif hasattr(entry, "content"):
            try:
                summary = entry.content[0].get("value", "")
            except (IndexError, TypeError, AttributeError):
                pass

        summary = self._strip_html(summary)[:300]

        pub_time = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_time = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub_time = datetime(*entry.updated_parsed[:6])

        return {
            "title": title,
            "link": link,
            "guid": guid,
            "category": category,
            "source_name": feed_data.get("feed_title", ""),
            "source_url": feed_data.get("feed_link", ""),
            "published": pub_time,
            "summary": summary,
            "estimated_time": pub_time is None,
        }

    @staticmethod
    def _strip_html(text: str) -> str:
        """简易 HTML 标签清理"""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @property
    def has_errors(self):
        return len(self.errors) > 0

    def get_error_summary(self):
        return [f"[{url}] {err}" for url, err in self.errors]