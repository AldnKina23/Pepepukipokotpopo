"""
meWATCH Fast Extractor (Single Proxy + Fast Timeout)
===================================================
"""

import json
import re
import time
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, Response

FREE_CHANNELS = [
    {"name": "Channel 5", "url": "https://www.mewatch.sg/channels/channel-5/97098"},
    {"name": "Channel 8", "url": "https://www.mewatch.sg/channels/Channel-8/97104"},
    {"name": "Channel U", "url": "https://www.mewatch.sg/channels/channel-u/97129"},
    {"name": "Suria", "url": "https://www.mewatch.sg/channels/suria/97084"},
    {"name": "Vasantham", "url": "https://www.mewatch.sg/channels/vasantham/97096"},
    {"name": "CNA", "url": "https://www.mewatch.sg/channels/cna/97072"},
    {"name": "Live 1", "url": "https://www.mewatch.sg/channels/live-1/97073"},
    {"name": "CWG CH01", "url": "https://www.mewatch.sg/channels/CWG-CH01/822075"},
    {"name": "CWG CH02", "url": "https://www.mewatch.sg/channels/CWG-CH02/822074"},
    {"name": "CWG CH03", "url": "https://www.mewatch.sg/channels/CWG-CH03/822077"},
    {"name": "CWG CH04", "url": "https://www.mewatch.sg/channels/CWG-CH04/822076"},
    {"name": "Live 5", "url": "https://www.mewatch.sg/channels/live-5/98202"},
    {"name": "Live 6", "url": "https://www.mewatch.sg/channels/live-6/204746"},
    {"name": "FIFA+", "url": "https://www.mewatch.sg/channels/FIFA+-557763"}
]

# --- MASUKKAN 1 PROXY TERBAIK DI SINI ---
SINGLE_PROXY = "socks5://45.43.63.37:10808"

def parse_drm_kid(response_bytes: bytes) -> Optional[str]:
    try:
        content_str = response_bytes.decode('utf-8', errors='ignore')
        kid_match = re.search(r'cenc:default_KID="([0-9a-fA-F\-]{32,36})"', content_str)
        if kid_match:
            return kid_match.group(1).replace('-', '').lower()
    except Exception:
        pass
    return None

def extract_channel_stream(page_url: str, channel_name: str) -> Dict:
    result = {
        "channel": channel_name,
        "page_url": page_url,
        "m3u8_urls": [],
        "mpd_urls": [],
        "license_servers": [],
        "kids": [],
        "status": "Failed"
    }

    with sync_playwright() as p:
        try:
            # Gunakan 1 Proxy saja
            browser = p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-setuid-sandbox'],
                proxy={"server": SINGLE_PROXY}
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()

            # Blokir gambar, font, dan stylesheet agar koneksi proxy jauh lebih cepat
            page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())

            def handle_response(response: Response):
                url = response.url
                if ".m3u8" in url and url not in result["m3u8_urls"]:
                    result["m3u8_urls"].append(url)
                elif ".mpd" in url and url not in result["mpd_urls"]:
                    result["mpd_urls"].append(url)
                    try:
                        kid = parse_drm_kid(response.body())
                        if kid and kid not in result["kids"]:
                            result["kids"].append(kid)
                    except Exception:
                        pass

                if ("license" in url.lower() or "widevine" in url.lower()) and response.request.method == "POST":
                    if url not in result["license_servers"]:
                        result["license_servers"].append(url)

            page.on("response", handle_response)

            print(f"[*] Navigasi: {channel_name}...")
            # Timeout dipangkas ke 10000ms (10 detik saja)
            page.goto(page_url, wait_until="domcontentloaded", timeout=10000)
            
            # Waktu tunggu pendek untuk memicu JS Player
            time.sleep(5)

            if result["m3u8_urls"] or result["mpd_urls"]:
                result["status"] = "Success"
            
            browser.close()
        except Exception as e:
            print(f"[!] {channel_name} Gagal/Timeout: {e}")
            result["status"] = "Timeout/Error"

    return result

def main():
    all_results = []
    print(f" Menggunakan Single Proxy: {SINGLE_PROXY}\n")

    for ch in FREE_CHANNELS:
        data = extract_channel_stream(ch["url"], ch["name"])
        all_results.append(data)
        print(f"[{data['status']}] {ch['name']}")

    with open("mewatch_streams.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4)
    print("\n[+] Selesai! Data tersimpan di 'mewatch_streams.json'")

if __name__ == "__main__":
    main()
