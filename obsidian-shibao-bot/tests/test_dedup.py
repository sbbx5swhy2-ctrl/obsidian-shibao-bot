"""
测试：去重模块
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.normalize_items import SeenManager, normalize_items


class TestDedup:
    """去重测试"""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp(prefix="shibao_test_")

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_seen_manager_basic(self):
        """测试基本去重"""
        sm = SeenManager(self.test_dir)
        assert not sm.is_seen("url1", "guid1", "title1")
        sm.mark_seen("url1", "guid1", "title1")
        assert sm.is_seen("url1", "guid1", "title1")

    def test_seen_manager_url_dedup(self):
        """测试 URL 去重"""
        sm = SeenManager(self.test_dir)
        sm.mark_seen("http://example.com/1", "guid1", "Title 1")
        assert sm.is_seen("http://example.com/1", "guid-different", "Different Title")

    def test_seen_manager_guid_dedup(self):
        """测试 GUID 去重"""
        sm = SeenManager(self.test_dir)
        sm.mark_seen("url1", "the-guid", "Title 1")
        assert sm.is_seen("different-url", "the-guid", "Different Title")

    def test_seen_manager_title_hash_dedup(self):
        """测试标题 hash 去重"""
        sm = SeenManager(self.test_dir)
        sm.mark_seen("url1", "guid1", "重复标题")
        assert sm.is_seen("url2", "guid2", "重复标题")

    def test_seen_manager_persistence(self):
        """测试持久化"""
        sm = SeenManager(self.test_dir)
        sm.mark_seen("url-persist", "guid-persist", "Persist Title")
        
        sm2 = SeenManager(self.test_dir)
        assert sm2.is_seen("url-persist", "guid-persist", "Persist Title")

    def test_normalize_items_dedup(self):
        """测试 normalize_items 去重"""
        sm = SeenManager(self.test_dir)
        raw = {
            "科技与AI": [
                {"title": "Item 1", "link": "http://example.com/1", "guid": "g1", "category": "科技与AI"},
                {"title": "Item 2", "link": "http://example.com/2", "guid": "g2", "category": "科技与AI"},
                {"title": "Item 1 (dup)", "link": "http://example.com/1", "guid": "g1", "category": "科技与AI"},
            ]
        }
        result = normalize_items(raw, sm, "Asia/Shanghai")
        total = sum(len(items) for items in result.values())
        assert total == 2, f"期望 2 条，实际 {total}条"


if __name__ == "__main__":
    t = TestDedup()
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