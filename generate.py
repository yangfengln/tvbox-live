"""
生成 tvbox / 影视仓 兼容的 TXT 直播源文件
同时输出 M3U 通用格式
"""

import logging
import os
import re
from datetime import datetime, timezone

from config import OUTPUT_DIR, OUTPUT_FILE, OUTPUT_ENCODING, MAX_SOURCES_PER_CHANNEL

logger = logging.getLogger(__name__)

M3U_FILE = "live.m3u"


def _is_chinese(s):
    """检查是否包含中文"""
    return bool(re.search(r'[一-鿿]', s))


def _clean_name(name):
    """清理名称，移除 emoji 和特殊字符但保留中文和常用符号"""
    # 先手动把常见分组映射成中文
    manual_map = {
        "☘️上海频道": "上海频道",
        "上海频道": "上海频道",
        "央视频道": "央视频道",
        "卫视频道": "卫视频道",
        "地方频道": "地方频道",
        "港澳频道": "港澳频道",
        "台湾频道": "台湾频道",
    }
    if name in manual_map:
        return manual_map[name]

    # 移除 emoji（保留中文、英文、数字、空格、-、()）
    cleaned = re.sub(r'[^\w一-鿿\s\-()（）]', '', name).strip()
    if not cleaned:
        cleaned = name.encode('ascii', errors='ignore').decode('ascii').strip()
    if not cleaned:
        cleaned = "未分类"
    return cleaned


def generate(channels):
    """生成 tvbox TXT 和 M3U 格式输出"""
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    txt_lines = []
    m3u_lines = ["#EXTM3U"]

    # 预处理：清理频道名和分组名，相同分组+频道名的源合并
    cleaned_channels = {}  # (group, name) -> [urls]

    for ch in channels:
        live_urls = [
            u[1] for u in ch["urls"] if isinstance(u, tuple) and u[0] == "live"
        ]
        if not live_urls:
            continue

        group = _clean_name(ch["group"])
        name = _clean_name(ch["name"])

        # 跳过纯英文/数字的频道名（可能是无效或非中文内容）
        if not _is_chinese(name) and not _is_chinese(group):
            # 但保留 CCTV 开头的
            if not name.upper().startswith("CCTV"):
                continue

        key = (group, name)
        if key not in cleaned_channels:
            cleaned_channels[key] = set()
        for u in live_urls:
            cleaned_channels[key].add(u)

    # 按分组排序
    sorted_items = sorted(cleaned_channels.items(), key=lambda x: (x[0][0], x[0][1]))

    current_group = None

    for (group, name), urls in sorted_items:
        urls = list(urls)[:MAX_SOURCES_PER_CHANNEL]

        # TXT 分组头
        if group != current_group:
            current_group = group
            txt_lines.append(f"{group},#genre#")

        for url in urls:
            txt_lines.append(f"{name},{group},{url}")

        # M3U
        best_url = urls[0]
        m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
        m3u_lines.append(best_url)

    # 写 TXT
    content = "\n".join(txt_lines)
    if OUTPUT_DIR != ".":
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(out_path, "w", encoding=OUTPUT_ENCODING) as f:
        f.write(content)

    # 写 M3U
    m3u_content = "\n".join(m3u_lines) + "\n"
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    with open(m3u_path, "w", encoding=OUTPUT_ENCODING) as f:
        f.write(m3u_content)

    logger.info("生成 %s: %d 频道, %.1f KB",
                 out_path, len(cleaned_channels), len(content.encode()) / 1024)
    logger.info("生成 %s: %d 频道, %.1f KB",
                 m3u_path, len(cleaned_channels), len(m3u_content.encode()) / 1024)

    return out_path
