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
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BASE_URL = "https://www.cubmu.com"

# Channel list dengan ID internal CubMu
CHANNELS = [
    {"id": "210", "slug": "210-trans-tv", "name": "Trans TV", "logo": "https://www.cubmu.com/images/trans-tv.png"},
    {"id": "201", "slug": "201-trans-7", "name": "Trans 7", "logo": "https://www.cubmu.com/images/trans-7.png"},
    {"id": "202", "slug": "202-cnn-indonesia", "name": "CNN Indonesia", "logo": "https://www.cubmu.com/images/cnn.png"},
    {"id": "203", "slug": "203-cnbc-indonesia", "name": "CNBC Indonesia", "logo": "https://www.cubmu.com/images/cnbc.png"}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_stream_url(session, channel):
    """Mencoba mengambil stream URL via API backend CubMu atau parse Next.js Props"""
    watch_url = f"{BASE_URL}/watch/live-tv/{channel['slug']}"
    
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"{BASE_URL}/live-tv",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        # Request 1: Ambil data NextJS Build Data dari HTML
        resp = session.get(watch_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            # Cari link m3u8 jika ada di script tags
            urls = re.findall(r'https?://[^\s"\'\\]+\.m3u8[^\s"\'\\]*', resp.text)
            if urls:
                clean_url = urls[0].replace('\\/', '/')
                logger.info(f"✅ {channel['name']}: Mendapat stream URL")
                return clean_url

            # Request 2: Jika tidak ada di HTML, panggil API Playback internal CubMu
            api_url = f"https://api.cubmu.com/v1/channel/play/{channel['id']}"
            api_headers = {
                "User-Agent": USER_AGENT,
                "Origin": BASE_URL,
                "Referer": watch_url,
                "Accept": "application/json"
            }
            api_resp = session.get(api_url, headers=api_headers, timeout=10)
            if api_resp.status_code == 200:
                data = api_resp.json()
                stream = data.get("data", {}).get("url") or data.get("stream_url")
                if stream:
                    logger.info(f"✅ {channel['name']}: Mendapat stream via API")
                    return stream

        logger.warning(f"⚠️ {channel['name']}: Stream URL tidak ditemukan")
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
    logger.info(f"💾 File berhasil disimpan di: {filepath}")

def main():
    logger.info("🚀 Memulai CubMu M3U Generator")
    session = requests.Session()
    successful_channels = []

    for channel in CHANNELS:
        logger.info(f"➡️ Memproses {channel['name']}...")
        stream_url = fetch_stream_url(session, channel)
        
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
        logger.error("❌ GAGAL! CubMu membutuhkan token login atau browser headless (Playwright/Selenium) untuk merender player.")
        sys.exit(1)

if __name__ == "__main__":
    main()
