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

# Daftar slug channel populer CubMu
CHANNELS = [
    {"slug": "trans-tv", "name": "Trans TV"},
    {"slug": "trans7", "name": "Trans 7"},
    {"slug": "cnn-indonesia", "name": "CNN Indonesia"},
    {"slug": "cnbc-indonesia", "name": "CNBC Indonesia"},
    {"slug": "tvone", "name": "tvOne"},
    {"slug": "antv", "name": "ANTV"},
    {"slug": "net-tv", "name": "NET TV"},
    {"slug": "kompas-tv", "name": "Kompas TV"}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_stream_url(session, slug):
    """Mengambil link m3u8 dari halaman channel CubMu"""
    url = f"{BASE_URL}/live/{slug}"
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": BASE_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"⚠️ {slug}: HTTP {resp.status_code}")
            return None

        # Cari pola URL m3u8 di dalam source code HTML / Javascript Next.js
        match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', resp.text)
        if match:
            stream_url = match.group(0).replace('\\/', '/')
            logger.info(f"✅ {slug}: Mendapat stream URL")
            return stream_url

        logger.warning(f"⚠️ {slug}: Link stream .m3u8 tidak ditemukan di halaman")
        return None

    except Exception as e:
        logger.error(f"❌ {slug}: Error - {e}")
        return None

def generate_m3u_content(channels_data):
    """Format ke M3U"""
    lines = ["#EXTM3U"]
    lines.append(f'# Generated CubMu: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    for ch in channels_data:
        lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="CubMu",{ch["name"]}')
        lines.append(f'#EXTVLCOPT:http-referrer={BASE_URL}/')
        lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}')
        lines.append(ch["stream_url"])
        lines.append('')

    return '\n'.join(lines)

def save_m3u(content):
    """Simpan file M3U"""
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
        stream_url = get_stream_url(session, channel["slug"])
        
        if stream_url:
            successful_channels.append({
                "name": channel["name"],
                "stream_url": stream_url
            })

    if successful_channels:
        m3u_content = generate_m3u_content(successful_channels)
        save_m3u(m3u_content)
        logger.info(f"🎉 SUKSES! {len(successful_channels)}/{len(CHANNELS)} channel berhasil diambil.")
    else:
        logger.error("❌ GAGAL! Tidak ada channel yang berhasil didapatkan.")
        sys.exit(1)

if __name__ == "__main__":
    main()
