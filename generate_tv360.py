import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "tv360.m3u"

# Daftar channel populer TV360 Vietnam
TV360_CHANNELS = [
    # Kênh VTV (Nasional)
    {"name": "VTV1 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv1-hd?id=1"},
    {"name": "VTV2 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv2-hd?id=2"},
    {"name": "VTV3 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv3-hd?id=3"},
    {"name": "VTV4 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv4-hd?id=4"},
    {"name": "VTV5 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv5-hd?id=5"},
    {"name": "VTV7 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv7-hd?id=7"},
    {"name": "VTV8 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv8-hd?id=8"},
    {"name": "VTV9 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv9-hd?id=9"},

    # Thể Thao / Sports (TV360 & HTV)
    {"name": "HTV Thể Thao", "category": "Sports", "url": "https://tv360.vn/tv/htv-the-thao?id=99"},
    {"name": "TV360 1 HD", "category": "Sports", "url": "https://tv360.vn/tv/tv360-1?id=9881"},
    {"name": "TV360 2 HD", "category": "Sports", "url": "https://tv360.vn/tv/tv360-2?id=9882"},

    # Kênh Thiết Yếu / Berita & Publik
    {"name": "ANTV (Công An)", "category": "Essential", "url": "https://tv360.vn/tv/antv?id=11"},
    {"name": "QPVN (Quốc Phòng)", "category": "Essential", "url": "https://tv360.vn/tv/qpvn?id=12"},
    {"name": "Vietnam Today", "category": "Essential", "url": "https://tv360.vn/tv/vietnam-today?id=13"}
]

REFERRER = "https://tv360.vn/"
ORIGIN = "https://tv360.vn"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_tv360_stream(page, channel):
    """Membuka halaman channel TV360 dan menyadap M3U8 link"""
    found_url = None

    def on_request(request):
        nonlocal found_url
        url = request.url
        # Sadap URL stream m3u8 dari CDN Viettel/TV360
        if ".m3u8" in url and ("tv360" in url or "viettel" in url or "cdn" in url or "vtt" in url):
            if not found_url:
                found_url = url

    page.on("request", on_request)

    try:
        page.goto(channel['url'], wait_until="domcontentloaded", timeout=20000)
        
        # Jeda sejenak untuk memicu pembacaan player
        for _ in range(15):
            if found_url:
                break
            page.wait_for_timeout(500)

    except Exception as e:
        logger.warning(f"⚠️ Warning saat membuka {channel['name']}: {e}")

    page.remove_listener("request", on_request)
    return found_url

def main():
    logger.info("🚀 Memulai pemindaian TV360 Vietnam...")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--autoplay-policy=no-user-gesture-required"
            ]
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            extra_http_headers={"Referer": REFERRER, "Origin": ORIGIN}
        )
        page = context.new_page()

        for ch in TV360_CHANNELS:
            logger.info(f"➡️ Menjelajah {ch['name']}...")
            stream_url = fetch_tv360_stream(page, ch)

            if stream_url:
                logger.info(f"  ✅ Ditemukan: {stream_url}")
                ch['stream'] = stream_url
                results.append(ch)
            else:
                logger.warning(f"  ❌ Gagal mendapatkan stream untuk {ch['name']}")

        browser.close()

    if results:
        lines = [
            '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
            f'# TV360 Vietnam Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        ]

        for item in results:
            lines.append(f'#EXTINF:-1 tvg-id="{item["name"]}" group-title="TV360 - {item["category"]}",{item["name"]}')
            lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}')
            lines.append(f'#EXTVLCOPT:http-referrer={REFERRER}')
            lines.append(f'#EXTVLCOPT:http-origin={ORIGIN}')
            lines.append(f'#KODIPROP:inputstream.adaptive.stream_headers=Referer={REFERRER}&Origin={ORIGIN}&User-Agent={USER_AGENT}')
            lines.append(item['stream'])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))

        logger.info(f"🎉 SUKSES! {len(results)} channel TV360 berhasil disimpan di {filepath}")
    else:
        logger.error("❌ Gagal mendapatkan semua channel TV360.")
        sys.exit(1)

if __name__ == "__main__":
    main()
