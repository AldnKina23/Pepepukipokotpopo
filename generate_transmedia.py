import os
from datetime import datetime

# Informasi Output
OUTPUT_DIR = "playlists"
OUTPUT_FILE = "transmedia.m3u"

# HTTP Referrer sesuai request
REFERRER_URL = "https://20.detik.com/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Daftar Channel Transmedia dari server Detik
CHANNELS = [
    {
        "name": "Trans TV",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/2/23/Trans_TV_logo_2013.png",
        "stream_url": "https://video.detik.com/transtv/smil:transtv.smil/playlist.m3u8"
    },
    {
        "name": "Trans 7",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/e/eb/Trans7_2013.png",
        "stream_url": "https://video.detik.com/trans7/smil:trans7.smil/playlist.m3u8"
    },
    {
        "name": "CNN Indonesia",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/0/09/CNN_Indonesia_logo.svg",
        "stream_url": "https://video.detik.com/cnn/smil:cnn.smil/playlist.m3u8"
    },
    {
        "name": "CNBC Indonesia",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/e/e3/CNBC_Indonesia_logo.svg",
        "stream_url": "https://video.detik.com/cnbc/smil:cnbc.smil/playlist.m3u8"
    }
]

def generate_m3u():
    lines = ["#EXTM3U"]
    lines.append(f'# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC')
    lines.append("")

    for ch in CHANNELS:
        lines.append(f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="Transmedia" tvg-logo="{ch["logo"]}",{ch["name"]}')
        lines.append(f'#EXTVLCOPT:http-referrer={REFERRER_URL}')
        lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}')
        lines.append(ch["stream_url"])
        lines.append("")

    return "\n".join(lines)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    content = generate_m3u()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Berhasil membuat playlist dengan {len(CHANNELS)} channel: {filepath}")

if __name__ == "__main__":
    main()
