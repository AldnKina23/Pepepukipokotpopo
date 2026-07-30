import os
import json
import requests

DOMAIN = "https://daddylive.mov"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{DOMAIN}/"
}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REFERER = f"{DOMAIN}/"

def get_channels():
    channels = {}
    
    # Endpoint JSON resmi dari daddylive al
    urls = [
        f"{DOMAIN}/cache/24-7channels.json",
        f"{DOMAIN}/cache/tv/tv.json"
    ]
    
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    for ch in data:
                        cid = ch.get("channel_id") or ch.get("id", "")
                        name = ch.get("channel_name") or ch.get("name", "")
                        if cid and name:
                            channels[str(cid)] = str(name)
                elif isinstance(data, dict):
                    for date, content in data.items():
                        if isinstance(content, dict):
                            for event_type, events in content.items():
                                if isinstance(events, list):
                                    for event in events:
                                        for ch in event.get("channels", []) + event.get("channels2", []):
                                            cid = ch.get("channel_id", "")
                                            name = ch.get("channel_name", "")
                                            if cid and name:
                                                channels[str(cid)] = str(name)
            print(f"Berhasil mengambil data dari {url}: {len(channels)} channels")
        except Exception as e:
            print(f"Gagal mengambil data dari {url}: {e}")
            
    return channels

def get_group(name):
    n = name.lower()
    if any(x in n for x in ["sky sports", "tnt sports", "bt sport"]):
        return "Sports UK"
    elif any(x in n for x in ["bbc", "itv", "channel 4", "channel 5"]):
        return "UK TV"
    elif any(x in n for x in ["espn", "fox sports", "nbc", "cbs", "nfl", "nba", "mlb", "nhl"]):
        return "Sports USA"
    elif any(x in n for x in ["bein", "eurosport", "dazn"]):
        return "Sports International"
    elif any(x in n for x in ["ufc", "wwe", "boxing", "fight"]):
        return "Combat Sports"
    elif any(x in n for x in ["f1", "formula", "motogp", "nascar"]):
        return "Motorsport"
    elif any(x in n for x in ["tennis", "wimbledon"]):
        return "Tennis"
    elif any(x in n for x in ["cricket"]):
        return "Cricket"
    elif any(x in n for x in ["rugby"]):
        return "Rugby"
    elif any(x in n for x in ["golf", "pga"]):
        return "Golf"
    elif any(x in n for x in ["ppv", "event ppv"]):
        return "PPV"
    else:
        return "General"

def build_m3u(channels):
    lines = ["#EXTM3U"]
    for cid, name in sorted(channels.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 9999):
        group = get_group(name)
        
        # PERBAIKAN: Format URL streaming yang benar adalah /live/stream-X.php
        stream_url = f"{DOMAIN}/live/stream-{cid}.php"
        
        lines.append(f'#EXTINF:-1 tvg-id="{cid}" tvg-logo="" group-title="{group}",{name}')
        lines.append(f'#EXTVLCOPT:http-referrer={REFERER}')
        lines.append(f'#EXTVLCOPT:http-user-agent={UA}')
        lines.append(f'#KODIPROP:inputstream.adaptive.manifest_headers=Referer={REFERER}&User-Agent={UA}')
        lines.append(f'#KODIPROP:inputstream.adaptive.stream_headers=Referer={REFERER}&User-Agent={UA}')
        lines.append(stream_url)
    return "\n".join(lines)

def main():
    os.makedirs("output", exist_ok=True)
    print("Memproses daftar channel...")
    channels = get_channels()
    print(f"Total unik channel: {len(channels)}")

    m3u = build_m3u(channels)
    with open("output/playlist.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u)

    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(f"""<html><head><title>DaddyLive M3U</title></head>
        <body>
        <h1>DaddyLive M3U Proxy (.mov)</h1>
        <p>Total channels: {len(channels)}</p>
        <p><a href="playlist.m3u8">Download Playlist</a></p>
        </body></html>""")

    print("Selesai! Hasil disimpan di output/playlist.m3u8")

if __name__ == "__main__":
    main()
