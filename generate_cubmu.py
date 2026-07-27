import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "cubmu.m3u"
BASE_URL = "https://www.cubmu.com"

# KID:KEY DRM ClearKey CubMu
CLEARKEY_DRM = "1d37f079910b49f08b40deb547514c76:c4ead9b8ce1242a38bbb08eba5d2af4a"

# Daftar channel CubMu
CHANNELS = [
    {"slug": "210-trans-tv", "name": "Trans TV", "logo": "https://www.cubmu.com/images/trans-tv.png"},
    {"slug": "201-trans-7", "name": "Trans 7", "logo": "https://www.cubmu.com/images/trans-7.png"},
    {"slug": "202-cnn-indonesia", "name": "CNN Indonesia", "logo": "https://www.cubmu.com/images/cnn.png"},
    {"slug": "203-cnbc-indonesia", "name": "CNBC Indonesia", "logo": "https://www.cubmu.com/images/cnbc.png"},
    {"slug": "204-tvone", "name": "tvOne", "logo": ""},
    {"slug": "205-antv", "name": "ANTV", "logo": ""},
    {"slug": "206-net-tv", "name": "NET TV", "logo": ""},
    {"slug": "207-kompas-tv", "name": "Kompas TV", "logo": ""},
    {"slug": "208-metro-tv", "name": "Metro TV", "logo": ""}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_mpd_url(page, channel):
    target_url = f"{BASE_URL}/watch/live-tv/{channel['slug']}"
    found_mpd = None

    def handle_request(request):
        nonlocal found_mpd
        if "manifest.mpd" in request.url and not found_mpd:
            found_mpd = request.url

    page.on("request", handle_request)

    try:
        page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)  # Diperpanjang jadi 10 detik agar player loading sempurna
    except Exception as e:
        logger.warning(f"⚠️ {channel['name']}: Error loading page - {e}")

    return found_mpd

def main():
    logger.info("🚀 Memulai CubMu MPD & DRM Extractor")
    successful_channels = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for ch in CHANNELS:
            logger.info(f"➡️ Memproses {ch['name']}...")
            mpd_url = get_mpd_url(page, ch)

            if mpd_url:
                logger.info(f"✅ {ch['name']}: Link MPD Ditemukan!")
                successful_channels.append({**ch, "stream_url": mpd_url})
            else:
                logger.warning(f"⚠️ {ch['name']}: MPD tidak ditemukan")

        browser.close()

    if successful_channels:
        lines = ["#EXTM3U", f'# Generated CubMu DRM Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n']
        for ch in successful_channels:
            lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="CubMu" tvg-logo="{ch["logo"]}",{ch["name"]}')
            # Tag DRM Kodi & IPTV Player
            lines.append('#KODIPROP:inputstream.adaptive.manifest_type=mpd')
            lines.append('#KODIPROP:inputstream.adaptive.license_type=clearkey')
            lines.append(f'#KODIPROP:inputstream.adaptive.license_key={CLEARKEY_DRM}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            lines.append(f'#EXTVLCOPT:http-referrer={BASE_URL}/')
            lines.append(ch["stream_url"])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
        logger.info(f"🎉 SUKSES! File disimpan di {filepath}")
    else:
        logger.error("❌ GAGAL! Tidak ada link MPD yang berhasil ditangkap.")
        sys.exit(1)

if __name__ == "__main__":
    main()
