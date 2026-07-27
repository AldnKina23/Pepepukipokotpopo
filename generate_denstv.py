import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv.m3u"
BASE_URL = "https://www.dens.tv"

# Daftar channel Dens.tv (Lokal, Premium, International)
CHANNELS = [
    # TV Local
    {"id": "tv-one", "name": "tvOne", "category": "Local TV"},
    {"id": "metro-tv", "name": "Metro TV", "category": "Local TV"},
    {"id": "kompas-tv", "name": "Kompas TV", "category": "Local TV"},
    {"id": "trans-tv", "name": "Trans TV", "category": "Local TV"},
    {"id": "trans7", "name": "Trans7", "category": "Local TV"},
    {"id": "net-tv", "name": "NET TV", "category": "Local TV"},
    {"id": "antv", "name": "ANTV", "category": "Local TV"},
    {"id": "rtv", "name": "RTV", "category": "Local TV"},
    {"id": "tvri", "name": "TVRI", "category": "Local TV"},
    {"id": "jak-tv", "name": "Jak TV", "category": "Local TV"},
    {"id": "btv", "name": "BTV", "category": "Local TV"},
    {"id": "jtv", "name": "JTV", "category": "Local TV"},
    
    # TV Premium / Dens Channels
    {"id": "dens-play", "name": "Dens Play Channel", "category": "Premium TV"},
    {"id": "dens-food", "name": "Dens Food Channel", "category": "Premium TV"},
    {"id": "dens-showbizz", "name": "Dens Showbizz", "category": "Premium TV"},
    {"id": "dens-life", "name": "Dens Life", "category": "Premium TV"},
    {"id": "dens-kids", "name": "Dens Kids", "category": "Premium TV"},
    
    # TV International & News
    {"id": "channel-news-asia", "name": "CNA", "category": "International TV"},
    {"id": "al-jazeera", "name": "Al Jazeera", "category": "International TV"},
    {"id": "france-24", "name": "France 24", "category": "International TV"},
    {"id": "euronews", "name": "Euronews", "category": "International TV"},
    {"id": "dw-english", "name": "DW English", "category": "International TV"},
    {"id": "cgtn", "name": "CGTN", "category": "International TV"},
    {"id": "arirang", "name": "Arirang", "category": "International TV"}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def extract_stream_url(page, ch):
    # Format URL player Dens.tv
    target_url = f"{BASE_URL}/tv/{ch['id']}"
    found_stream = None

    def handle_request(request):
        nonlocal found_stream
        url = request.url
        # Tangkap stream .m3u8, .mpd, atau .ts
        if (".m3u8" in url or ".mpd" in url) and not found_stream:
            if "blob:" not in url:
                found_stream = url

    page.on("request", handle_request)

    try:
        page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
        
        # Coba klik player jika butuh pemicu play
        try:
            page.click("video", timeout=2000)
        except Exception:
            pass

        # Tunggu jaringan menangkap link stream (maksimal 5 detik)
        for _ in range(10):
            if found_stream:
                break
            page.wait_for_timeout(500)

    except Exception as e:
        logger.warning(f"⚠️ Error saat memuat channel {ch['name']}: {e}")

    page.remove_listener("request", handle_request)
    return found_stream

def main():
    logger.info("🚀 Memulai Dens.tv Stream Extractor")
    successful_streams = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for idx, ch in enumerate(CHANNELS, start=1):
            logger.info(f"➡️ [{idx}/{len(CHANNELS)}] Memproses {ch['name']}...")
            stream_url = extract_stream_url(page, ch)

            if stream_url:
                logger.info(f"✅ {ch['name']}: Stream Ditemukan!")
                successful_streams.append({**ch, "stream_url": stream_url})
            else:
                logger.warning(f"⚠️ {ch['name']}: Stream tidak ditemukan")

        browser.close()

    if successful_streams:
        lines = ["#EXTM3U", f'# Generated Dens.tv Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n']
        for ch in successful_streams:
            lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="Dens.tv - {ch["category"]}",{ch["name"]}')
            
            if ".mpd" in ch["stream_url"]:
                lines.append('#KODIPROP:inputstream.adaptive.manifest_type=mpd')
                
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            lines.append(f'#EXTVLCOPT:http-referrer={BASE_URL}/')
            lines.append(ch["stream_url"])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
        logger.info(f"🎉 SUKSES! {len(successful_streams)} channel disimpan di {filepath}")
    else:
        logger.error("❌ GAGAL! Tidak ada stream yang berhasil ditangkap.")
        sys.exit(1)

if __name__ == "__main__":
    main()
