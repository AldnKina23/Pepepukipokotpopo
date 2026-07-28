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
    {"name": "LIVE STREAMING", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/3/live-streaming-1"},
    {"name": "DENS PLAY", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/107/densplay"},
    {"name": "DENS LIFESTYLE", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/42/denslifestyle"},
    {"name": "DRNS FOOD CHANNEL", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/117/densfood-channel"},
    {"name": "DENS SHOWBIZ", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/102/densshowbiz"},
    {"name": "DENS KNOWLEDGE", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/1/densknowledge"},
    {"name": "JOWO", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/137/channel-jowo"},
    {"name": "METRO TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/6/metro-tv"},
    {"name": "BTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/80/btv"},
    {"name": "BERITA SATU", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/131/berita-satu"},
    {"name": "MDTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/13/mdtv"},
    {"name": "RTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/22/rtv"},
    {"name": "ELSHINTA TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/94/elshinta-tv"},
    {"name": "MAGMA TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/122/magna-channel"},
    {"name": "TVRI SPORT", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/118/tvri-sport"},
    {"name": "TVRI", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/17/tvri"},
    {"name": "JAKTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/112/jak-tv"},
    {"name": "RODJA TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/21/rodjatv"},
    {"name": "DAAI TV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/23/daai-tv"},
    {"name": "NTV", "category": "Local TV", "url": "https://www.dens.tv/tv-local/watch/138/nusantara-tv-ntv"},
    {"name": "NamaCh", "category": "Local TV", "url": "Linkweb"},
    

    # Premium TV
    {"name": "MCE", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/92/my-cinema-europe-hd"},
    {"name": "CREMA TV", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/127/crema-tv"},
    {"name": "QWEST", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/143/qwest-tv"},
    {"name": "STINGRAY CLASSICA", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/128/stingray-classica"},
    {"name": "DANCE TV", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/130/dance-tv"},
    {"name": "MOTORVISION", "category": "Premium TV", "url": "https://www.dens.tv/tv-premium/watch/98/motorvision"},
    
    
    # International TV
    {"name": "CNA", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/61/cna"},
    {"name": "NHK WORLD JAPAN", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/77/nhk-world-japan"},
    {"name": "ALJAZEERA ENGLISH", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/56/al-jazeera-english"},
    {"name": "TRT WORLD", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/41/trt-world"},
    {"name": "RUSSIA TODAY", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/144/russia-today-rt"},
    {"name": "WION TV", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/79/wion"},
    {"name": "FREEDOM", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/104/freedom"},
    {"name": "ALJAZEERA ARABIC", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/27/al-jazeera-arabic"},
    {"name": "CCTV 4", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/85/cctv-4"},
    {"name": "FRANCE 24", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/69/france-24"},
    {"name": "TV 5 MONDE", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/90/tv5monde-asie"},
    {"name": "DW", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/81/dw-tv"},
    {"name": "DIM", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/132/dim-tv"},
    {"name": "TBN", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/78/tbn"},
    {"name": "CGTN", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/16/cgtn-documentary"},
    {"name": "QURAN TV", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/82/quran-tv"},
    {"name": "SUNNA TV", "category": "International TV", "url": "https://www.dens.tv/tv-international/watch/88/sunna-tv"}
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
