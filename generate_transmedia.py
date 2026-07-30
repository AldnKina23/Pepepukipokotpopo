import os
import sys
from datetime import datetime

# Informasi Output
OUTPUT_DIR = "playlists"
OUTPUT_FILE = "transtv.m3u"

# Trans TV menggunakan stream dari server detik/transmedia
CHANNELS = [
    {
        "name": "Trans TV",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/2/23/Trans_TV_logo_2013.png",
        "stream_url": "https://video.detik.com/transtv/smil:transtv.smil/playlist.m3u8",
        "referrer": "https://www.transtv.co.id/"
    },
    {
        "name": "Trans TV (Backup)",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/2/23/Trans_TV_logo_2013.png",
        "stream_url": "https://video.detik.com/transtv/smil:transtv-live.smil/playlist.m3u8",
        "referrer": "https://www.transtv.co.id/"
    }
]

def generate_m3u():
    lines = ["#EXTM3U"]
    lines.append(f'# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC')
    lines.append("")

    for ch in CHANNELS:
        lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="Nasional" tvg-logo="{ch["logo"]}",{ch["name"]}')
        # Header penting agar stream tidak di-block oleh server Detik/Trans TV
        lines.append(f'#EXTVLCOPT:http-referrer={ch["referrer"]}')
        lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        lines.append(ch["stream_url"])
        lines.append("")

    return "\n".join(lines)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    content = generate_m3u()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Berhasil membuat playlist: {filepath}")

if __name__ == "__main__":
    main()
