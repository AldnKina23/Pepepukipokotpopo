import os
import re
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ==========================================
# 1. MODUL PROXY AUTOMATION (OPTIMIZED) al
# ==========================================
def check_local_ip_is_vn():
    print("[INIT] 🔎 Memeriksa IP asal runner...")
    try:
        res = requests.get("http://ip-api.com/json/", timeout=5).json()
        if res.get("countryCode") == "VN":
            print(f"   -> 🇻🇳 IP kamu adalah Vietnam ({res.get('query')}). Berjalan langsung!")
            return True
        else:
            print(f"   -> 🌍 IP kamu adalah {res.get('countryCode')} ({res.get('query')}). Mengaktifkan Proxy Vietnam.")
            return False
    except Exception as e:
        print(f"   -> ⚠️ Lỗi check IP: {e}. Mặc định mengaktifkan Proxy.")
        return False

def get_free_vn_proxies():
    print("[PROXY] 📥 Mengambil daftar Proxy Vietnam gratis dari ProxyScrape...")
    raw_pool = []
    sources = [
        ("socks5", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=ipport&format=text&protocol=socks5&anonymity=elite&country=vn&timeout=10000"),
        ("http", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=ipport&format=text&protocol=http&anonymity=elite&country=vn&timeout=10000"),
    ]
    for protocol, url in sources:
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if res.status_code == 200:
                for line in res.text.split('\n'):
                    ip_port = line.strip()
                    if ip_port:
                        raw_pool.append({'ip': ip_port, 'protocol': protocol})
        except Exception as e:
            print(f"   ⚠️ Gagal mengambil proxy {protocol}: {e}")
    return raw_pool

def test_proxy(ip_port, protocol, target_url="https://vtvgo.vn"):
    try:
        proxies = {"http": f"{protocol}://{ip_port}", "https": f"{protocol}://{ip_port}"}
        start = time.time()
        res = requests.get(target_url, proxies=proxies, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        if res.status_code == 200:
            return time.time() - start
    except Exception:
        pass
    return None

def find_best_proxy(proxy_list):
    print("[PROXY] ⚡ Mengetes kecepatan proxy ke VTVGo...")
    best_ip, best_proto, best_ping = None, "http", 999
    for p in proxy_list:
        ping = test_proxy(p['ip'], p['protocol'])
        if ping is not None:
            print(f"   -> ✅ Sống: {p['ip']} ({p['protocol']}) - Ping: {ping:.2f}s")
            # Utamakan proxy berkecepatan di bawah 2.5s agar Selenium tidak timeout
            if ping < 2.5 and ping < best_ping:
                best_ping, best_ip, best_proto = ping, p['ip'], p['protocol']
                print(f"   ⚡ Proxy cepat dipilih: {p['ip']}")
                return p['ip'], p['protocol']
            
            if ping < best_ping:
                best_ping, best_ip, best_proto = ping, p['ip'], p['protocol']

    if best_ip:
        print(f"   🏆 Terpilih Proxy Terbaik: {best_ip} ({best_proto}) - Ping: {best_ping:.2f}s")
    return best_ip, best_proto

# ==========================================
# 2. MODUL CAPTURE MASTER TOKEN VTV VIA CDP
# ==========================================
def extract_vtv_master_token(proxy_ip=None, protocol="http"):
    print("\n[SELENIUM] 🚀 Membuka Chrome Headless & Network Sniffer...")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.page_load_strategy = 'eager'
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    if proxy_ip:
        print(f"   -> Menggunakan Proxy: {protocol}://{proxy_ip}")
        chrome_options.add_argument(f'--proxy-server={protocol}://{proxy_ip}')

    driver = None
    master_link = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(35) # Tambah durasi timeout halaman

        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

        target_url = "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv1-1.html"
        print(f"   -> Membuka Halaman: {target_url}")
        
        try:
            driver.get(target_url)
        except Exception as e:
            print(f"   ⚠️ Halaman lambat dimuat ({e}), melanjutkan inspeksi jaringan...")

        driver.execute_script("let v = document.querySelector('video'); if(v) { v.muted = true; v.play(); }")

        # Sniffing paket jaringan CDP hingga 25 detik
        start_time = time.time()
        while time.time() - start_time < 25:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    message = json.loads(entry['message'])['message']
                    if message['method'] == 'Network.requestWillBeSent':
                        req_url = message['params']['request']['url']
                        if '.m3u8' in req_url and 'vtv' in req_url.lower():
                            master_link = req_url
                            print(f"\n🎉 SUCCESS! Master Token VTV Ditangkap:\n   {master_link}\n")
                            break
                except Exception:
                    continue
            if master_link:
                break
            time.sleep(1)

    except Exception as e:
        print(f"   ❌ Gagal menangkap stream VTV: {e}")
    finally:
        if driver:
            driver.quit()

    return master_link

# ==========================================
# 3. MODUL GENERATE PLAYLIST M3U
# ==========================================
def remove_accents(input_str):
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    return ''.join([s0[s1.index(c)] if c in s1 else c for c in input_str])

def get_vtv_acronym(ch_name):
    clean_name = remove_accents(ch_name).lower().replace('-', ' ')
    if "vietnam today" in clean_name: return "vietnamtoday"
    words = clean_name.split()
    if not words: return ""
    res = words[0]
    for w in words[1:]:
        res += w if w.isdigit() else w[0]
    return res

def build_and_export_m3u(master_link, channel_list, filename="vn.m3u"):
    print(f"[EXPORT] 📝 Membuat file playlist {filename}...")
    m3u_content = "#EXTM3U\n"
    
    for ch in channel_list:
        folder_id = get_vtv_acronym(ch)
        is_sctv = 'sctv' in ch.lower()

        if is_sctv:
            token_match = re.search(r'\.vn/([^/]+/[^/]+)/', master_link)
            if token_match:
                tokens = token_match.group(1)
                new_url = f"https://vtvgolive-sctvdrm.vtvdigital.vn/{tokens}/manifest/{folder_id}/master.m3u8"
            else:
                new_url = re.sub(r'(/manifest/|/live/)[^/]+(/)', f'\\g<1>{folder_id}\\g<2>', master_link)
        else:
            new_url = re.sub(r'(/manifest/|/live/)[^/]+(/)', f'\\g<1>{folder_id}\\g<2>', master_link)

        m3u_content += f'#EXTINF:-1 tvg-id="{ch}" group-title="Kênh VTV", {ch}\n'
        m3u_content += f'{new_url}\n'

    with open(filename, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"✅ Selesai! File {filename} berhasil diperbarui.")

# ==========================================
# EKSEKUSI UTAMA
# ==========================================
if __name__ == "__main__":
    vtv_channels = ["VTV1", "VTV2", "VTV3", "VTV4", "VTV5", "VTV7", "VTV8", "VTV9", "VTV Cần Thơ"]
    
    proxy_ip, protocol = None, "http"
    if not check_local_ip_is_vn():
        proxy_pool = get_free_vn_proxies()
        if proxy_pool:
            proxy_ip, protocol = find_best_proxy(proxy_pool)

    master_url = extract_vtv_master_token(proxy_ip=proxy_ip, protocol=protocol)

    if master_url:
        build_and_export_m3u(master_url, vtv_channels, "vn.m3u")
    else:
        print("❌ Gagal mendapatkan Master Link. Pembaruan dibatalkan.")
        exit(1) # Beri sinyal error agar step Actions tahu scraper gagal
