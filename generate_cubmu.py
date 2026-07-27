import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "cubmu.m3u"
BASE_URL = "https://www.cubmu.com"

# KID:KEY DRM ClearKey CubMu
CLEARKEY_DRM = "1d37f079910b49f08b40deb547514c76:c4ead9b8ce1242a38bbb08eba5d2af4a"

# Daftar channel CubMu
CHANNELS = [
    {"slug": "210-trans-tv", "name": "TRANS TV", "logo": "https://www.cubmu.com/images/trans-tv.png"},
    {"slug": "201-trans-7", "name": "TRANS 7", "logo": "https://www.cubmu.com/images/trans-7.png"},
    {"slug": "202-cnn-indonesia", "name": "CNN INDONESIA", "logo": "https://www.cubmu.com/images/cnn.png"},
    {"slug": "203-cnbc-indonesia", "name": "CNBC INDONESIA", "logo": "https://www.cubmu.com/images/cnbc.png"},
    {"slug": "211-metro-tv", "name": "METRO TV", "logo": ""},
    {"slug": "363-tvone", "name": "TVONE", "logo": ""},
    {"slug": "215-sctv", "name": "SCTV", "logo": ""},
    {"slug": "216-indosiar", "name": "INDOSIAR", "logo": ""},
    {"slug": "217-rcti", "name": "RCTI", "logo": ""},
    {"slug": "218-gtv", "name": "GTV", "logo": ""},
    {"slug": "243-jaktv", "name": "JAKTV", "logo": ""},
    {"slug": "245-btv", "name": "BTV", "logo": ""},
    {"slug": "220-kompas-tv", "name": "KOMPAS TV", "logo": ""},
    {"slug": "221-mdtv", "name": "MDTV", "logo": ""},
    {"slug": "246-rtv", "name": "RTV", "logo": ""},
    {"slug": "222-mnc-tv", "name": "MNCTV", "logo": ""},
    {"slug": "223-tvri", "name": "TVRI NASIONAL", "logo": ""},
    {"slug": "364-antv", "name": "ANTV", "logo": ""},
    {"slug": "284-jtv", "name": "JTV", "logo": ""},
    {"slug": "214-berita-satu", "name": "BERITA SATU", "logo": ""},
    {"slug": "219-garuda-tv", "name": "GARUDA TV", "logo": ""},
    {"slug": "227-tvn-movies", "name": "TVN MOVIES", "logo": ""},
    {"slug": "229-celestial-movies", "name": "CELESTIAL MOVIES", "logo": ""},
    {"slug": "230-bioskop-indonesia", "name": "BIOSKOP INDONESIA", "logo": ""},
    {"slug": "232-thrill", "name": "THRILL", "logo": ""},
    {"slug": "185-movies-news", "name": "MOVIES NEWS", "logo": ""},
    {"slug": "248-cartoon-tv-premium", "name": "CARTOON TV PREMIUM", "logo": ""},
    {"slug": "249-cartoon-tv", "name": "CARTOON TV", "logo": ""},
    {"slug": "186-dunia-anak", "name": "DUNIA ANAK", "logo": ""},
    {"slug": "250-cartoon-tv-classic", "name": "CARTOON TV CLASSIC", "logo": ""},
    {"slug": "205-knowledge+", "name": "KNOWLEDGE +", "logo": ""},
    {"slug": "234-cgtn-documentary", "name": "CGTN DOCUMENTARY", "logo": ""},
    {"slug": "194-tvn", "name": "TVN", "logo": ""},
    {"slug": "236-nhk-world-premium", "name": "NHK WORLD PREMIUM", "logo": ""},
    {"slug": "247-channel-jowo", "name": "CHANNEL JOWO", "logo": ""},
    {"slug": "263-!nsert", "name": "!NSERT", "logo": ""},
    {"slug": "265-dunia-lain", "name": "DUNIA LAIN", "logo": ""},
    {"slug": "266-cctv4", "name": "CCTV4", "logo": ""},
    {"slug": "267-tv5-monde", "name": "TV5 MONDE", "logo": ""},
    {"slug": "268-one-tv", "name": "ONE TV", "logo": ""},
    {"slug": "274-travel-tv", "name": "TRAVEL TV", "logo": ""},
    {"slug": "208-eat-n-go", "name": "EAT & GO", "logo": ""},
    {"slug": "196-fashion-tv", "name": "FASHION TV", "logo": ""},
    {"slug": "276-cooking-tv", "name": "COOKING TV", "logo": ""},
    {"slug": "277-gaming-tv", "name": "GAMING TV", "logo": ""},
    {"slug": "278-dens-food-channel", "name": "DENS FOOD CHANNEL", "logo": ""},
    {"slug": "279-dens-play-channel", "name": "DENS PLAY CHANNEL", "logo": ""},
    {"slug": "251-superyacht-tv", "name": "SUPERYACHT TV", "logo": ""},
    {"slug": "280-dens-show-bizz", "name": "DENS SHOW BIZZ", "logo": ""},
    {"slug": "195-musik-indonesia", "name": "MUSIK INDONESIA", "logo": ""},
    {"slug": "281-song-tv", "name": "SONG TV", "logo": ""},
    {"slug": "238-abc-australia", "name": "ABC AUSTRALIA", "logo": ""},
    {"slug": "209-channel-newsasia", "name": "CHANNEL NEWSASIA", "logo": ""},
    {"slug": "237-cnbc-asia", "name": "CNBC ASIA", "logo": ""},
    {"slug": "197-al-jazeera", "name": "AL JAZEERA", "logo": ""},
    {"slug": "199-euronews", "name": "EURONEWS", "logo": ""},
    {"slug": "258-france-24", "name": "FRANCE 24", "logo": ""},
    {"slug": "259-cgtn", "name": "CGTN", "logo": ""},
    {"slug": "260-russia-today", "name": "RUSSIA TODAY", "logo": ""},
    {"slug": "261-arirang", "name": "ARIRANG", "logo": ""},
    {"slug": "283-wion-tv", "name": "WION TV", "logo": ""},
    {"slug": "204-al-quran-al-kareem", "name": "AL QURAN AL KAREEM", "logo": ""},
    {"slug": "187-tvmu", "name": "TVMU", "logo": ""},
    {"slug": "239-tv9", "name": "TV9", "logo": ""},
    {"slug": "240-nabawi-tv", "name": "NABAWI TV", "logo": ""},
    {"slug": "244-daystar", "name": "DAYSTAR", "logo": ""},
    {"slug": "241-daai-tv", "name": "DAAI TV", "logo": ""},
    {"slug": "594-hope-channel", "name": "HOPE CHANNEL", "logo": ""},
    {"slug": "242-pijar-tv", "name": "PIJAR TV", "logo": ""},
    {"slug": "200-khazanah", "name": "KHAZANAH", "logo": ""},
    {"slug": "203-golf-plus-id", "name": "GOLF PLUS ID", "logo": ""},
    {"slug": "252-football-tv", "name": "FOOTBALL TV", "logo": ""},
    {"slug": "253-sports-tv", "name": "SPORTS TV", "logo": ""},
    {"slug": "254-xtrem-sports", "name": "XTREM TV", "logo": ""},
    {"slug": "224-tvri-sport", "name": "TVRI SPORT", "logo": ""},
    {"slug": "255-speed-tv", "name": "SPEED TV", "logo": ""},
    {"slug": "256-fight-tv-premium", "name": "FIGHT TV PREMIUM", "logo": ""},
    {"slug": "257-psj-tv", "name": "PSJTV", "logo": ""}
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_mpd_url(page, channel):
    target_url = f"{BASE_URL}/watch/live-tv/{channel['slug']}"
    found_mpd = None

    def handle_request(request):
        nonlocal found_mpd
        if "manifest.mpd" in request.url and not found_mpd:
            found_mpd = request.url

    page.on("request", handle_request)

    try:
        page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
    except Exception as e:
        logger.warning(f"⚠️ {channel['name']}: Error loading page - {e}")

    return found_mpd

def main():
    logger.info("🚀 Memulai CubMu MPD & DRM Extractor")
    successful_channels = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for ch in CHANNELS:
            logger.info(f"➡️ Memproses {ch['name']}...")
            mpd_url = get_mpd_url(page, ch)

            if mpd_url:
                logger.info(f"✅ {ch['name']}: Link MPD Ditemukan!")
                successful_channels.append({**ch, "stream_url": mpd_url})
            else:
                logger.warning(f"⚠️ {ch['name']}: MPD tidak ditemukan")

        browser.close()

    if successful_channels:
        lines = ["#EXTM3U", f'# Generated CubMu DRM Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n']
        for ch in successful_channels:
            lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="CubMu" tvg-logo="{ch["logo"]}",{ch["name"]}')
            # Konfigurasi DRM ClearKey
            lines.append('#KODIPROP:inputstream.adaptive.manifest_type=mpd')
            lines.append('#KODIPROP:inputstream.adaptive.license_type=clearkey')
            lines.append(f'#KODIPROP:inputstream.adaptive.license_key={CLEARKEY_DRM}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            lines.append(f'#EXTVLCOPT:http-referrer={BASE_URL}/')
            lines.append(ch["stream_url"])
            lines.append('')

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
        logger.info(f"🎉 SUKSES! File disimpan di {filepath}")
    else:
        logger.error("❌ GAGAL! Tidak ada link MPD yang berhasil ditangkap.")
        sys.exit(1)

if __name__ == "__main__":
    main()
