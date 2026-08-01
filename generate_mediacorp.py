import json
import re
import time
import requests
from typing import Dict, Optional, List
from playwright.sync_api import sync_playwright, Response

FREE_CHANNELS = [
    {"name": "Channel 5", "url": "https://www.mewatch.sg/channels/channel-5/97098"},
    {"name": "Channel 8", "url": "https://www.mewatch.sg/channels/Channel-8/97104"},
    {"name": "Channel U", "url": "https://www.mewatch.sg/channels/channel-u/97129"},
    {"name": "Suria", "url": "https://www.mewatch.sg/channels/suria/97084"},
    {"name": "CNA", "url": "https://www.mewatch.sg/channels/cna/97072"}
]

# --- 1. OTOMATIS AMBIL PROXY SINGAPURA DARI PROXYSCRAPE ---
def fetch_singapore_proxies() -> List[Dict]:
    print("\n[+] Mengunduh daftar proxy Singapura dari ProxyScrape...")
    sources = [
        ("socks5", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=ipport&format=text&protocol=socks5&country=sg"),
        ("socks4", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=ipport&format=text&protocol=socks4&country=sg"),
        ("http", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=ipport&format=text&protocol=http&country=sg")
    ]
    
    proxy_list = []
    for protocol, url in sources:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                lines = res.text.strip().split('\n')
                for line in lines:
                    ip_port = line.strip()
                    if ip_port:
                        proxy_list.append({"proxy": f"{protocol}://{ip_port}", "protocol": protocol})
        except Exception:
            pass
            
    print(f"[+] Berhasil mengumpulkan {len(proxy_list)} proxy Singapura.")
    return proxy_list

# --- 2. TES SANGUP TIDAKNYA PROXY MEMBUKA MEWATCH ---
def find_working_proxy(proxy_pool: List[Dict]) -> Optional[str]:
    target_url = "https://www.mewatch.sg"
    print("[+] Mengetes proxy ke mewatch.sg (Timeout 4s)...")
    
    for item in proxy_pool:
        proxy_str = item["proxy"]
        try:
            proxies = {"http": proxy_str, "https": proxy_str}
            start = time.time()
            res = requests.get(target_url, proxies=proxies, timeout=4, headers={'User-Agent': 'Mozilla/5.0'})
            if res.status_code == 200:
                ping = time.time() - start
                print(f"    ✅ PROXY AKTIF: {proxy_str} (Ping: {ping:.2f}s)")
                return proxy_str
        except Exception:
            continue
            
    print("    ❌ Tidak ada proxy gratisan yang aktif saat ini.")
    return None

def parse_drm_kid(response_bytes: bytes) -> Optional[str]:
    try:
        content_str = response_bytes.decode('utf-8', errors='ignore')
        kid_match = re.search(r'cenc:default_KID="([0-9a-fA-F\-]{32,36})"', content_str)
        if kid_match:
            return kid_match.group(1).replace('-', '').lower()
    except Exception:
        pass
    return None

# --- 3. SCRAPE DENGAN PLAYWRIGHT DENGAN PROXY HASIL AUTO-DETECT ---
def extract_channel(page_url: str, channel_name: str, active_proxy: str) -> Dict:
    result = {"channel": channel_name, "mpd_urls": [], "kids": [], "status": "Failed"}
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox'],
                proxy={"server": active_proxy}
            )
            context = browser.new_context()
            page = context.new_page()

            # Blokir aset berat agar loading proxy sangat cepat
            page.route("**/*.{png,jpg,jpeg,gif,css,woff,woff2}", lambda r: r.abort())

            def handle_response(response: Response):
                url = response.url
                if ".mpd" in url and url not in result["mpd_urls"]:
                    result["mpd_urls"].append(url)
                    try:
                        kid = parse_drm_kid(response.body())
                        if kid and kid not in result["kids"]:
                            result["kids"].append(kid)
                    except Exception:
                        pass

            page.on("response", handle_response)
            page.goto(page_url, wait_until="domcontentloaded", timeout=12000)
            time.sleep(5)

            if result["mpd_urls"]:
                result["status"] = "Success"
            browser.close()
        except Exception as e:
            result["status"] = f"Error: {e}"

    return result

def main():
    proxies = fetch_singapore_proxies()
    best_proxy = find_working_proxy(proxies)

    if not best_proxy:
        print("[!] Proses dibatalkan karena tidak menemukan proxy SG yang hidup.")
        return

    results = []
    print(f"\n[*] Menggunakan Proxy Terpilih: {best_proxy}")
    for ch in FREE_CHANNELS:
        print(f"[*] Extracting {ch['name']}...")
        data = extract_channel(ch["url"], ch["name"], best_proxy)
        results.append(data)
        print(f"    -> Status: {data['status']} | MPD: {len(data['mpd_urls'])} | KID: {data['kids']}")

    with open("mewatch_streams.json", "w") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()
