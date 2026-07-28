import os
import re
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ==========================================
# 1. BANTUAN TEKS & TUKAR NAMA VTV
# ==========================================
def remove_accents(input_str):
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    s = ''
    for c in input_str:
        s += s0[s1.index(c)] if c in s1 else c
    return s

def get_vtv_acronym(ch_name):
    clean_name = remove_accents(ch_name).lower().replace('-', ' ')
    if "vietnam today" in clean_name or "viet nam today" in clean_name:
        return "vietnamtoday"
    words = clean_name.split()
    if not words: return ""
    res = words[0] 
    for w in words[1:]:
        res += w if w.isdigit() else w[0]
    return res

# ==========================================
# 2. CAPTURE MASTER LINK VTV VIA SELENIUM & CDP
# ==========================================
def extract_vtv_master_token(proxy_ip=None, protocol="http"):
    print("\n[VTV] 🚀 Memulai pencarian Master Link VTV1...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.page_load_strategy = 'eager'

    # Aktifkan Network Logging untuk membaca CDP
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    if proxy_ip:
        chrome_options.add_argument(f'--proxy-server={protocol}://{proxy_ip}')

    driver = None
    master_link = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Bypass deteksi bot/webdriver
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

        target_url = "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv1-1.html"
        print(f"   -> Mengakses {target_url}...")
        driver.get(target_url)

        # Trigger auto-play video jika tertahan
        driver.execute_script("let v = document.querySelector('video'); if(v) { v.muted = true; v.play(); }")
        
        # Sniffing paket jaringan selama max 12 detik
        start_time = time.time()
        while time.time() - start_time < 12:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    message = json.loads(entry['message'])['message']
                    if message['method'] == 'Network.requestWillBeSent':
                        req_url = message['params']['request']['url']
                        if '.m3u8' in req_url and 'vtv' in req_url.lower():
                            master_link = req_url
                            print(f"   ✅ BERHASIL! Master Link VTV Ditangkap:\n   {master_link}")
                            break
                except Exception:
                    continue
            if master_link:
                break
            time.sleep(1)

    except Exception as e:
        print(f"   ❌ Gagal mengambil Master Link VTV: {e}")
    finally:
        if driver:
            driver.quit()

    return master_link

# ==========================================
# 3. INTERPOLASI VTV MASTER TOKEN KE DAFTAR KANAL
# ==========================================
def generate_vtv_channels(master_link, channel_names):
    channels_result = []
    if not master_link:
        return channels_result

    print("\n[VTV] 🔄 Menggenerasi link untuk semua saluran VTV...")
    for ch_name in channel_names:
        folder_id = get_vtv_acronym(ch_name)
        is_sctv = 'sctv' in ch_name.lower()

        if is_sctv:
            token_match = re.search(r'\.vn/([^/]+/[^/]+)/', master_link)
            if token_match:
                tokens = token_match.group(1)
                new_url = f"https://vtvgolive-sctvdrm.vtvdigital.vn/{tokens}/manifest/{folder_id}/master.m3u8"
            else:
                new_url = re.sub(r'(/manifest/|/live/)[^/]+(/)', f'\\g<1>{folder_id}\\g<2>', master_link)
        else:
            new_url = re.sub(r'(/manifest/|/live/)[^/]+(/)', f'\\g<1>{folder_id}\\g<2>', master_link)

        channels_result.append({
            'name': ch_name,
            'group': 'Kênh VTV',
            'url': new_url
        })
        print(f"   -> {ch_name} -> {new_url}")

    return channels_result

# ==========================================
# 4. EXPORT FILE PLAYLIST M3U
# ==========================================
def export_to_m3u(channels, output_filename="vn.m3u"):
    print(f"\n[EXPORT] 📝 Menulis data ke {output_filename}...")
    m3u_content = "#EXTM3U\n"
    for ch in channels:
        m3u_content += f'#EXTINF:-1 tvg-id="{ch["name"]}" group-title="{ch["group"]}", {ch["name"]}\n'
        m3u_content += f'{ch["url"]}\n'

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"🎉 Selesai! Playlist disimpan di '{output_filename}'.")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # Daftar saluran VTV yang akan di-generasi otomatis
    vtv_channels_to_build = ["VTV1", "VTV2", "VTV3", "VTV4", "VTV5", "VTV7", "VTV8", "VTV9", "VTV Cần Thơ"]

    # 1. Ekstrak Master Token via VTV1
    master_vtv_link = extract_vtv_master_token()

    # 2. Jika di-run di local/server luar tanpa proxy dan gagal, kamu bisa memasukkan IP Proxy VN di parameter
    # master_vtv_link = extract_vtv_master_token(proxy_ip="160.22.17.4:9988", protocol="socks5")

    # 3. Generasi saluran otomatis jika master link didapat
    if master_vtv_link:
        playlist_data = generate_vtv_channels(master_vtv_link, vtv_channels_to_build)
        export_to_m3u(playlist_data, "vn.m3u")
    else:
        print("❌ Gagal mengekstrak token. Pastikan koneksi/proxy Vietnam terhubung.")
