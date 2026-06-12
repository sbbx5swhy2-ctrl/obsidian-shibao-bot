# obsidian-shibao-bot

日常信息自动化收集工具 —— 每天自动获取公开信息源中的重点信息，按日期写入 Obsidian 仓库的「时报」文件夹。

## 项目作用

- 自动抓取 RSS 信息源中的新闻、动态、趋势
- 按分类整理（科技与AI、设计与创意、财经商业 等）
- 生成适合 Obsidian 复习的 Markdown 文件
- 保护「我的记录」区域不被覆盖
- 支持 Windows 任务计划程序每天自动运行

## 目录结构

```
obsidian-shibao-bot/
├── config.yaml          # 配置文件（必须修改 vault_path）
├── requirements.txt     # Python 依赖
├── README.md            # 本文件
├── run_now.ps1          # 手动运行一次
├── install_task.ps1     # 安装每日自动任务
├── uninstall_task.ps1   # 卸载每日自动任务
├── open_today.ps1       # 打开今日日报文件
├── src/
│   ├── main.py                     # 主入口
│   ├── config.py                   # 配置加载
│   ├── fetch_rss.py                # RSS 抓取
│   ├── validate_sources.py         # RSS 源验证
│   ├── normalize_items.py          # 去重与规范化
│   ├── rank_news.py                # 排序
│   ├── summarize_rules.py          # 规则摘要
│   ├── render_markdown.py          # Markdown 渲染
│   ├── write_obsidian.py           # 安全写入 Obsidian
│   ├── safety.py                   # 安全机制（锁、备份、路径检查）
│   ├── logger.py                   # 日志
│   └── utils.py                    # 工具函数
├── state/
│   └── seen.json       # 已见条目记录（自动维护）
├── logs/               # 运行日志
├── backups/            # 文件备份（不是 Obsidian 仓库里）
└── tests/              # 测试
```

## 快速开始

### 1. 修改 config.yaml

用文本编辑器打开 `config.yaml`，找到第一行：

```yaml
vault_path: "OBSIDIAN_VAULT_PATH"
```

改为你的 Obsidian 仓库路径，例如：

```yaml
vault_path: "C:/iCloud/iCloudDrive/Obsidian/仓库"
```

> 注意：路径支持中文和空格，不要使用 Obsidian 仓库内的路径。

### 2. 安装依赖

```
pip install -r requirements.txt
```

### 3. 手动运行一次

右键点击 `run_now.ps1` -> 使用 PowerShell 运行。

或打开 PowerShell，进入项目目录后执行：

```
.un_now.ps1
```

首次运行会提示"未获取到新内容"，这是正常的——因为还没有配置 RSS 源。

### 4. 在 Obsidian 里查看

运行成功后，在 Obsidian 的「时报」文件夹中会出现 `YYYY/MM/YYYY-MM-DD.md` 文件。

## 如何添加 RSS 源

1. 打开 `config.yaml`
2. 找到 `rss_sources` 部分
3. 在对应的分类下添加 RSS 链接，例如：

```yaml
rss_sources:
  科技与AI:
    - "https://feeds.feedburner.com/TheVerge"
    - "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"
  设计与创意:
    - "https://www.behance.net/feeds/projects"
```

### 如何验证 RSS 源

用 `validate_sources.py` 脚本检查：

```
python -c "from src.validate_sources import validate_source; print(validate_source('你的RSS链接'))"
```

### RSS 源注意事项

- 只使用公开的 RSS feed
- 不要爬取需要登录、验证码或付费的网站
- 不要爬咸鱼、小红书、微信、知乎等平台
- 如果无法联网，不要编造 RSS 链接
- 如果 RSS 源失效，系统会自动跳过并记录日志，不会崩溃

## 自动运行

### 安装每日自动任务

右键点击 `install_task.ps1` -> 使用 PowerShell 运行。

任务计划程序会创建名为 `Obsidian Shibao Daily Update` 的任务，每天 08:30 自动运行。

### 修改运行时间

编辑 `config.yaml` 的 `daily_run_time` 字段，然后重新运行 `install_task.ps1`。

### 卸载自动任务

右键点击 `uninstall_task.ps1` -> 使用 PowerShell 运行。

注意：卸载不会删除任何已生成的日报文件。

## 修改分类

编辑 `config.yaml` 的 `categories` 部分：

```yaml
categories:
  - name: "科技与AI"
    priority: 10    # 优先级越高，排序越靠前
  - name: "设计与创意"
    priority: 9
```

优先级范围：0-10，建议保持至少 8 个分类不变。

## 日志

日志文件保存在 `logs/YYYY-MM-DD.log`。

每次运行记录：
- 开始/结束时间
- 配置文件路径
- RSS 源数量和状态
- 抓取、去重后的条目数
- 写入是否成功
- 错误信息

## 安全机制

### 为什么不要把项目代码放进 Obsidian 仓库

项目代码和 Obsidian 笔记应该分离。项目只需要在 Obsidian 仓库中写入「时报」文件夹，不应当和其他笔记混在一起。

### 为什么不能让脚本修改「时报」以外的文件

为了安全。脚本只应在指定范围内操作，避免意外修改、删除其他笔记。

### iCloud 同步注意事项

- 确保 Obsidian 仓库路径在 iCloud Drive 中已同步到本机
- 脚本不会频繁写入（每天只写一次）
- 不会批量扫描整个仓库
- 不会删除任何文件
- 使用安全写入（临时文件 + 原子替换 + 备份）
- 使用锁文件防止并发运行

### 如果 Dataview 不显示

「时报首页」使用了 Dataview 插件语法。如果首页没有显示表格：
1. 确认已安装 Dataview 社区插件
2. 确认插件已启用
3. 没有 Dataview 也不影响日报内容本身

### 如果当天文件没有更新

1. 检查 `logs/` 目录下的当天日志
2. 检查 config.yaml 的 vault_path 是否正确
3. 检查 RSS 源是否配置
4. 检查网络连接
5. 手动运行 `run_now.ps1` 查看输出

### 如果重复运行

系统内置了去重机制：
- 通过 URL、GUID、标题 hash 三重去重
- 结果保存在 `state/seen.json`
- 相同内容不会重复添加

### 「我的记录」区域保护

脚本只会替换 `<!-- AUTO-GENERATED-START -->` 到 `<!-- AUTO-GENERATED-END -->` 之间的内容。
在这两个标记之外的任何内容（包括「我的记录」区域）都不会被修改。

## Obsidian 插件建议

**建议开启的核心插件：**
- File explorer
- Search
- Tags
- Backlinks
- Outgoing links
- Daily notes
- Templates
- File recovery
- Bases

**建议安装的社区插件：**
- Dataview（用于首页表格展示）
- Calendar（日历视图）

**暂时不要安装的插件：**
- Git（iCloud 上使用 Git 容易冲突）
- Linter（自动改写 Markdown 可能覆盖手动内容）
- Auto Note Mover（自动整理可能干扰目录结构）
- 各种自动整理或同步插件

## 测试

运行单元测试：

```
cd obsidian-shibao-bot
python -m pytest tests/ -v
```

测试覆盖：
- 安全写入与路径检查
- 去重机制
- 用户内容保护
- Markdown 渲染
- 备份与恢复

## 问题排查

### 脚本报错 "vault_path 未设置"

修改 config.yaml 中的 vault_path。

### 脚本报错 "vault_path 不存在"

检查 iCloud Drive 是否已同步到本机，路径是否正确。

### 脚本报错 "路径越界"

检查 config.yaml 的 root_folder 配置，确保目标路径在 vault_path/root_folder 内。

### 脚本无法运行

1. 确认已安装 Python 3.8+
2. 确认已安装依赖：`pip install -r requirements.txt`
3. 确认工作目录为 obsidian-shibao-bot 目录