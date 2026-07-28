import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "tv360.m3u"

# Channel list sesuai struktur URL TV360 asli
TV360_CHANNELS = [
    {"name": "VTV1 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv1-hd?ch=2&col=1&sect=LIVE&page=home_live&c=0"},
    {"name": "VTV2 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv2-hd?ch=3&col=1&sect=LIVE&page=home_live&c=0"},
    {"name": "VTV3 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv3-hd?ch=4&col=1&sect=LIVE&page=home_live&c=0"},
    {"name": "VTV4 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv4-hd?ch=108&col=1&sect=LIVE&page=home_live&c=0"},
    {"name": "VTV6 HD", "category": "VTV", "url": "https://tv360.vn/tv/vtv6-hd?ch=10043&col=1&sect=LIVE&page=home_live&c=0"},
    {"name": "HTV Thể Thao", "category": "Sports", "url": "https://tv360.vn/tv/htv-the-thao?ch=99&col=1&sect=LIVE&page=home_live&c=0"},
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
REFERRER = "https://tv360.vn/"
ORIGIN = "https://tv360.vn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def grab_m3u8_token(page, target_url):
    """Menangkap URL m3u8 yang mengandung token 'auth=' saat web diputar"""
    token_url = None

    def handle_request(request):
        nonlocal token_url
        req_url = request.url
        # Filter khusus URL stream asli yang berisi token JWT auth
        if ("index.m3u8" in req_url or ".m3u8" in req_url) and "auth=" in req_url:
            token_url = req_url

    page.on("request", handle_request)

    try:
        page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        
        # Tunggu hingga player memicu request video berkunci token
        for _ in range(20):
            if token_url:
                break
            page.wait_for_timeout(500)

    except Exception as e:
        logger.warning(f"⚠️ Error saat memuat halaman: {e}")

    page.remove_listener("request", handle_request)
    return token_url

def main():
    logger.info("🚀 Memulai penangkapan token stream TV360...")
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
            stream_url = grab_m3u8_token(page, ch['url'])

            if stream_url:
                logger.info(f"  ✅ Token Stream Ditemukan:\n     {stream_url}")
                ch['stream'] = stream_url
                results.append(ch)
            else:
                logger.warning(f"  ❌ Gagal menangkap token untuk {ch['name']}")

        browser.close()

    if results:
        lines = [
            '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
            f'# Generated TV360 Vietnam Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
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

        logger.info(f"🎉 SUKSES! {len(results)} channel berhasil disimpan di {filepath}")
    else:
        logger.error("❌ Tidak ada token stream yang tertangkap.")
        sys.exit(1)

if __name__ == "__main__":
    main()
