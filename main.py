import re
import os
from bs4 import BeautifulSoup
from datetime import datetime

# 基础路径和目录
base_dir = 'C:\\Users\\Downloads\\Telegram Desktop\\ChatExport_2025-06-04'
base_filename = 'messages'

# 获取当前时间作为生成时间（HKT 与 UTC+08:00 相同）
generation_time = datetime.now().strftime('%Y.%m.%d %H:%M:%S UTC+08:00')

# 动态遍历文件
html_files = []
i = 1
while True:
    if i == 1:
        file_path = os.path.join(base_dir, f'{base_filename}.html')
    else:
        file_path = os.path.join(base_dir, f'{base_filename}{i}.html')

    if os.path.exists(file_path):
        html_files.append(file_path)
        i += 1
    else:
        break

# 提取第一个 text bold 作为标题
with open(html_files[0], 'r', encoding='utf-8') as file:
    content = file.read()
soup = BeautifulSoup(content, 'html.parser')
text_bold_tag = soup.find('div', class_=['text', 'bold'])
title_text = text_bold_tag.text.strip() if text_bold_tag else "未找到标题文本"

# 用户交互：获取 emoji 总数量阈值，默认值为 15
while True:
    user_input = input("请输入 emoji 总数量的阈值（例如 ≥ 15 或 20，默认 15）：").strip()
    if user_input == "":
        user_threshold = 15  # 默认值
        break
    try:
        user_threshold = int(user_input)
        if user_threshold < 0:
            print("请输入一个非负整数！")
            continue
        break
    except ValueError:
        print("请输入一个有效的整数！")

# 用户交互：获取时间范围，默认值为 N
use_custom_range = input("是否需要自定义时间范围？(Y/N，默认 N)：").strip().upper() or "N"
start_date = None
end_date = None

if use_custom_range == 'Y':
    while True:
        try:
            start_date_str = input("请输入起始日期 (格式: YYYY-MM-DD，例如 2025-05-28)：")
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            break
        except ValueError:
            print("日期格式错误，请使用 YYYY-MM-DD 格式！")

    while True:
        try:
            end_date_str = input("请输入结束日期 (格式: YYYY-MM-DD，例如 2025-05-28)：")
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if end_date < start_date:
                print("结束日期不能早于起始日期！")
                continue
            break
        except ValueError:
            print("日期格式错误，请使用 YYYY-MM-DD 格式！")
else:
    all_times = []
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as file:
            content = file.read()
        time_matches = re.findall(
            r'<div class="pull_right date details" title="(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2} UTC\+08:00)"', content)
        for time_str in time_matches:
            dt = datetime.strptime(time_str, '%d.%m.%Y %H:%M:%S UTC+08:00')
            all_times.append(dt)
    start_date = min(all_times) if all_times else datetime.now()
    end_date = max(all_times) if all_times else datetime.now()

# 用户交互：是否保留媒体链接，默认值为 N
keep_media_input = input("是否保留媒体链接？(Y/N，默认 N)：").strip().upper() or "N"
keep_media = keep_media_input == 'Y'

# 用户交互：是否排除特定标签内容，默认值为 n
exclude_tags_input = input("请输入排除标签（默认不排除，用英文逗号分隔，例如 #music, #star）：").strip().lower() or "n"
exclude_tags = []
if exclude_tags_input != "n":
    exclude_tags = [tag.strip() for tag in exclude_tags_input.split(',') if tag.strip()]

# 统计总信息数量（仅包含有时间戳的消息）
total_messages = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    message_blocks = soup.find_all('div', class_=re.compile(r'message'))
    for block in message_blocks:
        time_tag = block.find('div', class_=['pull_right', 'date', 'details'])
        if time_tag and time_tag.get('title') and re.match(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2} UTC\+08:00',
                                                           time_tag['title']):
            total_messages += 1

# 提取内容块，同时记录 emoji 总数量
all_filtered_matches = []
message_ids = []
message_times = []
emoji_counts = []
media_hints = []
tooltip_contents = []
skipped_due_to_time = 0
skipped_due_to_no_time = 0
skipped_due_to_tags = 0
merged_messages = 0  # 记录合并的消息数量

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # 移除分页链接（"Next messages"）
    content = re.sub(r'<a class="pagination block_link" href="messages\d*\.html">\s*Next messages\s*</a>', '', content, flags=re.DOTALL)

    message_pattern = r'<div class="message[^>]*>'
    message_blocks = list(re.finditer(message_pattern, content))

    filtered_matches = []
    current_ids = []
    current_times = []
    current_emoji_counts = []
    current_media_hints = []
    current_tooltip_contents = []

    i = 0
    while i < len(message_blocks):
        start_pos = message_blocks[i].start()
        end_pos = message_blocks[i + 1].start() if i + 1 < len(message_blocks) else len(content)
        block_content = content[start_pos:end_pos]

        count_matches = re.findall(r'<span class="count">\s*(\d+)\s*</span>', block_content)
        total_count = sum(int(count) for count in count_matches) if count_matches else 0

        time_match = re.search(
            r'<div class="pull_right date details" title="(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2} UTC\+08:00)"',
            block_content)
        if time_match:
            full_time = time_match.group(1)
            dt = datetime.strptime(full_time, '%d.%m.%Y %H:%M:%S UTC+08:00')
            formatted_time = dt.strftime('%Y.%m.%d %H:%M:%S UTC+08:00')
            if start_date <= dt <= end_date:
                if total_count >= user_threshold:
                    soup = BeautifulSoup(block_content, 'html.parser')
                    from_name_tag = soup.find('div', class_='from_name')
                    from_name = from_name_tag.text if from_name_tag else ""
                    from_name_cleaned = re.sub(r'\s*\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}\s*UTC\+08:00', '', from_name).strip()
                    from_name_cleaned = re.sub(r'\s*\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}', '', from_name_cleaned).strip()
                    title_cleaned = title_text.strip()

                    # 判断是否为原博主：检查类名或名称匹配
                    message_div = soup.find('div', class_=re.compile(r'message default clearfix joined'))
                    is_original_poster = (message_div is not None) or (from_name_cleaned == title_cleaned)

                    # 如果是原博主且有排除标签，检查标签
                    if is_original_poster and exclude_tags:
                        text_div = soup.find('div', class_='text')
                        if text_div:
                            tags = text_div.find_all('a', href="", onclick=re.compile(r'return ShowHashtag\("([^"]+)"\)'))
                            message_tags = []
                            for tag in tags:
                                onclick_parts = tag['onclick'].split('"')
                                if len(onclick_parts) > 1:
                                    message_tags.append(f"#{onclick_parts[1]}")
                            if any(tag.lower() in [et.lower() for et in exclude_tags] for tag in message_tags):
                                skipped_due_to_tags += 1
                                i += 1
                                continue

                    message_id_match = re.search(r'id="message(\d+)"', block_content)
                    message_id = message_id_match.group(1) if message_id_match else "未知"
                    current_ids.append(message_id)
                    current_times.append(formatted_time)
                    current_emoji_counts.append(total_count)

                    soup = BeautifulSoup(block_content, 'html.parser')
                    text_elements = soup.find_all('div', class_='text')
                    text_content = text_elements[-1].text.strip() if text_elements else ""

                    forwarded_time = None
                    forwarded_time_elem = soup.find('span', class_='date details')
                    if forwarded_time_elem and forwarded_time_elem.get('title'):
                        forwarded_full_time = forwarded_time_elem['title']
                        forwarded_dt = datetime.strptime(forwarded_full_time, '%d.%m.%Y %H:%M:%S UTC+08:00')
                        forwarded_time = forwarded_dt.strftime('%Y.%m.%d %H:%M:%S UTC+08:00')

                    reply_to = soup.find('div', class_='reply_to details')
                    if reply_to:
                        link = reply_to.find('a', href=re.compile(r'#go_to_message\d+'))
                        if link and link.get('onclick'):
                            message_id_in_href = re.search(r'#go_to_message(\d+)', link['href']).group(1)
                            message_id_in_onclick = re.search(r'GoToMessage\((\d+)\)', link['onclick']).group(1)
                            if message_id_in_href != message_id_in_onclick:
                                link['onclick'] = f"return GoToMessage({message_id_in_href})"
                            new_link_text = f'this message {message_id_in_href}'
                            link.string = new_link_text
                            block_content = str(soup)

                    # 处理 bot_buttons_table 按钮，转换为纯文本
                    soup_buttons = BeautifulSoup(block_content, 'html.parser')
                    bot_buttons_table = soup_buttons.find('table', class_='bot_buttons_table')
                    buttons_text = ""
                    if bot_buttons_table:
                        buttons = bot_buttons_table.find_all('div', class_='bot_button')
                        button_items = []
                        for button in buttons:
                            div = button.find('div')
                            if div and div.text:
                                button_items.append(div.text.strip())
                        if button_items:
                            buttons_text = " 丨 ".join(button_items)
                        bot_buttons_table.decompose()
                        block_content = str(soup_buttons)

                    # 为隐藏媒体时收集所有媒体内容
                    all_media_blocks_html = []
                    media_elements = soup.find_all(['div', 'a', 'img'], class_=re.compile(
                        r'(media_audio_file|media_voice_message|media_file|photo_wrap|video_file_wrap|media_video|media_photo|animated_wrap|sticker_wrap)'))
                    all_media_blocks_html.extend([str(elem) for elem in media_elements])

                    # 合并连续的纯图片消息，仅收集后续消息的图片
                    media_blocks_html = []  # 用于 keep_media=True 时追加的图片
                    j = i + 1
                    while j < len(message_blocks):
                        next_start_pos = message_blocks[j].start()
                        next_end_pos = message_blocks[j + 1].start() if j + 1 < len(message_blocks) else len(content)
                        next_block_content = content[next_start_pos:next_end_pos]

                        next_time_match = re.search(
                            r'<div class="pull_right date details" title="(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2} UTC\+08:00)"',
                            next_block_content)
                        if not next_time_match:
                            break
                        next_dt = datetime.strptime(next_time_match.group(1), '%d.%m.%Y %H:%M:%S UTC+08:00')
                        if (next_dt - dt).total_seconds() > 3:
                            break

                        next_soup = BeautifulSoup(next_block_content, 'html.parser')
                        has_text_div = next_soup.find('div', class_='text')
                        has_text_content = has_text_div and has_text_div.get_text(strip=True)
                        media_wrap = next_soup.find('div', class_='media_wrap')

                        if has_text_content or not media_wrap:
                            break

                        is_purely_images = True
                        if media_wrap:
                            children_media = media_wrap.find_all(['a', 'div'], class_=re.compile(r'(photo_wrap|media_photo)'), recursive=False)
                            all_children = media_wrap.find_all(recursive=False)
                            if not children_media or len(children_media) != len(all_children):
                                is_purely_images = False
                        else:
                            is_purely_images = False
                        if not is_purely_images:
                            break

                        next_media_elements = next_soup.find_all(['div', 'a', 'img'], class_=re.compile(r'(photo_wrap|media_photo)'))
                        media_blocks_html.extend([str(elem) for elem in next_media_elements])
                        all_media_blocks_html.extend([str(elem) for elem in next_media_elements])

                        merged_messages += 1
                        j += 1

                    media_hint = ""
                    tooltip_content = ""
                    media_link = ""
                    tooltip_id = f"media_tooltip_{message_id}" if message_id_match else f"media_tooltip_{i}"
                    if not keep_media and all_media_blocks_html:
                        audio_contents, voice_contents, file_contents, photo_contents, video_contents = [], [], [], [], []
                        sticker_contents, gif_contents, animated_sticker_contents = [], [], []
                        counts = {'audio': 0, 'voice': 0, 'file': 0, 'photo': 0, 'video': 0, 'sticker': 0, 'gif': 0, 'animated_sticker': 0}

                        for media_item_html in all_media_blocks_html:
                            def fix_path(match_obj): return f'{match_obj.group(1)}../{match_obj.group(2)}/{match_obj.group(3)}'
                            current_media_item_html = re.sub(r'(src="|href=")(photos|video_files|audio_files|voice_messages|files|stickers)/([^"]+)',
                                                            fix_path, media_item_html)
                            if not media_link and (first_link_match := re.search(r'(?:src|href)="([^"]*)"', current_media_item_html)):
                                media_link = first_link_match.group(1)

                            if 'sticker_wrap' in current_media_item_html:
                                if '.tgs' in current_media_item_html: counts['animated_sticker'] += 1; animated_sticker_contents.append(current_media_item_html)
                                else: counts['sticker'] += 1; sticker_contents.append(current_media_item_html)
                            elif 'animated_wrap' in current_media_item_html or '.gif' in current_media_item_html.lower():
                                counts['gif'] +=1; gif_contents.append(current_media_item_html)
                            elif 'photo_wrap' in current_media_item_html or 'media_photo' in current_media_item_html:
                                counts['photo'] += 1; photo_contents.append(current_media_item_html)
                            elif 'video_file_wrap' in current_media_item_html or 'media_video' in current_media_item_html:
                                counts['video'] += 1; video_contents.append(current_media_item_html)
                            elif 'media_audio_file' in current_media_item_html:
                                counts['audio'] += 1; audio_contents.append(current_media_item_html)
                            elif 'media_voice_message' in current_media_item_html:
                                counts['voice'] += 1; voice_contents.append(current_media_item_html)
                            elif 'media_file' in current_media_item_html:
                                counts['file'] += 1; file_contents.append(current_media_item_html)

                        tooltip_html_parts = []
                        if counts['audio'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>音频文件 ({counts["audio"]})</h4>{"".join(audio_contents)}</div>')
                        if counts['voice'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>语音消息 ({counts["voice"]})</h4>{"".join(voice_contents)}</div>')
                        if counts['file'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>文件 ({counts["file"]})</h4>{"".join(file_contents)}</div>')
                        if counts['photo'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>图片 ({counts["photo"]})</h4>{"".join(photo_contents)}</div>')
                        if counts['video'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>视频 ({counts["video"]})</h4>{"".join(video_contents)}</div>')
                        if counts['sticker'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>静态贴纸 ({counts["sticker"]})</h4>{"".join(sticker_contents)}</div>')
                        if counts['animated_sticker'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>动画贴纸 ({counts["animated_sticker"]})</h4>{"".join(animated_sticker_contents)}</div>')
                        if counts['gif'] > 0: tooltip_html_parts.append(f'<div class="tooltip-section"><h4>GIF ({counts["gif"]})</h4>{"".join(gif_contents)}</div>')

                        hint_summary_parts = []
                        if counts.get('photo', 0) > 0: hint_summary_parts.append(f"{counts['photo']} 张图片")
                        if counts.get('video', 0) > 0: hint_summary_parts.append(f"{counts['video']} 个视频")
                        if counts.get('gif', 0) > 0: hint_summary_parts.append(f"{counts['gif']} 个 GIF")

                        if not hint_summary_parts:
                            other_media_types = []
                            if counts.get('audio', 0) > 0: other_media_types.append(f"{counts['audio']} 个音频")
                            if counts.get('voice', 0) > 0: other_media_types.append(f"{counts['voice']} 条语音")
                            if counts.get('file', 0) > 0: other_media_types.append(f"{counts['file']} 个文件")
                            if counts.get('sticker', 0) > 0: other_media_types.append(f"{counts['sticker']} 张静态贴纸")
                            if counts.get('animated_sticker', 0) > 0: other_media_types.append(f"{counts['animated_sticker']} 张动画贴纸")
                            if other_media_types:
                                hint_summary_parts.extend(other_media_types)
                            elif sum(counts.values()) > 0:
                                hint_summary_parts.append(f"{sum(counts.values())} 个媒体项")

                        if hint_summary_parts:
                            hint_summary = "、".join(hint_summary_parts)
                            media_hint = (
                                f'<div class="media-hint" id="hint_{tooltip_id}" '
                                f'onmouseenter="showMediaTooltip(this, \'{tooltip_id}\')" '
                                f'onmouseleave="hideMediaTooltip(\'{tooltip_id}\')">'
                                f'<a href="{media_link if media_link else "#"}" target="_blank" onclick="event.stopPropagation()">'
                                f'此处隐藏了 {hint_summary}，鼠标悬停查看</a></div>'
                            )
                            tooltip_content = f'<div class="media-tooltip" id="{tooltip_id}">{"".join(tooltip_html_parts)}</div>'

                    if keep_media and media_blocks_html:
                        soup_with_media = BeautifulSoup(block_content, 'html.parser')
                        media_wrap = soup_with_media.find('div', class_='media_wrap')
                        if media_wrap:
                            for media_item in media_blocks_html:
                                media_soup = BeautifulSoup(media_item, 'html.parser')
                                media_element = media_soup.find(['a', 'div', 'img'], class_=re.compile(r'(photo_wrap|media_photo)'))
                                if media_element:
                                    media_wrap.append(media_element)
                        block_content = str(soup_with_media)

                    block_content = re.sub(r'<div class="pull_right date details"[^>]*>.*?</div>', '', block_content,
                                           flags=re.DOTALL)

                    from_name_pattern = r'<div class="from_name">(.*?)</div>'
                    from_names = re.findall(from_name_pattern, block_content, re.DOTALL)
                    filtered_block_content = block_content
                    for from_name in from_names:
                        from_name_cleaned = re.sub(r'<[^>]+>', '', from_name).strip()
                        from_name_cleaned = re.sub(r'\s*\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}\s*UTC\+08:00', '',
                                                   from_name_cleaned).strip()
                        from_name_cleaned = re.sub(r'\s*\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}', '',
                                                   from_name_cleaned).strip()
                        title_cleaned = title_text.strip()
                        if from_name_cleaned == title_cleaned:
                            filtered_block_content = re.sub(
                                r'<div class="from_name">\s*' + re.escape(from_name) + r'\s*</div>',
                                '',
                                filtered_block_content,
                                flags=re.DOTALL
                            )
                        else:
                            time_to_use = forwarded_time if forwarded_time else formatted_time
                            new_from_name = f'🔁 {from_name_cleaned} {time_to_use}'
                            filtered_block_content = re.sub(
                                r'<div class="from_name">\s*' + re.escape(from_name) + r'\s*</div>',
                                f'<div class="from_name">{new_from_name}</div>',
                                filtered_block_content,
                                flags=re.DOTALL
                            )

                    paragraph = filtered_block_content
                    paragraph = re.sub(r'<div class="initials" style="line-height: 42px">.*?</div>', '', paragraph,
                                       flags=re.DOTALL)
                    paragraph = re.sub(r'<div class="pull_left userpic_wrap">.*?</div>', '', paragraph, flags=re.DOTALL)
                    paragraph = re.sub(r'<div class="pull_left forwarded userpic_wrap">.*?</div>', '', paragraph,
                                       flags=re.DOTALL)
                    paragraph = re.sub(r'<div class="signature details">.*?</div>', '', paragraph, flags=re.DOTALL)
                    paragraph = re.sub(r'\n+', '', paragraph)

                    if keep_media:
                        paragraph = re.sub(
                            r'href="\s*(photos|video_files|audio_files|voice_messages|files|stickers)/([^"]+)"',
                            r'href="../\1/\2"',
                            paragraph
                        )
                        paragraph = re.sub(
                            r'src="\s*(photos|video_files|audio_files|voice_messages|files|stickers)/([^"]+)"',
                            r'src="../\1/\2"',
                            paragraph
                        )

                    if text_content and not re.search(r'<div class="text">', paragraph):
                        paragraph = re.sub(
                            r'</div>$',
                            f'<div class="text">{text_content}</div></div>',
                            paragraph,
                            flags=re.DOTALL
                        )

                    # 将按钮文本直接追加到 paragraph
                    if buttons_text:
                        paragraph = re.sub(
                            r'</div>$',
                            f'{buttons_text}</div>',
                            paragraph,
                            flags=re.DOTALL
                        )

                    if not keep_media and media_hint:
                        soup_no_media = BeautifulSoup(paragraph, 'html.parser')
                        for elem in soup_no_media.find_all(['div', 'a', 'img'], class_=re.compile(
                                r'(media_audio_file|media_voice_message|media_file|photo_wrap|video_file_wrap|media_video|media_photo|animated_wrap|sticker_wrap)')):
                            elem.decompose()
                        paragraph = str(soup_no_media)

                    filtered_matches.append(paragraph)
                    current_media_hints.append(media_hint)
                    current_tooltip_contents.append(tooltip_content)

                    i = j - 1  # 跳过已合并的消息

                else:
                    pass
            else:
                skipped_due_to_time += 1
        else:
            skipped_due_to_no_time += 1
        i += 1

    all_filtered_matches.extend(filtered_matches)
    message_ids.extend(current_ids)
    message_times.extend(current_times)
    emoji_counts.extend(current_emoji_counts)
    media_hints.extend(current_media_hints)
    tooltip_contents.extend(current_tooltip_contents)

unique_matches = all_filtered_matches
unique_message_ids = message_ids
unique_message_times = message_times
unique_media_hints = media_hints
unique_tooltip_contents = tooltip_contents

# 统计筛选后消息中的中文字数
chinese_count = 0
for match in unique_matches:
    soup = BeautifulSoup(match, 'html.parser')
    text_elements = soup.find_all('div', class_='text')
    for element in text_elements:
        text = element.get_text(strip=True)
        # 扩展中文字符范围，包括 CJK 扩展字符区
        chinese_chars = re.findall(r'[\u4e00-\u9fff\U00020000-\U0002A6DF\U0002A700-\U0002B738\U0002B740-\U0002B81D\U0002B820-\U0002CEA1\U0002CEB0-\U0002EBE0]', text)
        chinese_count += len(chinese_chars)

# extraction_rate = (len(unique_matches) / total_messages) * 100 if total_messages > 0 else 0
# extraction_rate = round(extraction_rate, 2)

effective_total_messages = total_messages - merged_messages
extraction_rate = (len(unique_matches) / effective_total_messages) * 100 if effective_total_messages > 0 else 0
extraction_rate = round(extraction_rate, 2)

html_content = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>Combined Filtered Messages</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0 auto;
            max-width: 800px;
            padding: 20px;
            background-color: #f9f9f9;
            color: #333;
        }
        .message-block {
            padding: 10px 0;
            margin-bottom: 0;
            width: 100%;
            box-sizing: border-box;
        }
        .message-block:nth-child(odd) {
            background-color: #fff;
        }
        .message-block:nth-child(even) {
            background-color: #f5f5f5;
        }
        .separator {
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
            display: block;
            width: 100%;
        }
        .from_name {
            font-size: 0.9em;
            color: #2c5282;
            margin-bottom: 5px;
            width: 100%;
            word-wrap: break-word;
        }
        .text {
            margin-bottom: 5px;
            font-weight: normal;
            width: 100%;
            word-wrap: break-word;
        }
        .text a {
            color: #1a73e8;
            text-decoration: none;
        }
        .text a:hover {
            text-decoration: underline;
        }
        .reactions {
            margin-top: 5px;
            font-size: 0.9em;
            color: #555;
        }
        .count {
            font-weight: bold;
            color: #2c3e50;
        }
        .emoji {
            margin-right: 5px;
        }
        .summary {
            background-color: #e9ecef;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            width: 100%;
            box-sizing: border-box;
        }
        .text.bold {
            font-weight: bold;
            font-size: 18px;
            margin: 0 0 10px 0;
        }
        .reply_to.details {
            font-size: 0.9em;
            color: #2c5282;
            margin-bottom: 5px;
        }
        .reply_to.details a {
            color: #1a73e8;
            text-decoration: none;
        }
        .reply_to.details a:hover {
            text-decoration: underline;
        }
        .media-container {
            position: relative;
            display: inline-block;
            margin-top: 5px;
        }
        .media-hint {
            font-size: 0.9em;
            color: #007bff;
            font-style: italic;
            cursor: pointer;
            display: inline-block;
            padding: 3px 0;
            margin-bottom: 5px;
        }
        .media-hint a {
            color: #007bff;
            text-decoration: underline;
        }
        .media-hint a:hover {
            color: #0056b3;
            text-decoration: underline;
        }
        .media-tooltip {
            display: none;
            position: fixed;
            background-color: #ffffff;
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 15px;
            z-index: 1000;
            max-width: 600px;
            max-height: 600px;
            overflow-y: auto;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            line-height: 1.4;
        }
        .media-tooltip::-webkit-scrollbar { width: 10px; }
        .media-tooltip::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
        .media-tooltip::-webkit-scrollbar-thumb { background: #aaa; border-radius: 10px; }
        .media-tooltip::-webkit-scrollbar-thumb:hover { background: #888; }
        .tooltip-section {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .tooltip-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .tooltip-section h4 { margin-top: 0; margin-bottom: 8px; color: #333; font-size: 1.1em; }
        .tooltip-section img,
        .tooltip-section video {
            max-width: 100%; height: auto; display: block; margin: 0 auto 10px auto;
            object-fit: contain; max-height: 480px; border-radius: 4px; background-color: #f0f0f0;
        }
        .tooltip-section a { color: #007bff; }

        @media print {
            @page { 
                margin: 0.6cm; /* 增加边距，防止内容被裁剪 */
                size: A4;
            }
            body {
                background-color: #fff;
                margin: 0;
                padding: 0; /* 移除多余内边距 */
                font-size: 10pt;
                line-height: 1.4;
                color: #000;
                width: auto; /* 移除宽度限制，适应 A4 */
                max-width: none;
                font-family: 'Arial', 'Noto Serif CJK SC', sans-serif;
                orphans: 2;
                widows: 2;
            }
            .message-block {
                padding: 5px 0;
                margin-bottom: 0;
                font-size: 10pt;
                width: 100%;
                page-break-inside: auto;
                break-inside: auto;
                page-break-before: avoid;
            }
            .message-block:nth-child(odd) { background-color: #fff; }
            .message-block:nth-child(even) { background-color: #f5f5f5; }
            .separator { 
                color: #000; 
                font-weight: bold; 
                margin: 0; 
                font-size: 10pt; 
                page-break-inside: avoid; 
                break-inside: avoid; 
            }
            .from_name { 
                color: #000; 
                font-size: 0.8em; 
                width: 100%; 
                word-wrap: break-word; 
                page-break-inside: avoid; 
                break-inside: avoid; 
            }
            .text { 
                margin-bottom: 3px; 
                font-weight: normal; 
                font-size: 10pt; 
                width: 100%; 
                max-width: 100%; /* 确保内容不超过页面宽度 */
                line-break: strict;
                word-break: break-all; /* 强制换行 */
                overflow-wrap: anywhere; /* 兼容性换行 */
                overflow: hidden; /* 防止溢出 */
                page-break-inside: auto;
                break-inside: auto; 
                orphans: 2; 
                widows: 2; 
            }
            .text pre {
                white-space: pre-wrap; /* 保留换行和空格，但允许自动换行 */
                word-break: break-all; /* 强制在任意字符处换行 */
                overflow-wrap: anywhere; /* 允许在任意位置换行 */
                max-width: 100%; /* 限制宽度 */
                overflow: hidden; /* 防止溢出 */
                page-break-inside: auto;
                break-inside: auto;
            }
            .text.bold { 
                color: #000; 
                font-size: 12pt; 
                font-weight: bold !important; 
                page-break-inside: avoid; 
                break-inside: avoid; 
            }
            .count { 
                color: #000; 
                font-size: 10pt; 
                page-break-inside: avoid; 
                break-inside: avoid; 
            }
            .text a { 
                color: #1a73e8; 
                text-decoration: underline; 
            }
            .reactions { 
                color: #000; 
                font-size: 0.8em; 
                margin-top: 3px; 
                page-break-inside: avoid; 
                break-inside: avoid; 
            }
            .summary { 
                background-color: #fff; 
                padding: 5px; 
                margin-bottom: 10px; 
                font-size: 10pt; 
                width: 100%;
                max-width: 100%; /* 确保摘要部分不溢出 */
                page-break-inside: avoid; 
                break-inside: avoid; 
            }
            .media-hint {
                font-size: 0.8em;
                color: #555 !important;
                font-style: italic;
                margin-top: 3px;
                text-decoration: none !important;
                cursor: default;
                page-break-inside: avoid;
                break-inside: avoid;
            }
            .media-hint a { color: #555 !important; text-decoration: none !important; }
            .media-tooltip { display: none !important; }
            .reply_to.details {
                font-size: 0.8em;
                color: #000;
                page-break-inside: avoid;
                break-inside: avoid;
            }
            .reply_to.details a {
                color: #000;
                text-decoration: underline;
                text-decoration-color: #1a73e8 !important;
            }
        }
    </style>
    <script>
        let currentTooltipId = null;
        let tooltipHideTimeout = null;

        function showMediaTooltip(hintElement, tooltipId) {
            clearTimeout(tooltipHideTimeout);
            const tooltip = document.getElementById(tooltipId);
            if (!tooltip) return;

            if (currentTooltipId && currentTooltipId !== tooltipId) {
                const oldTooltip = document.getElementById(currentTooltipId);
                if (oldTooltip) oldTooltip.style.display = 'none';
            }
            const rect = hintElement.getBoundingClientRect();
            tooltip.style.display = 'block';
            const tooltipRect = tooltip.getBoundingClientRect();
            let top = rect.bottom + 5;
            let left = rect.left;
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;

            if (left + tooltipRect.width > viewportWidth - 10) left = viewportWidth - tooltipRect.width - 10;
            if (left < 10) left = 10;
            if (top + tooltipRect.height > viewportHeight - 10) {
                if (rect.top - tooltipRect.height - 5 > 10) top = rect.top - tooltipRect.height - 5;
                else top = Math.max(10, viewportHeight - tooltipRect.height - 10);
            }
            if (top < 10) top = 10;

            tooltip.style.position = 'fixed';
            tooltip.style.left = left + 'px';
            tooltip.style.top = top + 'px';
            currentTooltipId = tooltipId;
            tooltip.onmouseenter = function() { clearTimeout(tooltipHideTimeout); };
            tooltip.onmouseleave = function() {
                tooltipHideTimeout = setTimeout(() => {
                    tooltip.style.display = 'none';
                    if (currentTooltipId === tooltipId) currentTooltipId = null;
                }, 300);
            };
        }

        function hideMediaTooltip(tooltipId) {
            tooltipHideTimeout = setTimeout(() => {
                const tooltip = document.getElementById(tooltipId);
                if (tooltip && !tooltip.matches(':hover')) {
                     tooltip.style.display = 'none';
                     if (currentTooltipId === tooltipId) currentTooltipId = null;
                }
            }, 300);
        }

        function GoToMessage(messageId) {
            const element = document.getElementById('message' + messageId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
            return false;
        }
    </script>
</head>
<body>
"""

summary_content = '<div class="summary">\n'
summary_content += f'<div class="text bold">{title_text}</div>\n'

message_blocks_content = ""
for i, (match, msg_id, msg_time, media_hint, tooltip_content) in enumerate(
        zip(unique_matches, unique_message_ids, unique_message_times, unique_media_hints, unique_tooltip_contents), 1):
    separator = f'<div class="separator">--- 信息 {i} (message {msg_id}) [{msg_time}] ---</div>'
    message_block = f'<div class="message-block" id="message{msg_id}">{separator}'
    # 处理按钮
    soup_buttons = BeautifulSoup(match, 'html.parser')
    bot_buttons_table = soup_buttons.find('table', class_='bot_buttons_table')
    buttons_text = ""
    if bot_buttons_table:
        buttons = bot_buttons_table.find_all('div', class_='bot_button')
        button_items = []
        for button in buttons:
            div = button.find('div')
            if div and div.text:
                button_items.append(div.text.strip())
        if button_items:
            buttons_text = " 丨 ".join(button_items)
        bot_buttons_table.decompose()
        match = str(soup_buttons)
    if buttons_text:
        match = re.sub(r'</div>$', f'{buttons_text}</div>', match, flags=re.DOTALL)
    if media_hint:
        content = match.strip()
        message_block += f'{media_hint}{tooltip_content}{content}</div>'
    else:
        message_block += f'{match.strip()}</div>'
    message_blocks_content += message_block

def adjust_file_paths(content):
    file_path_pattern = r'file:///(.*?)/html/(.*?)(?:#go_to_message\d+)?'

    def replace_path(match):
        base_path = match.group(1)
        file_path = match.group(2)
        return f'file:///{base_path}/{file_path}'

    return re.sub(file_path_pattern, replace_path, content)

html_content = adjust_file_paths(html_content)
summary_content = adjust_file_paths(summary_content)
message_blocks_content = adjust_file_paths(message_blocks_content)

output_lines = []
output_lines.append(f"HTML 文件创建时间：{generation_time}")
output_lines.append(f"时间范围从 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
output_lines.append(f"HTML 文件中的总推送信息数量：{total_messages}")
output_lines.append(f"根据设置，媒体内容已{'被隐藏（可悬停查看）' if not keep_media else '保留'}")
if exclude_tags and skipped_due_to_tags > 0:
    output_lines.append(f"根据设置，因排除标签 {', '.join(exclude_tags)}，跳过消息数量：{skipped_due_to_tags}")
if merged_messages > 0:
    output_lines.append(f"合并了 {merged_messages} 条纯图片消息到主消息中")
output_lines.append(f"筛选总 emoji 数量大于等于 {user_threshold} 的推送信息")
output_lines.append(f"按条件提取信息的数量：{len(unique_matches)}, 提取率：{extraction_rate}%")
output_lines.append(f"输出范围内的中文字数约：{chinese_count}")

summary_content += '\n'.join(output_lines)
summary_content += '\n</div>\n'

html_content += summary_content
html_content += message_blocks_content
html_content += """
</body>
</html>
"""

output_dir = os.path.join(base_dir, 'html')
os.makedirs(output_dir, exist_ok=True)

generation_time_dt = datetime.strptime(generation_time, '%Y.%m.%d %H:%M:%S UTC+08:00')
output_filename = generation_time_dt.strftime('%Y%m%d%H%M%S') + '.html'
output_path = os.path.join(output_dir, output_filename)

with open(output_path, 'w', encoding='utf-8') as output:
    output.write(html_content)

for line in output_lines:
    print(line)
print(f"\n结果已保存到: {output_path}")

# Current version: V1.83.55
