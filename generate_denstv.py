import os
import sys
import logging
from datetime import datetime

OUTPUT_DIR = "playlists"
OUTPUT_FILE = "denstv.m3u"

# Mapping ID/Kode CDN Dens.tv beserta nama channel-nya
CHANNELS = [
    # Local TV
    {"id": "h12", "name": "Metro TV", "chname": "Metro_TV", "category": "Local TV"},
    {"id": "h217", "name": "SCTV", "chname": "SCTV", "category": "Local TV"},
    {"id": "h218", "name": "Indosiar", "chname": "Indosiar", "category": "Local TV"},
    {"id": "h01", "name": "tvOne", "chname": "tvOne", "category": "Local TV"},
    {"id": "h02", "name": "Kompas TV", "chname": "Kompas_TV", "category": "Local TV"},
    {"id": "h03", "name": "Trans TV", "chname": "Trans_TV", "category": "Local TV"},
    {"id": "h04", "name": "Trans7", "chname": "Trans7", "category": "Local TV"},
    {"id": "h05", "name": "NET TV", "chname": "NET_TV", "category": "Local TV"},
    {"id": "h06", "name": "ANTV", "chname": "ANTV", "category": "Local TV"},
    {"id": "h07", "name": "RTV", "chname": "RTV", "category": "Local TV"},
    {"id": "h08", "name": "TVRI", "chname": "TVRI", "category": "Local TV"},
    {"id": "h09", "name": "Jak TV", "chname": "Jak_TV", "category": "Local TV"},
    {"id": "h10", "name": "JTV", "chname": "JTV", "category": "Local TV"},
    {"id": "h11", "name": "BTV", "chname": "BTV", "category": "Local TV"},
    
    # Premium / Dens TV
    {"id": "h20", "name": "Dens Play Channel", "chname": "Dens_Play", "category": "Premium TV"},
    {"id": "h21", "name": "Dens Food Channel", "chname": "Dens_Food", "category": "Premium TV"},
    {"id": "h22", "name": "Dens Showbizz", "chname": "Dens_Showbizz", "category": "Premium TV"},
    {"id": "h23", "name": "Dens Life", "chname": "Dens_Life", "category": "Premium TV"},
    {"id": "h24", "name": "Dens Kids", "chname": "Dens_Kids", "category": "Premium TV"},
    
    # International TV
    {"id": "h43", "name": "Al Jazeera English", "chname": "Al_Jazeera_English", "category": "International TV"},
    {"id": "h40", "name": "CNA", "chname": "CNA", "category": "International TV"},
    {"id": "h41", "name": "France 24", "chname": "France_24", "category": "International TV"},
    {"id": "h42", "name": "Euronews", "chname": "Euronews", "category": "International TV"},
    {"id": "h44", "name": "DW English", "chname": "DW_English", "category": "International TV"},
    {"id": "h45", "name": "CGTN", "chname": "CGTN", "category": "International TV"},
    {"id": "h46", "name": "Arirang", "chname": "Arirang", "category": "International TV"}
]

DENS_REFERRER = "https://www.dens.tv/"
DENS_ORIGIN = "https://www.dens.tv"
DENS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Memulai Generate Dens.tv Playlist dengan CDN Direct URL...")

    lines = [
        '#EXTM3U url-tvg="https://raw.githubusercontent.com/dhasap/dhanytv/main/epg.xml"',
        f'# Generated Dens.tv Playlist: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
    ]

    for ch in CHANNELS:
        # Konstruksi link M3U8 langsung ke server CDN Dens.tv
        stream_url = f"https://op-flashcon-digdayahd-1.dens.tv/h/{ch['id']}/index.m3u8?app_type=web&userid=lite&chname={ch['chname']}"
        
        lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="Dens.tv - {ch["category"]}",{ch["name"]}')
        lines.append(f'#EXTVLCOPT:http-user-agent={DENS_UA}')
        lines.append(f'#EXTVLCOPT:http-referrer={DENS_REFERRER}')
        lines.append(f'#EXTVLCOPT:http-origin={DENS_ORIGIN}')
        lines.append(f'#KODIPROP:inputstream.adaptive.stream_headers=Referer={DENS_REFERRER}&Origin={DENS_ORIGIN}&User-Agent={DENS_UA}')
        lines.append(stream_url)
        lines.append('')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))
        
    logger.info(f"🎉 SUKSES! {len(CHANNELS)} channel berhasil dibuat di {filepath}")

if __name__ == "__main__":
    main()
