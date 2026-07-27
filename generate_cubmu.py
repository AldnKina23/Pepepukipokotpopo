import requests
import json
import os
import sys
import logging
from datetime import datetime

# ========== KONFIGURASI ==========
OUTPUT_DIR = "playlists"
OUTPUT_FILE = "cubmu.m3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://www.cubmu.com"
API_URL = "https://api.cubmu.com/v1/channel/live"  # Endpoint channel live CubMu

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_cubmu_channels():
    """Mengambil daftar channel dan link stream dari CubMu"""
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"{BASE_URL}/",
        "Origin": BASE_URL,
        "Accept": "application/json, text/plain, */*"
    }
    
    session = requests.Session()
    channels_data = []

    try:
        logger.info("➡️ Meminta data channel dari CubMu API...")
        response = session.get(API_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"❌ Gagal mengakses API: HTTP {response.status_code}")
            return []

        data = response.json()
        
        # Ekstrak channel dari struktur JSON CubMu
        # Catatan: Struktur JSON disesuaikan dengan key dari API CubMu (misal: data/results)
        items = data.get("data", []) if isinstance(data, dict) else []

        for item in items:
            name = item.get("title") or item.get("name")
            stream_url = item.get("stream_url") or item.get("url")
            logo = item.get("poster") or item.get("logo", "")

            if name and stream_url:
                channels_data.append({
                    "name": name,
                    "logo": logo,
                    "stream_url": stream_url
                })
                logger.info(f"✅ Ditemukan: {name}")

    except Exception as e:
        logger.error(f"❌ Error saat merayap CubMu: {e}")

    return channels_data

def generate_m3u_content(channels):
    """Format hasil ke playlist M3U"""
    lines = ["#EXTM3U"]
    lines.append(f'# Generated CubMu: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    for ch in channels:
        lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="CubMu" tvg-logo="{ch["logo"]}",{ch["name"]}')
        lines.append(f'#EXTVLCOPT:http-referrer={BASE_URL}/')
        lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}')
        lines.append(ch["stream_url"])
        lines.append('')

    return '\n'.join(lines)

def save_m3u(content):
    """Simpan file ke folder playlists/cubmu.m3u"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"💾 File berhasil disimpan di: {filepath}")

if __name__ == "__main__":
    logger.info("🚀 Memulai CubMu M3U Generator")
    channels = fetch_cubmu_channels()
    
    if channels:
        m3u_text = generate_m3u_content(channels)
        save_m3u(m3u_text)
        logger.info(f"🎉 Selesai! Total {len(channels)} channel berhasil didapatkan.")
    else:
        logger.error("❌ Tidak ada channel yang berhasil diambil.")
        sys.exit(1)
