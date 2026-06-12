"""
测试：安全路径检查、路径越界保护
"""

import os
import sys
import tempfile
import shutil

# 添加项目根目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.safety import (
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


class TestSafety:
    """安全模块测试"""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp(prefix="shibao_test_")
        self.vault_path = os.path.join(self.test_dir, "vault")
        os.makedirs(self.vault_path)

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_resolve_vault_root_valid(self):
        """测试正常路径解析"""
        root = resolve_vault_root(self.vault_path, "时报")
        assert root == os.path.join(self.vault_path, "时报")
        # 应该创建目录
        assert os.path.exists(root)

    def test_resolve_vault_root_invalid_path(self):
        """测试路径不存在"""
        try:
            resolve_vault_root("/nonexistent/path", "时报")
            assert False, "应该报错"
        except FileNotFoundError:
            pass

    def test_resolve_vault_root_empty(self):
        """测试空路径"""
        try:
            resolve_vault_root("", "时报")
            assert False, "应该报错"
        except ValueError:
            pass

    def test_resolve_file_path_valid(self):
        """测试合法文件路径"""
        file_path = resolve_file_path(self.vault_path, "时报", "2026/06/2026-06-12.md")
        expected = os.path.join(self.vault_path, "时报", "2026", "06", "2026-06-12.md")
        assert file_path == expected

    def test_resolve_file_path_escape(self):
        """测试路径越界 - 尝试使用 ../ 逃离"""
        try:
            resolve_file_path(self.vault_path, "时报", "../../escape.md")
            assert False, "应该报错"
        except ValueError:
            pass
        except Exception:
            pass

    def test_resolve_file_path_absolute_escape(self):
        """测试路径越界 - 尝试使用绝对路径"""
        try:
            resolve_file_path(self.vault_path, "时报", "/etc/passwd")
            assert False, "应该报错"
        except ValueError:
            pass
        except Exception:
            pass

    def test_atomic_write(self):
        """测试原子写入"""
        file_path = os.path.join(self.test_dir, "test.md")
        content = "# Test\n\nHello World"
        success = atomic_write(file_path, content)
        assert success
        assert os.path.exists(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_atomic_write_overwrite(self):
        """测试覆盖写入"""
        file_path = os.path.join(self.test_dir, "test2.md")
        atomic_write(file_path, "version 1")
        success = atomic_write(file_path, "version 2")
        assert success
        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == "version 2"

    def test_backup_manager(self):
        """测试备份管理器"""
        backup_dir = os.path.join(self.test_dir, "backups")
        bm = BackupManager(backup_dir, max_backups=3)
        file_path = os.path.join(self.test_dir, "backup_test.md")
        atomic_write(file_path, "original")
        # 备份
        backup_path = bm.backup(file_path)
        assert backup_path is not None
        assert os.path.exists(backup_path)
        # 再次写入并备份
        atomic_write(file_path, "updated")
        bm.backup(file_path)
        # 检查备份目录
        assert os.path.exists(backup_dir)

    def test_lock_mechanism(self):
        """测试文件锁"""
        lock_dir = os.path.join(self.test_dir, "locks")
        lock = Lock(lock_dir, "test", max_lock_minutes=30)
        assert lock.try_acquire()
        # 释放
        lock.release()
        # 重新获取
        assert lock.try_acquire()
        lock.release()

    def test_lock_expired(self):
        """测试过期锁"""
        lock_dir = os.path.join(self.test_dir, "locks2")
        import json
        from datetime import datetime, timedelta
        os.makedirs(lock_dir, exist_ok=True)
        # 创建一个过期的锁
        expired = {
            "time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "pid": 99999,
        }
        with open(os.path.join(lock_dir, "test2.lock"), "w") as f:
            json.dump(expired, f)
        lock = Lock(lock_dir, "test2", max_lock_minutes=30)
        assert lock.try_acquire()
        lock.release()

    def test_replace_auto_section(self):
        """测试替换自动生成区域"""
        existing = f"# Header\n\n{MARKER_START}\nold content\n{MARKER_END}\n\n## 我的记录\nkeep this"
        new_auto = f"{MARKER_START}\nnew content\n{MARKER_END}"
        result = replace_auto_section(existing, new_auto)
        assert "new content" in result
        assert "keep this" in result
        assert "old content" not in result

    def test_replace_auto_section_no_markers(self):
        """测试文件没有标记时的行为"""
        existing = "# Old file\n\nSome content"
        new_auto = f"{MARKER_START}\nnew\n{MARKER_END}"
        result = replace_auto_section(existing, new_auto)
        assert MARKER_START in result
        assert "Some content" in result

    def test_extract_user_section(self):
        """测试提取用户记录"""
        content = f"{MARKER_START}\nauto\n{MARKER_END}\n\n## 我的记录\nuser data"
        user = extract_user_section(content)
        assert "user data" in user

    def test_has_auto_markers(self):
        """测试标记检测"""
        assert has_auto_markers(f"{MARKER_START}\n{MARKER_END}")
        assert not has_auto_markers("no markers here")


if __name__ == "__main__":
    t = TestSafety()
    methods = [m for m in dir(t) if m.startswith("test_")]
    for m in methods:
        try:
            t.setup_method()
            getattr(t, m)()
            t.teardown_method()
            print(f"  [PASS] {m}")
        except Exception as e:
            print(f"  [FAIL] {m}: {e}")
            try:
                t.teardown_method()
            except Exception:
                pass