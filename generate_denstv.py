import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv.m3u"

# Daftar target URL web Dens.tv resmi
TARGET_CHANNELS = [
    # Local TV
    {"name": "Metro TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/6/metro-tv"},
    {"name": "Trans7", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/4/trans7"},
    {"name": "Trans TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/3/trans-tv"},
    {"name": "tvOne", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/1/tvone"},
    {"name": "Kompas TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/2/kompas-tv"},
    {"name": "NET TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/5/net-tv"},
    {"name": "ANTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/7/antv"},
    {"name": "RTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/8/rtv"},
    {"name": "TVRI", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/9/tvri"},
    {"name": "Jak TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/10/jaktv"},
    
    # International TV
    {"name": "Al Jazeera English", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/56/al-jazeera-english"},
    {"name": "CNA", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/55/cna"},
    {"name": "France 24", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/57/france-24"},
    {"name": "DW English", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/58/dw-english"},
    
    # Premium TV
    {"name": "Dens Play", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/101/dens-play"},
    {"name": "Dens Food", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/102/dens-food"},
]

DENS_REFERRER = "https://www.dens.tv/"
DENS_ORIGIN = "https://www.dens.tv"
DENS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_m3u8_from_page(page, target_url):
    """Membuka web Dens.tv dan menangkap link .m3u8 asli yang dipanggil oleh player"""
    captured_stream = None

    def handle_request(request):
        nonlocal captured_stream
        url = request.url
        # Menangkap request m3u8 asli dari domain CDN Dens.tv
        if ".m3u8" in url and "dens.tv" in url:
            captured_stream = url

    # Dengarkan seluruh traffic jaringan dari browser
    page.on("request", handle_request)

    try:
        page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        
        # Coba klik tombol play jika player tertahan/paused
        try:
            page.click("video", timeout=3000)
        except Exception:
            pass

        # Tunggu sampai request m3u8 tertangkap (max 10 detik)
        for _ in range(20):
            if captured_stream:
                break
            page.wait_for_timeout(500)

    except Exception as e:
        logger.error(f"Error saat memuat {target_url}: {e}")

    return captured_stream

def main():
    logger.info("🚀 Memulai Scraping Murni Dens.tv via Playwright...")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--mute-audio"
            ]
        )
        context = browser.new_context(
            user_agent=DENS_UA,
            viewport={"width": 1280, "height": 720}
        )

        page = context.new_page()

        for ch in TARGET_CHANNELS:
            logger.info(f"🔍 Mengambil stream asli untuk: {ch['name']} ({ch['url']})")
            stream_url = get_m3u8_from_page(page, ch['url'])

            if stream_url:
                logger.info(f"✅ DAFTAR HASIL: {ch['name']} -> {stream_url}")
                ch['stream'] = stream_url
                results.append(ch)
            else:
                logger.warning(f"❌ GAGAL mendapatkan link asli untuk {ch['name']}")

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

        logger.info(f"🎉 SELESAI! {len(results)} channel asli berhasil disimpan di {filepath}")
    else:
        logger.error("❌ Tidak ada stream yang berhasil ditangkap.")
        sys.exit(1)

if __name__ == "__main__":
    main()
