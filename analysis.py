import os
import re
import glob
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from collections import Counter

# 设置输入文件路径
base_dir = 'C:\\Users\\Downloads\\Telegram Desktop\\ChatExport_2025-06-04)'
html_files = glob.glob(os.path.join(base_dir, 'messages*.html'))

# 创建 analysis 文件夹
output_dir = os.path.join(base_dir, 'analysis')
os.makedirs(output_dir, exist_ok=True)

# 存储所有消息数据
all_messages = []

# 定义媒体类型
media_classes = [
    'media_audio_file', 'media_voice_message', 'media_file',
    'photo_wrap', 'video_file_wrap', 'media_video', 'media_photo',
    'animated_wrap', 'sticker_wrap'
]

# 提取频道主人 ID
with open(html_files[0], 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file, 'html.parser')
channel_owner_tag = soup.find('div', class_=['text', 'bold'])
channel_owner_id = channel_owner_tag.get_text(strip=True) if channel_owner_tag else 'Unknown'

# 存储超链接和标签的全局计数
all_links = []
all_tags = []

# 定义媒体文件扩展名
media_extensions = ('.mp3', '.wav', '.mp4', '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.tgs', '.webp')

# 遍历所有 messages*.html 文件
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # 提取消息数据
    for msg in soup.find_all('div', class_=re.compile(r'message')):
        # 放宽系统信息排除条件，仅当明确是系统消息时跳过
        body_details = msg.find('div', class_='body details')
        if body_details and not msg.find('div', class_='text') and not msg.find('a', href=True):
            continue

        # 提取时间戳
        time_tag = msg.find('div', class_=['pull_right', 'date', 'details'])
        if time_tag and 'title' in time_tag.attrs:
            time_str = time_tag['title']
            time = datetime.strptime(time_str, '%d.%m.%Y %H:%M:%S UTC+08:00')
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            continue

        # 提取博主 ID
        classes = msg.get('class', [])
        if 'joined' in classes:
            blogger_id = channel_owner_id
        else:
            forwarded_body = msg.find('div', class_='forwarded body')
            if forwarded_body:
                from_name = forwarded_body.find('div', class_='from_name')
                if from_name:
                    date_span = from_name.find('span', class_='date details')
                    if date_span:
                        date_span.decompose()
                    blogger_id = from_name.get_text(strip=True) or 'Unknown'
                else:
                    blogger_id = 'Unknown'
            else:
                from_name = msg.find('div', class_='from_name')
                if from_name:
                    link = from_name.find('a')
                    if link and 'href' in link.attrs:
                        blogger_id = link['href'].split('/')[-1]
                    else:
                        blogger_id = from_name.get_text(strip=True) or 'Unknown'
                else:
                    blogger_id = 'Unknown'

        # 提取消息 ID
        msg_id = msg.get('id', '')
        if msg_id.startswith('message'):
            try:
                message_id = abs(int(msg_id.replace('message', '')))
            except ValueError:
                message_id = 'Unknown'
        else:
            message_id = 'Unknown'

        # 提取文本内容
        text_tag = msg.find('div', class_='text')
        text = text_tag.get_text(strip=True) if text_tag else ''

        # 统计 emoji 数量
        emoji_counts = msg.find_all('span', class_='count')
        emoji_total = sum(int(count.get_text().strip()) for count in emoji_counts if count.get_text().strip().isdigit()) if emoji_counts else 0

        # 判断是否包含媒体
        has_media = '否'
        for media_class in media_classes:
            if msg.find(True, class_=re.compile(media_class)):
                has_media = '是'
                break

        # 提取超链接（排除特定头部和媒体文件）
        links = [a.get('href') for a in msg.find_all('a', href=True) if a.get('href') and (a.get('href').lower().startswith(('http://', 'https://')) or (not a.get('href').lower().startswith(('http://', 'https://')) and not any(a.get('href').lower().endswith(ext) for ext in media_extensions))) and not a.get('href').startswith(('files/', 'video_files/', 'tg://', '#'))]
        all_links.extend(links)

        # 提取原博主非转发消息的标签
        if blogger_id == channel_owner_id and not msg.find('div', class_='forwarded body'):
            if text_tag:
                tags = text_tag.find_all('a', href="", onclick=re.compile(r'return ShowHashtag\("([^"]+)"\)'))
                for tag in tags:
                    onclick_parts = tag['onclick'].split('"')
                    if len(onclick_parts) > 1:
                        all_tags.append(f"#{onclick_parts[1]}")

        # 存储消息数据
        all_messages.append({
            '时间': timestamp,
            '用户名': blogger_id,
            '消息编号': message_id,
            '消息文本': text,
            'emoji总数': emoji_total,
            '是否包含媒体': has_media
        })

# 转换为 DataFrame
df_messages = pd.DataFrame(all_messages)

# 统计超链接并按出现次数降序排列
link_counts = Counter(all_links)
link_data = [{'超链接': link, '出现次数': count} for link, count in link_counts.items()]
df_links = pd.DataFrame(link_data).sort_values(by='出现次数', ascending=False)

# 统计标签并按出现次数降序排列
tag_counts = Counter(all_tags)
tag_data = [{'标签': tag, '出现次数': count} for tag, count in tag_counts.items()]
df_tags = pd.DataFrame(tag_data).sort_values(by='出现次数', ascending=False)

# 生成文件名
current_time = datetime.now().strftime('%Y%m%d%H%M%S')
output_file = os.path.join(output_dir, f'analysis_{current_time}.xlsx')

# 导出到 Excel（多工作表）
with pd.ExcelWriter(output_file) as writer:
    df_messages.to_excel(writer, sheet_name='Messages', index=False)
    df_links.to_excel(writer, sheet_name='Links', index=False)
    df_tags.to_excel(writer, sheet_name='Tags', index=False)

print(f"\n结果已保存到: {output_path}")

# Current version: V1.27.3
