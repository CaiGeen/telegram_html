# Telegram Channel Export Processor

## 简介

Telegram Channel Export Processor 是一个可自定义数据内容、重排版 Telegram 导出 HTML 数据的 Python 工具，信息密度提高 20% 以上。

以 [Reorx’s Forge](https://t.me/reorx_share) 频道为例，对比处理前后的效果。

处理前：


处理后：


它包含两个模块：
- **主模块**：筛选、合并和格式化聊天记录，生成易于阅读的 HTML 输出，生成易于阅读的 HTML，针对 PDF 打印优化，支持自定义时间范围、emoji 数量筛选、标签排除和媒体文件的显示 / 隐藏等。
- **数据分析子模块**：提取消息数据、超链接和原博主标签，输出到 Excel 文件，便于进一步分析。

该项目适用于需要整理回顾和分析 Telegram 频道或群组聊天记录的用户。

## 功能

### 主模块 (V1.00.0)
- **消息筛选**：
  - 根据用户指定的时间范围筛选消息。
  - 按 emoji 总数阈值（默认 ≥ 15）筛选消息。
  - 排除原博主消息中包含特定标签的内容（例如 `#music`）。
- **消息合并**：将连续的纯图片消息合并到主消息中，减少冗余。
- **媒体处理**：
  - 可选择隐藏媒体（图片、视频等），提供鼠标悬停查看功能。
  - 可选择保留媒体链接，直接显示在输出中。
- **输出**：
  - 生成格式化的 HTML 文件，包含筛选后的消息、摘要信息和提取率。
  - 提取率计算考虑合并的纯图片消息，确保准确性。
  - 支持打印友好的样式，适合导出 PDF。
- **统计**：输出消息总数、合并消息数、中文字数和提取率。

### 数据分析子模块 (V1.00.0)
- **消息提取**：
  - 提取每条消息的时间、用户名、消息编号、文本、emoji 总数和是否包含媒体。
- **超链接统计**：统计所有消息中的超链接（排除媒体文件链接），按出现次数排序。
- **标签统计**：仅统计原博主（频道主人）非转发消息中的标签，按出现次数排序。
- **输出**：生成 Excel 文件，包含三个工作表：
  - `Messages`：消息详细信息。
  - `Links`：超链接及其出现次数。
  - `Tags`：原博主非转发消息的标签及其出现次数。

## 文件结构
```
Telegram-Chat-Export-Processor/
├── main.py                # 主模块 (V1.00.0)
├── analysis.py            # 数据分析子模块 (V1.00.0)
├── README.md              # 项目说明文件
├── ChatExport_2025-06-04/ # Telegram 导出的聊天记录目录
│   ├── messages.html
│   ├── messages2.html
│   ├── photos/
│   ├── video_files/
│   ├── ...
├── html/                  # 主模块输出目录（自动创建）
│   ├── YYYYMMDDHHMMSS.html
├── analysis/              # 数据分析子模块输出目录（自动创建）
│   ├── analysis_YYYYMMDDHHMMSS.xlsx
```

## 使用说明

### 依赖
- Python 3.6+
- 所需库：
  ```bash
  pip install beautifulsoup4 pandas
  ```

### 准备工作
1. 从 Telegram 导出数据，保存到目录（例如 `ChatExport_2025-06-04`），包含 `messages*.html` 文件和媒体文件夹。
2. 更新代码中的 `base_dir` 为您的导出目录路径：
   ```python
   base_dir = 'C:\\path\\to\\your\\ChatExport_2025-06-04'
   ```

### 运行主模块
1. 运行 `main.py`：
   ```bash
   python main.py
   ```
2. 根据提示输入：
   - Emoji 总数阈值（默认 15）。
   - 是否自定义时间范围（Y/N，默认 N，使用全部消息时间范围）。
   - 是否保留媒体链接（Y/N，默认 N，隐藏媒体）。
   - 是否排除特定标签（默认不排除，输入标签如 `#music, #star`）。
3. 输出：
   - HTML 文件保存在 `html/YYYYMMDDHHMMSS.html`。
   - 终端和 HTML 文件开头显示摘要信息（消息总数、提取率等）。

### 运行数据分析子模块
1. 运行 `analysis.py`：
   ```bash
   python analysis.py
   ```
2. 输出：
   - Excel 文件保存在 `analysis/analysis_YYYYMMDDHHMMSS.xlsx`，包含 `Messages`、`Links` 和 `Tags` 工作表。

## 注意事项
- **输入文件**：确保 Telegram 导出的 HTML 文件格式正确，包含 `messages*.html` 和相关媒体文件夹。
- **标签统计**：仅统计原博主非转发消息的标签（`#tag_name` 格式）。
- **性能**：对于大型聊天记录，处理时间可能较长。
- **编码**：确保输入文件使用 UTF-8 编码，避免乱码。

## 版本信息
- 主模块：V1.00.0
- 数据分析子模块：V1.00.0

## 联系
如有问题或建议，请联系 [涂俊杰](https://mp.weixin.qq.com/s/d79_AdX4IF4v7Ho2_E84yw) 或提交 issue。
