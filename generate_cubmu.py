import requests
import json
import re
import os
import sys
import logging
from datetime import datetime

# ========== KONFIGURASI ==========
OUTPUT_DIR = "playlists"
OUTPUT_FILE = "cubmu.m3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://www.cubmu.com"

# Daftar channel CubMu dengan ID & path yang tepat
CHANNELS = [
    {"path": "210-trans-tv", "name": "Trans TV", "logo": "https://www.cubmu.com/images/trans-tv.png"},
    {"path": "201-trans-7", "name": "Trans 7", "logo": "https://www.cubmu.com/images/trans-7.png"},
    {"path": "202-cnn-indonesia", "name": "CNN Indonesia", "logo": "https://www.cubmu.com/images/cnn.png"},
    {"path": "203-cnbc-indonesia", "name": "CNBC Indonesia", "logo": "https://www.cubmu.com/images/cnbc.png"}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def extract_m3u8(html_content):
    """Mencari URL stream .m3u8 di dalam kode HTML/JavaScript Next.js CubMu"""
    # Pattern 1: Mencari URL m3u8 langsung
    match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html_content)
    if match:
        return match.group(0).replace('\\/', '/')
    
    # Pattern 2: Mencari di dalam JSON __NEXT_DATA__
    next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content)
    if next_data_match:
        try:
            json_data = json.loads(next_data_match.group(1))
            # Ekstrak rekursif / pencarian teks m3u8 di JSON
            json_str = json.dumps(json_data)
            m3u8_find = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', json_str)
            if m3u8_find:
                return m3u8_find.group(0).replace('\\/', '/')
        except Exception:
            pass

    return None

def fetch_channel_stream(session, channel):
    url = f"{BASE_URL}/watch/live-tv/{channel['path']}"
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"{BASE_URL}/live-tv",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"⚠️ {channel['name']}: HTTP {resp.status_code}")
            return None

        stream_url = extract_m3u8(resp.text)
        if stream_url:
            logger.info(f"✅ {channel['name']}: Stream didapatkan!")
            return stream_url
        else:
            logger.warning(f"⚠️ {channel['name']}: Halaman terbuka (200 OK) tapi link .m3u8 terlindungi/tidak ditemukan.")
            return None

    except Exception as e:
        logger.error(f"❌ {channel['name']}: Error - {e}")
        return None

def generate_m3u_content(channels_data):
    lines = ["#EXTM3U"]
    lines.append(f'# Generated CubMu: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    for ch in channels_data:
        lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="CubMu" tvg-logo="{ch["logo"]}",{ch["name"]}')
        lines.append(f'#EXTVLCOPT:http-referrer={BASE_URL}/')
        lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}')
        lines.append(ch["stream_url"])
        lines.append('')

    return '\n'.join(lines)

def save_m3u(content):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"💾 File M3U berhasil disimpan di: {filepath}")

def main():
    logger.info("🚀 Memulai CubMu M3U Generator")
    session = requests.Session()
    successful_channels = []

    for channel in CHANNELS:
        logger.info(f"➡️ Memproses {channel['name']} ({channel['path']})...")
        stream_url = fetch_channel_stream(session, channel)
        
        if stream_url:
            successful_channels.append({
                **channel,
                "stream_url": stream_url
            })

    if successful_channels:
        m3u_content = generate_m3u_content(successful_channels)
        save_m3u(m3u_content)
        logger.info(f"🎉 SUKSES! {len(successful_channels)}/{len(CHANNELS)} channel berhasil didapatkan.")
    else:
        logger.error("❌ GAGAL! Link m3u8 CubMu membutuhkan API Auth Token atau pemutar video berbasis JS.")
        sys.exit(1)

if __name__ == "__main__":
    main()
