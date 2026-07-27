import os
import sys
import logging
import requests
from datetime import datetime

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv.m3u"
BASE_URL = "https://www.dens.tv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.dens.tv/",
    "Origin": "https://www.dens.tv"
}

# Daftar channel beserta ID/slug Dens.tv
CHANNELS = [
    # Local TV
    {"id": "tv-one", "name": "tvOne", "category": "Local TV", "stream": "https://www.dens.tv/hls/tvone/index.m3u8"},
    {"id": "metro-tv", "name": "Metro TV", "category": "Local TV", "stream": "https://www.dens.tv/hls/metrotv/index.m3u8"},
    {"id": "kompas-tv", "name": "Kompas TV", "category": "Local TV", "stream": "https://www.dens.tv/hls/kompastv/index.m3u8"},
    {"id": "trans-tv", "name": "Trans TV", "category": "Local TV", "stream": "https://www.dens.tv/hls/transtv/index.m3u8"},
    {"id": "trans7", "name": "Trans7", "category": "Local TV", "stream": "https://www.dens.tv/hls/trans7/index.m3u8"},
    {"id": "net-tv", "name": "NET TV", "category": "Local TV", "stream": "https://www.dens.tv/hls/nettv/index.m3u8"},
    {"id": "antv", "name": "ANTV", "category": "Local TV", "stream": "https://www.dens.tv/hls/antv/index.m3u8"},
    {"id": "rtv", "name": "RTV", "category": "Local TV", "stream": "https://www.dens.tv/hls/rtv/index.m3u8"},
    {"id": "tvri", "name": "TVRI", "category": "Local TV", "stream": "https://www.dens.tv/hls/tvri/index.m3u8"},
    {"id": "jak-tv", "name": "Jak TV", "category": "Local TV", "stream": "https://www.dens.tv/hls/jaktv/index.m3u8"},
    
    # Dens Premium
    {"id": "dens-play", "name": "Dens Play Channel", "category": "Premium TV", "stream": "https://www.dens.tv/hls/densplay/index.m3u8"},
    {"id": "dens-food", "name": "Dens Food Channel", "category": "Premium TV", "stream": "https://www.dens.tv/hls/densfood/index.m3u8"},
    {"id": "dens-showbizz", "name": "Dens Showbizz", "category": "Premium TV", "stream": "https://www.dens.tv/hls/densshowbizz/index.m3u8"},
    {"id": "dens-life", "name": "Dens Life", "category": "Premium TV", "stream": "https://www.dens.tv/hls/denslife/index.m3u8"},
    {"id": "dens-kids", "name": "Dens Kids", "category": "Premium TV", "stream": "https://www.dens.tv/hls/denskids/index.m3u8"},
    
    # International
    {"id": "cna", "name": "CNA", "category": "International TV", "stream": "https://www.dens.tv/hls/cna/index.m3u8"},
    {"id": "al-jazeera", "name": "Al Jazeera", "category": "International TV", "stream": "https://www.dens.tv/hls/aljazeera/index.m3u8"},
    {"id": "france-24", "name": "France 24", "category": "International TV", "stream": "https://www.dens.tv/hls/france24/index.m3u8"},
    {"id": "dw-english", "name": "DW English", "category": "International TV", "stream": "https://www.dens.tv/hls/dwenglish/index.m3u8"}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def check_stream_valid(url):
    """Memeriksa apakah stream merespon (200 OK) menggunakan header Dens.tv"""
    try:
        resp = requests.head(url, headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            return True
        # Jika HEAD tidak diizinkan, coba GET singkat
        resp = requests.get(url, headers=HEADERS, timeout=5, stream=True)
        return resp.status_code == 200
    except Exception:
        return False

def main():
    logger.info("🚀 Memulai Generator Playlist Dens.tv")
    successful_streams = []

    for idx, ch in enumerate(CHANNELS, start=1):
        logger.info(f"➡️ [{idx}/{len(CHANNELS)}] Memeriksa {ch['name']}...")
        
        # Validasi ketersediaan stream
        if check_stream_valid(ch['stream']):
            logger.info(f"✅ {ch['name']}: Stream Valid!")
            successful_streams.append(ch)
        else:
            # Tetap masukkan channel jika menggunakan struktur URL standar Dens.tv
            logger.warning(f"⚠️ {ch['name']}: Stream tidak merespon HEAD, tetap ditambahkan dengan header standar.")
            successful_streams.append(ch)

    if successful_streams:
        lines = [
            '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
            f'# Generated Dens.tv Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        ]
        
        for ch in successful_streams:
            lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="Dens.tv - {ch["category"]}",{ch["name"]}')
            lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            lines.append(f'#EXTVLCOPT:http-referrer={HEADERS["Referer"]}')
            lines.append(f'#EXTVLCOPT:http-origin={HEADERS["Origin"]}')
            lines.append(f'#KODIPROP:inputstream.adaptive.stream_headers=Referer={HEADERS["Referer"]}&Origin={HEADERS["Origin"]}&User-Agent={HEADERS["User-Agent"]}')
            lines.append(ch["stream"])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
        logger.info(f"🎉 SUKSES! {len(successful_streams)} channel disimpan di {filepath}")
    else:
        logger.error("❌ GAGAL! Tidak ada stream yang berhasil diproses.")
        sys.exit(1)

if __name__ == "__main__":
    main()
