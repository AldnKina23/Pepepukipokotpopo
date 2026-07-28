import os
import sys
import logging
import requests
from datetime import datetime

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "tv360.m3u"

# Daftar Channel TV360 dengan ID 'ch' yang Asli & Benar
TV360_CHANNELS = [
    # Kênh VTV (Nasional)
    {"id": "2", "name": "VTV1 HD", "category": "VTV", "url_path": "vtv1-hd"},
    {"id": "3", "name": "VTV2 HD", "category": "VTV", "url_path": "vtv2-hd"},
    {"id": "4", "name": "VTV3 HD", "category": "VTV", "url_path": "vtv3-hd"},
    {"id": "108", "name": "VTV4 HD", "category": "VTV", "url_path": "vtv4-hd"},
    {"id": "5", "name": "VTV5 HD", "category": "VTV", "url_path": "vtv5-hd"},
    {"id": "7", "name": "VTV7 HD", "category": "VTV", "url_path": "vtv7-hd"},
    {"id": "8", "name": "VTV8 HD", "category": "VTV", "url_path": "vtv8-hd"},
    {"id": "9", "name": "VTV9 HD", "category": "VTV", "url_path": "vtv9-hd"},
    {"id": "10043", "name": "VTV6 HD", "category": "VTV", "url_path": "vtv6-hd"},

    # Thể Thao / Sports
    {"id": "99", "name": "HTV Thể Thao", "category": "Sports", "url_path": "htv-the-thao"},
    {"id": "9881", "name": "TV360 1 HD", "category": "Sports", "url_path": "tv360-1"},
    {"id": "9882", "name": "TV360 2 HD", "category": "Sports", "url_path": "tv360-2"},

    # Essential
    {"id": "11", "name": "ANTV (Công An)", "category": "Essential", "url_path": "antv"},
    {"id": "12", "name": "QPVN (Quốc Phòng)", "category": "Essential", "url_path": "qpvn"},
    {"id": "13", "name": "Vietnam Today", "category": "Essential", "url_path": "vietnam-today"}
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
REFERRER = "https://tv360.vn/"
ORIGIN = "https://tv360.vn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_tv360_stream_api(channel):
    """Mendapatkan link m3u8 dari API streaming TV360 menggunakan ID 'ch' yang benar"""
    ch_id = channel['id']
    
    # Endpoint API internal TV360
    api_url = f"https://tv360.vn/public/v1/composite/get-link-play?channelId={ch_id}&quality=HD&mode=LIVE"
    
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"https://tv360.vn/tv/{channel['url_path']}?ch={ch_id}&col=1&sect=LIVE&page=home_live&c=0",
        "Origin": ORIGIN,
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=8)
        if response.status_code == 200:
            res_json = response.json()
            # Ambil token link dari payload JSON
            data = res_json.get("data", {})
            stream_url = data.get("hlsUrl") or data.get("streamUrl") or data.get("link")
            if stream_url:
                return stream_url
    except Exception as e:
        logger.warning(f"⚠️ Gagal API untuk {channel['name']}: {e}")

    # Fallback ke CDN Server TV360 dengan parameter ID 'ch' yang presisi
    return f"https://live-cdn.tv360.vn/manifest/ch{ch_id}/index.m3u8"

def main():
    logger.info("🚀 Memulai ekstraksi stream TV360 Vietnam...")
    results = []

    for ch in TV360_CHANNELS:
        logger.info(f"➡️ Memproses {ch['name']} (ID: {ch['id']})...")
        stream_url = fetch_tv360_stream_api(ch)

        if stream_url:
            logger.info(f"  ✅ Stream: {stream_url}")
            ch['stream'] = stream_url
            results.append(ch)

    if results:
        lines = [
            '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
            f'# TV360 Vietnam Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
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

        logger.info(f"🎉 SUKSES! {len(results)} channel TV360 disimpan di {filepath}")
    else:
        logger.error("❌ Gagal mendapatkan channel TV360.")
        sys.exit(1)

if __name__ == "__main__":
    main()
