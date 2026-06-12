"""
测试：Obsidian 写入模块
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.safety import MARKER_START, MARKER_END
from src.render_markdown import render_daily_markdown, render_index_md


class TestWriteObsidian:
    """写入模块测试"""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp(prefix="shibao_test_")
        self.vault_path = os.path.join(self.test_dir, "vault")
        self.root_folder = "时报"
        os.makedirs(self.vault_path)

        # Mock config-like dict
        self.config = type("Config", (), {
            "vault_path": self.vault_path,
            "root_folder": self.root_folder,
            "timezone": "Asia/Shanghai",
            "safe_write_config": {"max_backups_per_file": 5, "max_lock_minutes": 30},
        })

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_writer(self):
        from src.write_obsidian import ObsidianWriter
        return ObsidianWriter(self.config, self.test_dir)

    def test_create_daily_file(self):
        """测试创建日报文件"""
        writer = self._make_writer()
        os.makedirs(writer.resolved_root, exist_ok=True)
        
        content = f"{MARKER_START}\n# Test\n{MARKER_END}\n## 我的记录"
        success = writer.write_daily_file(content)
        assert success

        file_path = writer.get_today_file_path()
        assert os.path.exists(file_path)

    def test_preserve_user_section(self):
        """测试保留用户记录"""
        writer = self._make_writer()
        os.makedirs(writer.resolved_root, exist_ok=True)
        
        # 创建文件
        content = f"{MARKER_START}\n# Auto\n{MARKER_END}\n\n## 我的记录\n\n这是我的手动测试内容，不能被覆盖。"
        writer.write_daily_file(content)

        # 更新内容
        new_content = f"{MARKER_START}\n# Updated Auto\n{MARKER_END}"
        writer.write_daily_file(new_content)

        # 读取文件确认用户记录保留
        file_path = writer.get_today_file_path()
        with open(file_path, "r", encoding="utf-8") as f:
            result = f.read()
        assert "这是我的手动测试内容，不能被覆盖。" in result
        assert "# Updated Auto" in result

    def test_refresh_generated_header_when_preserving_user_section(self):
        """测试更新旧日报时刷新自动生成头部"""
        writer = self._make_writer()
        os.makedirs(writer.resolved_root, exist_ok=True)

        old_content = (
            "---\n"
            "updated: 2026-06-12 08:30\n"
            "---\n\n"
            "> 自动生成时间：2026-06-12 08:30\n\n"
            f"{MARKER_START}\n"
            "## 旧内容\n"
            f"{MARKER_END}\n\n"
            "---\n\n"
            "## 我的记录\n\n"
            "保留这段手写内容。"
        )
        writer.write_daily_file(old_content)

        new_content = (
            "---\n"
            "updated: 2026-06-12 22:30\n"
            "---\n\n"
            "> 自动生成时间：2026-06-12 22:30\n\n"
            f"{MARKER_START}\n"
            "## 新内容\n"
            f"{MARKER_END}\n\n"
            "---\n\n"
            "## 我的记录\n\n"
            "默认占位。"
        )
        writer.write_daily_file(new_content)

        file_path = writer.get_today_file_path()
        with open(file_path, "r", encoding="utf-8") as f:
            result = f.read()

        assert "updated: 2026-06-12 22:30" in result
        assert "自动生成时间：2026-06-12 22:30" in result
        assert "## 新内容" in result
        assert "保留这段手写内容。" in result
        assert "默认占位。" not in result

    def test_index_creation(self):
        """测试首页创建"""
        writer = self._make_writer()
        os.makedirs(writer.resolved_root, exist_ok=True)
        created = writer.create_index_if_not_exists()
        assert created

        # 第二次不应该重新创建
        created_again = writer.create_index_if_not_exists()
        assert not created_again

    def test_render_markdown_no_content(self):
        """测试无内容时的渲染"""
        from datetime import datetime
        md = render_daily_markdown(
            today_str="2026-06-12",
            now_local=datetime.now(),
            summaries=[],
            ranked_items=[],
            grouped_items={},
            useful_tips=[],
            english_sentence={},
            has_content=False,
        )
        assert MARKER_START in md
        assert MARKER_END in md
        assert "本次未获取到新内容" in md

    def test_render_markdown_with_content(self):
        """测试有内容时的渲染"""
        from datetime import datetime
        ranked = [
            {
                "title": "Test Item",
                "link": "http://example.com",
                "guid": "g1",
                "category": "科技与AI",
                "source_name": "Test Source",
                "summary": "This is a test summary for a tech news item about AI.",
                "published": datetime.now(),
                "_score": 100,
            }
        ]
        md = render_daily_markdown(
            today_str="2026-06-12",
            now_local=datetime.now(),
            summaries=[{
                "title": "Test Item",
                "link": "http://example.com",
                "source": "Test",
                "category": "科技与AI",
                "summary": "Summary here",
                "importance": "Test importance",
                "personal_value": "Test value",
            }],
            ranked_items=ranked,
            grouped_items={"科技与AI": ranked},
            useful_tips=[{"label": "AI学习", "tip": "Test tip"}],
            english_sentence={"chinese": "Test", "english": "Test", "structure": "Test", "template": "Test"},
            has_content=True,
        )
        assert MARKER_START in md
        assert MARKER_END in md
        assert "Test Item" in md


if __name__ == "__main__":
    t = TestWriteObsidian()
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
