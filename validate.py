"""
并发验证直播源可用性
使用 asyncio + aiohttp 并发 HTTP HEAD 检测
"""

import asyncio
import logging

import aiohttp

from config import VALIDATE_TIMEOUT, VALIDATE_RETRIES, MAX_CONCURRENT

logger = logging.getLogger(__name__)


def _is_stream_url(url):
    """只验证 HTTP 流地址，跳过 cls:// 等专用协议"""
    return url.startswith("http://") or url.startswith("https://")


async def _check_one(session, url, sem):
    """检查单个 URL 是否可达"""
    async with sem:
        for attempt in range(VALIDATE_RETRIES + 1):
            try:
                async with session.head(
                    url,
                    timeout=aiohttp.ClientTimeout(total=VALIDATE_TIMEOUT),
                    allow_redirects=True,
                ) as resp:
                    # 200/206/302 都算可访问
                    if resp.status in (200, 206, 302, 301):
                        return True
            except Exception:
                if attempt < VALIDATE_RETRIES - 1:
                    await asyncio.sleep(1)
        return False


async def _validate_channels(channels):
    """并发验证所有频道源"""
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0 (compatible; tvbox-validator/1.0)"}
    ) as session:
        tasks = []
        task_map = {}  # idx → (ch_idx, url_idx)

        for ci, ch in enumerate(channels):
            for ui, url in enumerate(ch["urls"]):
                if _is_stream_url(url):
                    idx = len(tasks)
                    tasks.append(_check_one(session, url, sem))
                    task_map[idx] = (ci, ui)

        logger.info("开始验证 %d 个流地址...", len(tasks))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 标记结果
        live_count = 0
        for idx, ok in enumerate(results):
            if idx in task_map and ok is True:
                ci, ui = task_map[idx]
                channels[ci]["urls"][ui] = ("live", channels[ci]["urls"][ui])
                live_count += 1

        # 其余标记为 dead
        for ci, ch in enumerate(channels):
            for ui in range(len(ch["urls"])):
                if not isinstance(ch["urls"][ui], tuple):
                    ch["urls"][ui] = ("dead", ch["urls"][ui])

        logger.info("验证完成: %d 可用 / %d 总数", live_count, len(tasks))
        return channels


def validate(channels):
    """入口：验证频道源可用性"""
    return asyncio.run(_validate_channels(channels))
