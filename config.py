"""
tvbox 直播源采集配置
用户可在此增删源 URL 和调整参数
"""

# 采集源列表
# 支持 M3U 格式、tvbox TXT 格式、以及返回 JSON 的 API
SOURCE_URLS = [
    # === GitHub 上维护的 IPTV 源 ===
    # YueChan Live - 国内85频道 IPv4/IPv6
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/IPTV.m3u",

    # wwb521 直播源 - M3U格式
    "https://raw.bgithub.xyz/wwb521/live/refs/heads/main/tv.m3u",

    # Guovin iptv-api 自动更新源 (CDN)
    "https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u",

    # === 添加你自己的源 ===
    # "https://example.com/my-live-sources.txt",
]

# ========== 验证参数 ==========
VALIDATE_TIMEOUT = 3       # HTTP 请求超时(秒)
VALIDATE_RETRIES = 1       # 失败重试次数
MAX_CONCURRENT = 50        # 并发验证数

# ========== 生成参数 ==========
MAX_SOURCES_PER_CHANNEL = 3  # 每个频道最多保留的源地址数

# ========== 输出 ==========
OUTPUT_DIR = "."
OUTPUT_FILE = "live.txt"
OUTPUT_ENCODING = "utf-8"

# 频道分组名称映射（统一分组名）
GROUP_ALIASES = {
    "央视": "央视",
    "卫视": "卫视",
    "CCTV": "央视",
    "卫视台": "卫视",
    "地方台": "地方台",
    "高清": "综合",
    "港澳台": "港澳台",
    "体育": "体育",
    "少儿": "少儿",
    "新闻": "新闻",
}
