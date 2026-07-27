import os
import sys
import logging
import concurrent.futures
import requests
from datetime import datetime

# Samakan output file agar langsung menimpa denstv.m3u utama
OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv.m3u"

SCAN_START = 251
SCAN_END = 500

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
    """Mengecek ID h{ch_number} dan memasukkan nama channel dummy yang sesuai"""
    ch_id = f"h{ch_number:02d}" if ch_number < 10 else f"h{ch_number}"
    ch_name_param = f"Channel_{ch_id.upper()}"
    
    # URL wajib menyertakan app_type, userid, dan chname agar stream tidak fallback/stuck di 1 siaran
    stream_url = f"https://op-flashcon-digdayahd-1.dens.tv/h/{ch_id}/index.m3u8?app_type=web&userid=lite&chname={ch_name_param}"

    try:
        resp = requests.get(stream_url, headers=HEADERS, timeout=3, stream=True)
        if resp.status_code == 200:
            return {"id": ch_id, "url": stream_url, "name": ch_name_param}
    except Exception:
        pass

    return None

def main():
    logger.info(f"🔍 Pemindaian ID Dens.tv (h{SCAN_START} - h{SCAN_END})...")
    valid_channels = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(check_channel_id, i) for i in range(SCAN_START, SCAN_END + 1)]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                logger.info(f"✅ DITEMUKAN: {res['id']}")
                valid_channels.append(res)

    valid_channels.sort(key=lambda x: int(x['id'].replace('h', '')))

    if valid_channels:
        lines = [
            '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
            f'# Scanned Dens.tv Streams: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        ]

        for item in valid_channels:
            disp_name = f"DensTV - {item['id'].upper()}"
            lines.append(f'#EXTINF:-1 tvg-id="{disp_name}" group-title="Dens.tv Scanned",{disp_name}')
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

        logger.info(f"🎉 Selesai! Menemukan {len(valid_channels)} stream. File {filepath} berhasil diperbarui.")
    else:
        logger.error("❌ Tidak ada ID aktif yang ditemukan.")
        sys.exit(1)

if __name__ == "__main__":
    main()
