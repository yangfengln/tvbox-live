"""
从多个公开源拉取并解析播放列表
支持 M3U 格式和 tvbox TXT 格式
"""

import re
import logging
from urllib.parse import urlparse

import requests

from config import SOURCE_URLS

logger = logging.getLogger(__name__)


def fetch_text(url, timeout=15):
    """拉取远程文本内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; tvbox-fetcher/1.0)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.warning("拉取失败 %s: %s", url, e)
        return None


def parse_m3u(text):
    """
    解析 M3U 格式
    #EXTINF:-1 group-title="央视",CCTV-1 综合
    http://xxx/1.m3u8
    返回: [(频道名, 分组, url), ...]
    """
    results = []
    pattern = re.compile(
        r'#EXTINF:.*?group-title="(.*?)".*?,(.*?)\s*\n(https?://\S+)',
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        group = m.group(1).strip()
        name = m.group(2).strip()
        url = m.group(3).strip()
        if url:
            results.append((name, group, url))
    return results


def parse_tvbox_txt(text):
    """
    解析 tvbox TXT 格式
    央视,#genre#
    CCTV1,央视,http://xxx/1.m3u8
    返回: [(频道名, 分组, url), ...]
    """
    results = []
    current_group = "未分类"
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(",#genre#"):
            current_group = line.rsplit(",#genre#", 1)[0].strip()
            continue
        parts = line.split(",")
        if len(parts) >= 3:
            name = parts[0].strip()
            group = parts[1].strip() or current_group
            url = parts[2].strip()
            if url.startswith("http"):
                results.append((name, group, url))
            else:
                # 可能是 cls:// 等其他协议，也保留
                results.append((name, group, url))
    return results


def is_m3u(text):
    """判断文本是否为 M3U 格式"""
    return "#EXTINF" in text[:2000] or "#EXTM3U" in text[:2000]


def collect():
    """从所有源采集频道列表，按 (分组, 频道名) 去重，多源保留"""
    # key: (分组, 频道名) → set of urls
    channels = {}

    for url in SOURCE_URLS:
        logger.info("采集: %s", url)
        text = fetch_text(url)
        if not text:
            continue

        if is_m3u(text):
            items = parse_m3u(text)
        else:
            items = parse_tvbox_txt(text)

        for name, group, stream_url in items:
            key = (group.strip(), name.strip())
            if key not in channels:
                channels[key] = []
            # 避免同源重复
            if stream_url not in channels[key]:
                channels[key].append(stream_url)

        logger.info("  → 解析到 %d 个条目", len(items))

    # 转换为列表
    result = [
        {"group": g, "name": n, "urls": urls}
        for (g, n), urls in channels.items()
    ]

    logger.info("合并去重后共 %d 个频道", len(result))
    return result
