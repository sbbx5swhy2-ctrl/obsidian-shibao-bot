"""
日志模块 - 每次运行时创建日志文件 logs/YYYY-MM-DD.log
"""

import os
import logging
from datetime import datetime
from typing import Optional


class ShibaoLogger:
    """时报机器人日志管理器"""
    
    def __init__(self, log_dir: str, timezone_str: str = "Asia/Shanghai"):
        self.log_dir = log_dir
        self.timezone_str = timezone_str
        self.logger: Optional[logging.Logger] = None
        self._log_path: Optional[str] = None
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        os.makedirs(self.log_dir, exist_ok=True)
    
    @property
    def today_log_path(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{today}.log")
    
    def get_logger(self) -> logging.Logger:
        if self.logger is not None:
            return self.logger
        
        self._log_path = self.today_log_path
        self.logger = logging.getLogger("shibao")
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        fh = logging.FileHandler(self._log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)
        
        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        self.logger.addHandler(ch)
        
        return self.logger
    
    def close(self):
        if self.logger:
            for h in self.logger.handlers[:]:
                h.close()
                self.logger.removeHandler(h)


# 全局默认实例
_default_logger: Optional[ShibaoLogger] = None


def init_logger(log_dir: str, timezone_str: str = "Asia/Shanghai") -> logging.Logger:
    global _default_logger
    _default_logger = ShibaoLogger(log_dir, timezone_str)
    return _default_logger.get_logger()


def get_logger() -> logging.Logger:
    if _default_logger is None:
        return init_logger("logs")
    return _default_logger.get_logger()


def close_logger():
    if _default_logger:
        _default_logger.close()
