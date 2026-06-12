"""
obsidian-shibao-bot 主入口
"""

import os
import sys
import traceback
from datetime import datetime
from typing import Optional

from src.logger import init_logger, get_logger, close_logger
from src.config import Config
from src.fetch_rss import RSSFetcher
from src.normalize_items import SeenManager, normalize_items
from src.rank_news import NewsRanker
from src.summarize_rules import generate_summary, generate_useful_tips, generate_english_sentence
from src.render_markdown import render_daily_markdown
from src.render_email import render_email_html
from src.email_sender import EmailSender
from src.write_obsidian import ObsidianWriter
from src.safety import Lock, resolve_vault_root
from src.utils import get_today_str, get_now_local


class ShibaoBot:
    """时报机器人主控类"""

    def __init__(self, project_dir: str, config_path: str):
        self.project_dir = project_dir
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.logger: Optional = None
        self.lock: Optional[Lock] = None
        self.writer: Optional[ObsidianWriter] = None
        self.today_str: str = ""
        self.now_local: datetime = None

    def run(self) -> int:
        """运行主流程，返回退出码 (0=成功, 1=可恢复错误, 2=严重错误)"""
        try:
            return self._run_internal()
        except SystemExit as e:
            return e.code
        except Exception as e:
            try:
                get_logger().critical(f"未预期错误: {e}\n{traceback.format_exc()}")
            except Exception:
                pass
            return 2

    def _run_internal(self) -> int:
        # 1. 初始化
        self.today_str = get_today_str()
        self.now_local = get_now_local()
        log_dir = os.path.join(self.project_dir, "logs")
        init_logger(log_dir)
        self.logger = get_logger()

        self.logger.info("=" * 50)
        self.logger.info(f"时报机器人开始运行 - {self.today_str}")
        self.logger.info(f"配置文件: {self.config_path}")
        self.logger.info("=" * 50)

        # 2. 加载配置
        self.config = Config(self.config_path)
        vault_path = self.config.vault_path
        root_folder = self.config.root_folder
        self.logger.info(f"vault_path: {vault_path}")
        self.logger.info(f"root_folder: {root_folder}")

        # 3. 读取运行模式
        mode = os.environ.get("SHIBAO_MODE", "obsidian")
        self.run_mode = mode

        # 4. 检查 vault_path（仅 obsidian 模式需要）
        if mode == "obsidian":
            if not vault_path or vault_path == "OBSIDIAN_VAULT_PATH":
                self.logger.error(
                    "vault_path 未设置。请修改 config.yaml 中的 vault_path 为你的 Obsidian 仓库路径。"
                )
                return 1

            if not os.path.exists(vault_path):
                self.logger.error(
                    f"vault_path 不存在: {vault_path}\n"
                    "请检查 iCloud Drive 是否已同步到本机。"
                )
                return 1

            # 验证目标路径
            try:
                resolve_vault_root(vault_path, root_folder)
            except Exception as e:
                self.logger.error(f"路径检查失败: {e}")
                return 1
        else:
            self.logger.info("email 模式，跳过 Obsidian 仓库检查")

        # 5. 初始化写入器
        self.writer = ObsidianWriter(self.config, self.project_dir)

        # 6. 获取锁
        lock = Lock(
            os.path.join(self.project_dir, "state"),
            "shibao",
            self.config.safe_write_config.get("max_lock_minutes", 30),
        )
        if not lock.try_acquire():
            self.logger.warning("无法获取锁，可能另有进程在运行，退出。")
            return 1
        self.lock = lock

        try:
            return self._do_work(mode=mode)
        finally:
            if self.lock:
                self.lock.release()
                self.lock = None
            close_logger()

    def _do_work(self, mode: str = "obsidian") -> int:
        logger = self.logger
        config = self.config

        # 7. 获取 RSS 源列表
        rss_sources = config.rss_sources
        total_sources = sum(len(urls) for urls in rss_sources.values())
        logger.info(f"RSS 源数量: {total_sources}")

        # 8. 创建首页（如果不存在）
        if self.writer:
            self.writer.create_index_if_not_exists()

        # 9. 抓取 RSS
        fetcher = RSSFetcher()
        raw_items = fetcher.fetch_all(rss_sources)

        failed_sources = fetcher.get_error_summary()
        for err in failed_sources:
            logger.warning(f"RSS 源失败: {err}")

        total_fetched = sum(len(items) for items in raw_items.values())
        logger.info(f"成功抓取: {total_fetched} 条")

        # 10. 去重
        seen_manager = SeenManager(os.path.join(self.project_dir, "state"))
        normalized = normalize_items(raw_items, seen_manager, config.timezone)

        total_after_dedup = sum(len(items) for items in normalized.values())
        logger.info(f"去重后: {total_after_dedup} 条")

        # 11. 排序
        category_priority = {c["name"]: c["priority"] for c in config.categories}
        ranker = NewsRanker(config.important_keywords, category_priority)
        ranked_items = ranker.rank_items(normalized)

        # 12. 应用限制
        limited = NewsRanker.apply_limits(
            ranked_items,
            config.max_items_per_category,
            config.max_items_per_day,
        )

        limited_ranked = []
        for cat_items in limited.values():
            limited_ranked.extend(cat_items)
        limited_ranked.sort(key=lambda x: x.get("_score", 0), reverse=True)

        has_content = len(limited_ranked) > 0
        logger.info(f"最终保留: {len(limited_ranked)} 条")

        # 13. 生成摘要
        summaries = generate_summary(limited_ranked, config.summary_top_n, config.important_keywords)
        useful_tips = generate_useful_tips(limited_ranked)
        english_sentence = generate_english_sentence(limited_ranked)

        # 14. 渲染 Markdown
        md_content = render_daily_markdown(
            today_str=self.today_str,
            now_local=self.now_local,
            summaries=summaries,
            ranked_items=limited_ranked,
            grouped_items=limited,
            useful_tips=useful_tips,
            english_sentence=english_sentence,
            has_content=has_content,
            timezone=config.timezone,
        )

        # 15. 写入文件
        if self.writer:
            success = self.writer.write_daily_file(md_content, self.today_str)
            if success:
                file_path = self.writer.get_today_file_path(self.today_str)
                logger.info(f"写入成功: {file_path}")
            else:
                logger.error("写入失败")
                return 1

        logger.info("=" * 50)
        logger.info(f"时报机器人运行完成 - {self.today_str}")
        logger.info("=" * 50)

        return 0


def main():
    """CLI 入口"""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_dir, "config.yaml")

    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        print("请确保已创建 config.yaml")
        return 1

    bot = ShibaoBot(project_dir, config_path)
    return bot.run()


if __name__ == "__main__":
    sys.exit(main())