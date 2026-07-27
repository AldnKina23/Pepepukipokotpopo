import os
import sys
import logging
import concurrent.futures
import requests
from datetime import datetime

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv_scanned.m3u"

# Range ID yang akan di-scan (misal dari h1 sampai h300)
SCAN_START = 1
SCAN_END = 300

DENS_REFERRER = "https://www.dens.tv/"
DENS_ORIGIN = "https://www.dens.tv"
DENS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent": DENS_UA,
    "Referer": DENS_REFERRER,
    "Origin": DENS_ORIGIN
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def check_channel_id(ch_number):
    """Mengecek apakah ID h{ch_number} menghasilkan stream m3u8 yang aktif"""
    ch_id = f"h{ch_number:02d}" if ch_number < 10 else f"h{ch_number}"
    stream_url = f"https://op-flashcon-digdayahd-1.dens.tv/h/{ch_id}/index.m3u8?app_type=web&userid=lite"

    try:
        # Kirim request HEAD / GET singkat dengan timeout 3 detik
        resp = requests.head(stream_url, headers=HEADERS, timeout=3)
        if resp.status_code == 200:
            return {"id": ch_id, "url": stream_url}
        
        # Coba metode GET jika HEAD di-reject oleh server
        resp = requests.get(stream_url, headers=HEADERS, timeout=3, stream=True)
        if resp.status_code == 200:
            return {"id": ch_id, "url": stream_url}
    except Exception:
        pass

    return None

def main():
    logger.info(f"🔍 Memulai pemindaian ID dari h{SCAN_START} sampai h{SCAN_END}...")
    valid_channels = []

    # Menggunakan Multi-threading agar proses scan 300 ID selesai dalam hitungan detik
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_channel_id, i) for i in range(SCAN_START, SCAN_END + 1)]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                logger.info(f"✅ DITEMUKAN ACTIVE STREAM: {res['id']} -> {res['url']}")
                valid_channels.append(res)

    # Urutkan berdasarkan ID
    valid_channels.sort(key=lambda x: int(x['id'].replace('h', '')))

    if valid_channels:
        lines = [
            '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
            f'# Scanned Dens.tv Streams: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        ]

        for item in valid_channels:
            channel_name = f"DensTV Channel {item['id'].upper()}"
            lines.append(f'#EXTINF:-1 tvg-id="{channel_name}" group-title="Dens.tv - Scanned",{channel_name}')
            lines.append(f'#EXTVLCOPT:http-user-agent={DENS_UA}')
            lines.append(f'#EXTVLCOPT:http-referrer={DENS_REFERRER}')
            lines.append(f'#EXTVLCOPT:http-origin={DENS_ORIGIN}')
            lines.append(f'#KODIPROP:inputstream.adaptive.stream_headers=Referer={DENS_REFERRER}&Origin={DENS_ORIGIN}&User-Agent={DENS_UA}')
            lines.append(item['url'])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))

        logger.info(f"🎉 SELESAI! Menemukan {len(valid_channels)} stream aktif. Disimpan di {filepath}")
    else:
        logger.error("❌ Tidak ada ID aktif yang ditemukan.")
        sys.exit(1)

if __name__ == "__main__":
    main()
