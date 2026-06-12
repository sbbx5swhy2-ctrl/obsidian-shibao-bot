"""
Obsidian 写入模块 - 安全写入 Markdown 文件到 Obsidian 仓库
"""

import os
from datetime import datetime
from typing import Optional
from src.safety import (
    clean_duplicate_frontmatter,
    resolve_vault_root,
    resolve_file_path,
    atomic_write,
    BackupManager,
    Lock,
    replace_auto_section,
    extract_user_section,
    has_auto_markers,
    MARKER_START,
    MARKER_END,
)
from src.utils import ensure_dir, get_today_str, get_now_local
from src.logger import get_logger


class ObsidianWriter:
    """安全地写入文件到 Obsidian 仓库"""

    def __init__(self, config, project_dir: str):
        self.config = config
        self.project_dir = project_dir
        self.vault_path = config.vault_path
        self.root_folder = config.root_folder
        self.backup_dir = os.path.join(project_dir, "backups")
        self.lock_dir = os.path.join(project_dir, "state")

        self._resolved_root: Optional[str] = None
        self.backup_manager = BackupManager(self.backup_dir, config.safe_write_config.get("max_backups_per_file", 5))

    @property
    def resolved_root(self) -> str:
        if self._resolved_root is None:
            self._resolved_root = resolve_vault_root(self.vault_path, self.root_folder)
        return self._resolved_root

    def get_today_file_path(self, today_str: Optional[str] = None) -> str:
        """获取今天应该写入的文件路径"""
        if today_str is None:
            today_str = get_today_str(self.config.timezone)
        
        year, month = today_str.split("-")[0], today_str.split("-")[1]
        relative = os.path.join(year, month, f"{today_str}.md")
        return resolve_file_path(self.vault_path, self.root_folder, relative)

    def get_today_dir_path(self, today_str: Optional[str] = None) -> str:
        """获取今天的目录路径"""
        if today_str is None:
            today_str = get_today_str(self.config.timezone)
        year, month = today_str.split("-")[0], today_str.split("-")[1]
        dir_path = os.path.join(self.resolved_root, year, month)
        return dir_path

    def get_index_file_path(self) -> str:
        """获取首页文件路径"""
        return os.path.join(self.resolved_root, self.root_folder + "首页.md")

    def acquire_lock(self) -> Optional[Lock]:
        """获取运行锁"""
        lock = Lock(self.lock_dir, "shibao", self.config.safe_write_config.get("max_lock_minutes", 30))
        if lock.try_acquire():
            return lock
        return None

    def ensure_daily_dir(self, today_str: Optional[str] = None) -> bool:
        """确保今日目录存在"""
        dir_path = self.get_today_dir_path(today_str)
        return ensure_dir(dir_path)

    def create_index_if_not_exists(self) -> bool:
        """如果首页不存在，创建首页"""
        index_path = self.get_index_file_path()
        if os.path.exists(index_path):
            return False
        
        from src.render_markdown import render_index_md
        content = render_index_md()
        return atomic_write(index_path, content, self.backup_manager)

    def write_daily_file(self, new_content: str, today_str: Optional[str] = None) -> bool:
        """写入每日 Markdown 文件，保护「我的记录」区域"""
        logger = get_logger()
        file_path = self.get_today_file_path(today_str)
        self.ensure_daily_dir(today_str)

        if not os.path.exists(file_path):
            # 文件不存在，直接写入完整内容
            success = atomic_write(file_path, new_content, self.backup_manager)
            if success:
                logger.info(f"已创建新文件: {file_path}")
            return success
        else:
            # 文件已存在，替换自动生成区域
            with open(file_path, "r", encoding="utf-8") as f:
                existing = f.read()

            if has_auto_markers(existing):
                existing = clean_duplicate_frontmatter(existing)
                updated = replace_auto_section(existing, new_content)
                success = atomic_write(file_path, updated, self.backup_manager)
                if success:
                    logger.info(f"已更新文件（保留用户记录）: {file_path}")
                return success
            else:
                # 文件没有标记，备份后创建带标记的新文件
                logger.info("文件没有自动生成标记，备份后创建新格式")
                combined = new_content + "\n\n---\n\n## 我的记录\n\n" + existing.strip()
                success = atomic_write(file_path, combined, self.backup_manager)
                return success