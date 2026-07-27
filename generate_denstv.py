import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv.m3u"
BASE_URL = "https://www.dens.tv"

# Kategori Dens.tv yang akan dipindai
CATEGORIES = [
    {"name": "Local TV", "url": "https://www.dens.tv/tv-local"},
    {"name": "Premium TV", "url": "https://www.dens.tv/tv-premium"},
    {"name": "International TV", "url": "https://www.dens.tv/tv-international"}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_channel_links(page, category_url):
    """Mengambil semua link channel dari halaman kategori Dens.tv"""
    channels = []
    try:
        page.goto(category_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Ekstrak semua elemen anchor yang mengarah ke link nonton TV
        links = page.eval_on_selector_all(
            'a[href*="/tv/"]',
            'elements => elements.map(e => ({ href: e.href, name: e.innerText.trim() }))'
        )
        
        seen_hrefs = set()
        for link in links:
            href = link["href"]
            # Filter link agar hanya mengambil channel TV murni
            if href not in seen_hrefs and "/tv/" in href and not href.endswith("/tv/"):
                seen_hrefs.add(href)
                # Bersihkan nama channel jika ada newline
                clean_name = link["name"].split('\n')[0] if link["name"] else href.split('/')[-1].replace('-', ' ').title()
                channels.append({"url": href, "name": clean_name})
                
    except Exception as e:
        logger.warning(f"⚠️ Gagal mengambil daftar channel dari {category_url}: {e}")
        
    return channels

def extract_stream_url(page, channel_url):
    """Menangkap URL stream (.m3u8 atau .mpd) saat player Dens.tv dibuka"""
    found_stream = None

    def handle_request(request):
        nonlocal found_stream
        url = request.url
        # Tangkap HLS (.m3u8) atau MPEG-DASH (.mpd)
        if (".m3u8" in url or ".mpd" in url) and not found_stream:
            if "blob:" not in url:
                found_stream = url

    page.on("request", handle_request)

    try:
        page.goto(channel_url, timeout=25000, wait_until="domcontentloaded")
        
        # Coba klik player jika ada tombol play
        try:
            page.click("video", timeout=2000)
        except Exception:
            pass

        # Tunggu jaringan menangkap link stream
        for _ in range(10):
            if found_stream:
                break
            page.wait_for_timeout(500)

    except Exception as e:
        logger.warning(f"⚠️ Error saat memuat channel {channel_url}: {e}")

    # Lepas listener event agar tidak numpuk
    page.remove_listener("request", handle_request)
    return found_stream

def main():
    logger.info("🚀 Memulai Dens.tv Extractor")
    all_channels = []
    successful_streams = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Step 1: Kumpulkan semua link channel dari 3 kategori
        for cat in CATEGORIES:
            logger.info(f"🔍 Memindai kategori: {cat['name']}...")
            cat_channels = get_channel_links(page, cat['url'])
            logger.info(f"   Ditemukan {len(cat_channels)} channel di {cat['name']}")
            for ch in cat_channels:
                all_channels.append({**ch, "category": cat['name']})

        logger.info(f"📋 Total channel unik terkumpul: {len(all_channels)}")

        # Step 2: Extract URL stream dari setiap channel
        for idx, ch in enumerate(all_channels, start=1):
            logger.info(f"➡️ [{idx}/{len(all_channels)}] Memproses {ch['name']}...")
            stream_url = extract_stream_url(page, ch['url'])

            if stream_url:
                logger.info(f"✅ {ch['name']}: Stream Ditemukan!")
                successful_streams.append({**ch, "stream_url": stream_url})
            else:
                logger.warning(f"⚠️ {ch['name']}: Stream tidak ditemukan")

        browser.close()

    # Step 3: Simpan ke M3U
    if successful_streams:
        lines = ["#EXTM3U", f'# Generated Dens.tv Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n']
        for ch in successful_streams:
            lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="Dens.tv - {ch["category"]}",{ch["name"]}')
            
            # Jika stream berupa .mpd, tambahkan tag manifest type
            if ".mpd" in ch["stream_url"]:
                lines.append('#KODIPROP:inputstream.adaptive.manifest_type=mpd')
                
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            lines.append(f'#EXTVLCOPT:http-referrer={BASE_URL}/')
            lines.append(ch["stream_url"])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
        logger.info(f"🎉 SUKSES! {len(successful_streams)} channel disimpan di {filepath}")
    else:
        logger.error("❌ GAGAL! Tidak ada stream yang berhasil ditangkap.")
        sys.exit(1)

if __name__ == "__main__":
    main()
