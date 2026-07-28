import os
import sys
import logging
import requests
from datetime import datetime

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "tv360.m3u"

# Daftar Channel TV360 dengan ID Resmi
TV360_CHANNELS = [
    # Kênh VTV (Nasional)
    {"id": "1", "name": "VTV1 HD", "category": "VTV"},
    {"id": "2", "name": "VTV2 HD", "category": "VTV"},
    {"id": "3", "name": "VTV3 HD", "category": "VTV"},
    {"id": "4", "name": "VTV4 HD", "category": "VTV"},
    {"id": "5", "name": "VTV5 HD", "category": "VTV"},
    {"id": "7", "name": "VTV7 HD", "category": "VTV"},
    {"id": "8", "name": "VTV8 HD", "category": "VTV"},
    {"id": "9", "name": "VTV9 HD", "category": "VTV"},

    # Thể Thao / Sports
    {"id": "99", "name": "HTV Thể Thao", "category": "Sports"},
    {"id": "9881", "name": "TV360 1 HD", "category": "Sports"},
    {"id": "9882", "name": "TV360 2 HD", "category": "Sports"},

    # Essential
    {"id": "11", "name": "ANTV (Công An)", "category": "Essential"},
    {"id": "12", "name": "QPVN (Quốc Phòng)", "category": "Essential"},
    {"id": "13", "name": "Vietnam Today", "category": "Essential"}
]

DENS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
REFERRER = "https://tv360.vn/"
ORIGIN = "https://tv360.vn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_tv360_stream(channel_id):
    """Mengambil link m3u8 langsung dari API internal TV360"""
    api_url = f"https://tv360.vn/public/v1/composite/get-link-play?channelId={channel_id}&quality=HD"
    
    headers = {
        "User-Agent": DENS_UA,
        "Referer": REFERRER,
        "Origin": ORIGIN,
        "Accept": "application/json, text/plain, */*",
        "Device-Type": "WEB"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Ambil streaming URL dari response API
            stream_url = data.get("data", {}).get("hlsUrl") or data.get("data", {}).get("streamUrl")
            if stream_url:
                return stream_url
    except Exception as e:
        logger.warning(f"⚠️ API Error ID {channel_id}: {e}")

    # Fallback ke CDN Direct Structure jika API Publik dibatasi
    return f"https://live-cdn.tv360.vn/manifest/channel_{channel_id}/index.m3u8"

def main():
    logger.info("🚀 Memulai ekstraksi API TV360 Vietnam...")
    results = []

    for ch in TV360_CHANNELS:
        logger.info(f"➡️ Memproses {ch['name']} (ID: {ch['id']})...")
        stream_url = get_tv360_stream(ch['id'])

        if stream_url:
            logger.info(f"  ✅ Link Didapat: {stream_url}")
            ch['stream'] = stream_url
            results.append(ch)
        else:
            logger.warning(f"  ❌ Gagal mendapatkan stream untuk {ch['name']}")

    if results:
        lines = [
            '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
            f'# Generated TV360 Vietnam Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        ]

        for item in results:
            lines.append(f'#EXTINF:-1 tvg-id="{item["name"]}" group-title="TV360 - {item["category"]}",{item["name"]}')
            lines.append(f'#EXTVLCOPT:http-user-agent={DENS_UA}')
            lines.append(f'#EXTVLCOPT:http-referrer={REFERRER}')
            lines.append(f'#EXTVLCOPT:http-origin={ORIGIN}')
            lines.append(f'#KODIPROP:inputstream.adaptive.stream_headers=Referer={REFERRER}&Origin={ORIGIN}&User-Agent={DENS_UA}')
            lines.append(item['stream'])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))

        logger.info(f"🎉 SUKSES! {len(results)} channel disimpan di {filepath}")
    else:
        logger.error("❌ Gagal mendapatkan channel TV360.")
        sys.exit(1)

if __name__ == "__main__":
    main()
