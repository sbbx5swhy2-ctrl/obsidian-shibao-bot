"""
工具函数模块
"""

import os
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional


def ensure_dir(path: str) -> bool:
    """确保目录存在，不存在则创建"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def safe_path_join(*parts: str) -> str:
    """安全拼接路径，处理中文和空格"""
    return os.path.normpath(os.path.join(*parts))


def title_hash(title: str) -> str:
    """对标题生成 hash，用于去重"""
    return hashlib.md5(title.strip().lower().encode("utf-8")).hexdigest()


def normalize_datetime(dt: Optional[datetime], tz_name: str = "Asia/Shanghai") -> Optional[datetime]:
    """规范化时间为本地时区"""
    if dt is None:
        return None
    try:
        import tzdata  # noqa: F401
        from dateutil import tz
        local_tz = tz.gettz(tz_name)
        if dt.tzinfo is None:
            # 假设为 UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(local_tz)
    except Exception:
        # fallback: 如果时区处理失败，返回原时间
        return dt


def get_today_str(tz_name: str = "Asia/Shanghai") -> str:
    """获取本地时区今天的日期字符串 YYYY-MM-DD"""
    try:
        from dateutil import tz
        local_tz = tz.gettz(tz_name)
        now = datetime.now(local_tz)
        return now.strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def get_now_local(tz_name: str = "Asia/Shanghai") -> datetime:
    """获取本地时区当前时间"""
    try:
        from dateutil import tz
        local_tz = tz.gettz(tz_name)
        return datetime.now(local_tz)
    except Exception:
        return datetime.now()


def parse_date_str(date_str: str) -> Optional[datetime]:
    """尝试解析多种格式的日期字符串"""
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y %H:%M:%S %z",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def generate_lock_id() -> str:
    """生成唯一的运行 ID"""
    import uuid
    return str(uuid.uuid4())
