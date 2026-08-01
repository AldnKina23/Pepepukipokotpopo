"""
meWATCH Stream Extractor (Updated Channel URLs + SOCKS Proxy + KID Extractor)
=============================================================================
"""

import json
import re
import time
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, Response

# Daftar channel presisi sesuai input terbaru
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

# Daftar SOCKS Proxy Singapore
PROXIES = [
    "socks5://45.43.63.37:10808",
    "socks5://109.199.105.194:1080",
    "socks5://140.245.99.105:7890",
    "socks5://43.160.255.142:7890",
    "socks5://213.35.102.40:50161",
    "socks4://180.157.93.11:7891",
    "socks4://178.128.59.180:40001"
]

def parse_drm_kid(response_bytes: bytes) -> Optional[str]:
    """Ekstrak DRM Key ID (KID) dari manifest DASH (.mpd) atau response init."""
    try:
        content_str = response_bytes.decode('utf-8', errors='ignore')
        
        # 1. Cari tag XML cenc:default_KID
        kid_match = re.search(r'cenc:default_KID="([0-9a-fA-F\-]{32,36})"', content_str)
        if kid_match:
            return kid_match.group(1).replace('-', '').lower()
        
        # 2. Cari pssh / Widevine UUID alternatif
        uuid_matches = re.findall(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', content_str)
        for uuid in uuid_matches:
            if uuid.lower() != "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed": # Saring Widevine System ID
                return uuid.replace('-', '').lower()
    except Exception:
        pass
    return None

def extract_channel_stream(page_url: str, channel_name: str, proxy_url: str) -> Dict:
    result = {
        "channel": channel_name,
        "page_url": page_url,
        "proxy_used": proxy_url,
        "m3u8_urls": [],
        "mpd_urls": [],
        "license_servers": [],
        "kids": [],
        "status": "Failed"
    }

    with sync_playwright() as p:
        browser_args = ['--no-sandbox', '--disable-setuid-sandbox']
        
        try:
            # Menjalankan Chromium JS Engine dengan proxy SOCKS
            browser = p.chromium.launch(
                headless=True, 
                args=browser_args,
                proxy={"server": proxy_url}
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Network Interception (Menyadap lalu lintas HTTP/HTTPS)
            def handle_response(response: Response):
                url = response.url
                
                # Saring link .m3u8
                if ".m3u8" in url and url not in result["m3u8_urls"]:
                    result["m3u8_urls"].append(url)
                
                # Saring link .mpd dan ambil KID
                elif ".mpd" in url and url not in result["mpd_urls"]:
                    result["mpd_urls"].append(url)
                    try:
                        kid = parse_drm_kid(response.body())
                        if kid and kid not in result["kids"]:
                            result["kids"].append(kid)
                    except Exception:
                        pass

                # Tangkap Widevine / License Server Request
                if ("license" in url.lower() or "widevine" in url.lower() or "key" in url.lower()) and response.request.method == "POST":
                    if url not in result["license_servers"]:
                        result["license_servers"].append(url)

            page.on("response", handle_response)

            print(f"[*] Navigasi: {channel_name} -> {page_url} via {proxy_url}")
            page.goto(page_url, wait_until="domcontentloaded", timeout=25000)
            
            # Waktu tunggu untuk memicu pemutaran JS video player
            time.sleep(10)

            if result["m3u8_urls"] or result["mpd_urls"]:
                result["status"] = "Success"
            
            browser.close()
        except Exception as e:
            print(f"[!] Proxy {proxy_url} error/timeout: {e}")
            result["status"] = f"Error: {str(e)}"

    return result

def main():
    all_results = []

    for ch in FREE_CHANNELS:
        success = False
        # Cobalah setiap proxy sampai ada yang berhasil mengekstrak stream
        for proxy in PROXIES:
            data = extract_channel_stream(ch["url"], ch["name"], proxy)
            if data["status"] == "Success":
                all_results.append(data)
                print(f"[+] SUCCESS: {ch['name']} | M3U8/MPD ditemukan!")
                success = True
                break
            else:
                print(f"[-] Gagal pada proxy {proxy}, mencoba proxy cadangan...")
        
        if not success:
            print(f"[!] GAGAL TOTAL untuk channel: {ch['name']}")
            all_results.append({
                "channel": ch["name"],
                "page_url": ch["url"],
                "status": "Failed All Proxies",
                "m3u8_urls": [], "mpd_urls": [], "kids": []
            })

    # Simpan hasil akhir ke JSON File
    with open("mewatch_streams.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4)
    print("\n[+] Selesai! Seluruh data channel tersimpan di 'mewatch_streams.json'")

if __name__ == "__main__":
    main()
