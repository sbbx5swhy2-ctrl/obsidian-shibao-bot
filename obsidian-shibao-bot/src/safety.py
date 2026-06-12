import re
"""
安全模块 - 路径检查、安全写入、锁机制、备份
"""

import os
import shutil
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from src.logger import get_logger


# ========== 路径安全检查 ==========

def resolve_vault_root(vault_path: str, root_folder: str) -> str:
    """
    解析并验证 Obsidian 仓库中的目标根目录路径。
    返回规范化后的绝对路径。
    如果路径越界（不在 vault_path/root_folder 内），抛出 ValueError。
    """
    if not vault_path:
        raise ValueError("vault_path 未设置，请在 config.yaml 中配置")
    
    vault_abs = os.path.abspath(os.path.normpath(vault_path))
    if not os.path.exists(vault_abs):
        raise FileNotFoundError(f"vault_path 不存在: {vault_abs}。请检查 iCloud Drive 是否已同步到本机。")
    
    target = os.path.abspath(os.path.normpath(os.path.join(vault_abs, root_folder)))
    
    # 检查是否越界：target 必须以 vault_abs 开头
    if not target.startswith(vault_abs + os.sep) and target != vault_abs:
        raise ValueError(f"目标路径越界！{target} 不是 {vault_abs} 的子目录")
    
    # 创建目录（如果不存在）
    os.makedirs(target, exist_ok=True)
    
    return target


def resolve_file_path(vault_path: str, root_folder: str, relative_path: str) -> str:
    """
    解析并验证目标文件路径是否在安全范围内。
    """
    root = resolve_vault_root(vault_path, root_folder)
    file_path = os.path.abspath(os.path.normpath(os.path.join(root, relative_path)))
    
    if not file_path.startswith(root + os.sep) and file_path != root:
        raise ValueError(
            f"文件路径越界！{file_path} 不在安全目录 {root} 内"
        )
    return file_path


# ========== 锁机制 ==========

class Lock:
    """防止并发运行的文件锁"""
    
    def __init__(self, lock_dir: str, lock_name: str = "shibao", max_lock_minutes: int = 30):
        self.lock_dir = lock_dir
        self.lock_name = lock_name
        self.max_lock_minutes = max_lock_minutes
        self.lock_file = os.path.join(lock_dir, f"{lock_name}.lock")
        self._acquired = False
    
    def try_acquire(self) -> bool:
        """尝试获取锁，如果成功返回 True"""
        os.makedirs(self.lock_dir, exist_ok=True)
        
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    lock_data = json.load(f)
                lock_time = datetime.fromisoformat(lock_data.get("time", ""))
                elapsed = (datetime.now() - lock_time).total_seconds() / 60
                
                if elapsed < self.max_lock_minutes:
                    logger = get_logger()
                    logger.warning(f"锁文件存在且未过期（{elapsed:.1f}分钟），跳过本次运行")
                    return False
                else:
                    logger = get_logger()
                    logger.warning(f"锁文件过期（{elapsed:.1f}分钟），清理旧锁")
                    os.remove(self.lock_file)
            except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
                logger = get_logger()
                logger.warning(f"锁文件异常 ({e})，清理后重试")
                try:
                    os.remove(self.lock_file)
                except OSError:
                    pass
        
        lock_data = {
            "time": datetime.now().isoformat(),
            "pid": os.getpid(),
        }
        try:
            with open(self.lock_file, "w", encoding="utf-8") as f:
                json.dump(lock_data, f)
            self._acquired = True
            return True
        except OSError as e:
            logger = get_logger()
            logger.error(f"无法写入锁文件: {e}")
            return False
    
    def release(self):
        """释放锁"""
        if self._acquired and os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
                self._acquired = False
            except OSError as e:
                logger = get_logger()
                logger.warning(f"释放锁文件失败: {e}")

    def __enter__(self):
        if not self.try_acquire():
            raise RuntimeError("无法获取锁，可能已有其他进程在运行")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# ========== 备份机制 ==========

class BackupManager:
    """备份管理器，用于写入前备份已有文件"""
    
    def __init__(self, backup_dir: str, max_backups: int = 5):
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _backup_key(self, file_path: str) -> str:
        """生成备份 key（基于原始文件路径的 hash）"""
        import hashlib
        return hashlib.md5(file_path.encode("utf-8")).hexdigest()
    
    def backup(self, file_path: str) -> Optional[str]:
        """
        备份文件，返回备份路径。如果文件不存在，返回 None。
        """
        if not os.path.exists(file_path):
            return None
        
        key = self._backup_key(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = os.path.basename(file_path)
        backup_name = f"{timestamp}_{basename}"
        backup_subdir = os.path.join(self.backup_dir, key)
        os.makedirs(backup_subdir, exist_ok=True)
        
        backup_path = os.path.join(backup_subdir, backup_name)
        shutil.copy2(file_path, backup_path)
        
        self._cleanup_old_backups(key)
        
        return backup_path
    
    def _cleanup_old_backups(self, key: str):
        """清理旧备份，只保留最近 N 个"""
        backup_subdir = os.path.join(self.backup_dir, key)
        if not os.path.exists(backup_subdir):
            return
        
        backups = sorted([
            os.path.join(backup_subdir, f) for f in os.listdir(backup_subdir)
            if os.path.isfile(os.path.join(backup_subdir, f))
        ], key=os.path.getmtime)
        
        while len(backups) > self.max_backups:
            old = backups.pop(0)
            try:
                os.remove(old)
            except OSError:
                pass


# ========== 原子写入 ==========

def atomic_write(file_path: str, content: str, backup_manager: Optional[BackupManager] = None) -> bool:
    """
    原子写入文件：
    1. 先写临时文件
    2. 校验内容
    3. 替换原文件
    """
    temp_path = file_path + ".tmp." + str(int(time.time()))
    try:
        # 写入临时文件
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # 校验：读取临时文件验证内容完整
        with open(temp_path, "r", encoding="utf-8") as f:
            written = f.read()
        if written != content:
            raise IOError("临时文件内容校验失败")
        
        # 备份原文件（如果存在）
        if backup_manager and os.path.exists(file_path):
            backup_manager.backup(file_path)
        
        # 原子替换
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        shutil.move(temp_path, file_path)
        return True
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"写入文件失败: {e}")
        # 清理临时文件
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False


# ========== 标记区域操作 ==========

MARKER_START = "<!-- AUTO-GENERATED-START -->"
MARKER_END = "<!-- AUTO-GENERATED-END -->"


def extract_user_section(content: str) -> str:
    """提取自动生成区域之后的内容（用户记录部分）"""
    if MARKER_END in content:
        idx = content.index(MARKER_END)
        return content[idx + len(MARKER_END):]
    return ""


def replace_auto_section(full_content: str, new_auto_content: str) -> str:
    """
    替换文件中的自动生成区域内容。
    如果文件没有标记，则将新内容插入到文件开头。
    """
    # 如果新内容包含完整 frontmatter，只保留 MARKER 起始之后的部分
    if MARKER_START in new_auto_content:
        start = new_auto_content.index(MARKER_START)
        new_auto_content = new_auto_content[start:]

    if MARKER_START in full_content and MARKER_END in full_content:
        start_idx = full_content.index(MARKER_START)
        end_idx = full_content.index(MARKER_END) + len(MARKER_END)
        user_section = full_content[end_idx:]
        return full_content[:start_idx] + new_auto_content + user_section
    else:
        return new_auto_content + "\n\n" + full_content.strip() + "\n"


def has_auto_markers(content: str) -> bool:
    """检查是否包含自动生成标记"""
    return MARKER_START in content and MARKER_END in content


def clean_duplicate_frontmatter(content: str) -> str:
    """清理累积的重复 frontmatter 块，只保留最后一个"""
    if MARKER_START not in content:
        return content
    marker_idx = content.index(MARKER_START)
    prefix = content[:marker_idx]
    suffix = content[marker_idx:]

    fm_pattern = r"(?ms)^---$.*?^---$\s*"
    matches = list(re.finditer(fm_pattern, prefix))
    if len(matches) <= 1:
        return content

    last_match = matches[-1]
    clean_prefix = prefix[last_match.end():]
    clean_prefix = last_match.group() + clean_prefix
    return clean_prefix + suffix


def parse_auto_section(content: str) -> str:
    """提取自动生成区域之间的内容"""
    if MARKER_START in content and MARKER_END in content:
        start_idx = content.index(MARKER_START) + len(MARKER_START)
        end_idx = content.index(MARKER_END)
        return content[start_idx:end_idx].strip()
    return ""
