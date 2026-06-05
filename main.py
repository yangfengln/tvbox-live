#!/usr/bin/env python3
"""
tvbox 直播源自动采集验证生成
用法: python main.py
"""

import logging
import sys

from collect import collect
from validate import validate
from generate import generate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def main():
    logger.info("=" * 50)
    logger.info("tvbox 直播源自动更新开始")

    # 1. 采集
    logger.info("--- 采集 ---")
    channels = collect()
    if not channels:
        logger.error("未采集到任何频道，退出。请检查源 URL 是否可访问。")
        sys.exit(1)

    # 2. 验证
    logger.info("--- 验证 ---")
    channels = validate(channels)

    # 3. 生成
    logger.info("--- 生成 ---")
    out_path = generate(channels)

    # 统计
    total_urls = sum(len(ch["urls"]) for ch in channels)
    live_urls = sum(
        1 for ch in channels
        for u in ch["urls"]
        if isinstance(u, tuple) and u[0] == "live"
    )
    channels_with_live = sum(
        1 for ch in channels
        if any(isinstance(u, tuple) and u[0] == "live" for u in ch["urls"])
    )

    logger.info("=" * 50)
    logger.info("完成!")
    logger.info("  频道总数: %d", len(channels))
    logger.info("  有可用源的频道: %d", channels_with_live)
    logger.info("  源地址总数: %d", total_urls)
    logger.info("  可用源地址: %d (%.1f%%)", live_urls,
                 live_urls / total_urls * 100 if total_urls else 0)
    logger.info("  输出文件: %s", out_path)


if __name__ == "__main__":
    main()
