import os
import sys
import logging
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv.m3u"

# Daftar halaman channel resmi Dens.tv
DENS_CHANNELS = [
    # Local TV
    {"name": "Metro TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/6/metro-tv"},
    {"name": "Trans TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/3/trans-tv"},
    {"name": "Trans7", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/4/trans7"},
    {"name": "tvOne", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/1/tvone"},
    {"name": "Kompas TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/2/kompas-tv"},
    {"name": "NET TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/5/net-tv"},
    {"name": "ANTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/7/antv"},
    {"name": "RTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/8/rtv"},
    {"name": "TVRI", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/9/tvri"},
    {"name": "Jak TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/10/jaktv"},

    # Premium TV
    {"name": "Dens Play Channel", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/101/dens-play"},
    {"name": "Dens Food Channel", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/102/dens-food"},
    {"name": "Dens Showbizz", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/103/dens-showbizz"},
    {"name": "Dens Life", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/104/dens-life"},

    # International TV
    {"name": "CNA", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/55/cna"},
    {"name": "Al Jazeera English", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/56/al-jazeera-english"},
    {"name": "France 24", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/57/france-24"},
    {"name": "DW English", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/58/dw-english"}
]

DENS_REFERRER = "https://www.dens.tv/"
DENS_ORIGIN = "https://www.dens.tv"
DENS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_stream_link(page, channel):
    """Membuka web Dens.tv dan menyadap request m3u8 asli"""
    found_url = None

    def on_response(response):
        nonlocal found_url
        url = response.url
        # Menangkap request stream m3u8 dari domain CDN Dens.tv
        if ".m3u8" in url and ("dens.tv" in url or "digdayahd" in url):
            if "index.m3u8" in url or "master" in url:
                found_url = url

    page.on("response", on_response)

    try:
        page.goto(channel['url'], wait_until="commit", timeout=15000)
        
        # Tunggu max 6 detik untuk request jaringan dimuat
        for _ in range(12):
            if found_url:
                break
            page.wait_for_timeout(500)

    except Exception as e:
        logger.warning(f"⚠️ Warning saat membuka {channel['name']}: {e}")

    page.remove_listener("response", on_response)
    return found_url

def main():
    logger.info("🚀 Memulai ekstraksi stream Dens.tv...")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=DENS_UA,
            extra_http_headers={"Referer": DENS_REFERRER, "Origin": DENS_ORIGIN}
        )
        page = context.new_page()

        for ch in DENS_CHANNELS:
            logger.info(f"➡️ Menjelajah {ch['name']}...")
            stream_url = fetch_stream_link(page, ch)

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
            f'# Generated Dens.tv Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        ]

        for item in results:
            lines.append(f'#EXTINF:-1 tvg-id="{item["name"]}" group-title="Dens.tv - {item["category"]}",{item["name"]}')
            lines.append(f'#EXTVLCOPT:http-user-agent={DENS_UA}')
            lines.append(f'#EXTVLCOPT:http-referrer={DENS_REFERRER}')
            lines.append(f'#EXTVLCOPT:http-origin={DENS_ORIGIN}')
            lines.append(f'#KODIPROP:inputstream.adaptive.stream_headers=Referer={DENS_REFERRER}&Origin={DENS_ORIGIN}&User-Agent={DENS_UA}')
            lines.append(item['stream'])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))

        logger.info(f"🎉 SUKSES! {len(results)} channel berhasil disimpan di {filepath}")
    else:
        logger.error("❌ Gagal mengambil semua channel Dens.tv.")
        sys.exit(1)

if __name__ == "__main__":
    main()
