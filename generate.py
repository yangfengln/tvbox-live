"""
生成 tvbox 兼容的 TXT 直播源文件
"""

import logging
from datetime import datetime, timezone

from config import OUTPUT_DIR, OUTPUT_FILE, OUTPUT_ENCODING, MAX_SOURCES_PER_CHANNEL

logger = logging.getLogger(__name__)


def generate(channels):
    """生成 tvbox TXT 格式输出"""
    lines = []
    lines.append(
        f"# tvbox 直播源 - 自动更新于 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    lines.append(f"# 共 {len(channels)} 个频道")
    lines.append("")

    # 按分组排序输出
    channels.sort(key=lambda c: (c["group"], c["name"]))

    current_group = None
    have_any_live = False

    for ch in channels:
        # 过滤：至少有一个可用源
        live_urls = [
            u[1] for u in ch["urls"] if isinstance(u, tuple) and u[0] == "live"
        ]
        if not live_urls:
            continue

        # 每个频道最多保留 N 个源
        live_urls = live_urls[:MAX_SOURCES_PER_CHANNEL]
        have_any_live = True

        # 分组头
        if ch["group"] != current_group:
            current_group = ch["group"]
            lines.append(f"{current_group},#genre#")

        for url in live_urls:
            lines.append(f"{ch['name']},{ch['group']},{url}")

        lines.append("")

    # 写入文件
    import os

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    content = "\n".join(lines)
    with open(out_path, "w", encoding=OUTPUT_ENCODING) as f:
        f.write(content)

    live_channel_count = len(
        {ch["name"] + ch["group"] for ch in channels if any(
            isinstance(u, tuple) and u[0] == "live" for u in ch["urls"]
        )}
    )

    logger.info("生成 %s: %d 个频道有可用源, %.1f KB",
                 out_path, live_channel_count, len(content.encode()) / 1024)

    return out_path
