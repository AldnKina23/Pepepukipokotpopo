import requests
import json
import re
from bs4 import BeautifulSoup
import time
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote, parse_qs
import base64

# ============================================
# CẤU HÌNH pokot
# ============================================

BASE_URL = "https://xoilaczzuuz.tv/"
PER_PAGE = 20
OUTPUT_FILE = "LiveEvent.m3u"
MAX_PAGES_TO_FETCH = 5


def get_actual_base_url():
    try:
        response = requests.get(BASE_URL, allow_redirects=True, timeout=10)
        actual_url = response.url
        if not actual_url.endswith('/'):
            actual_url += '/'
        return actual_url
    except Exception:
        if not BASE_URL.endswith('/'):
            return BASE_URL + '/'
        return BASE_URL


def build_dynamic_headers(referer_override=None):
    actual_url = get_actual_base_url()
    parsed = urlparse(actual_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    return {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9,id;q=0.8",
        "cache-control": "no-cache",
        "origin": domain,
        "pragma": "no-cache",
        "referer": referer_override if referer_override else actual_url,
        "sec-ch-ua": '"Chromium";v="122", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }


def find_m3u8_in_text(text):
    """Mencari pola URL .m3u8 dalam string mentah, URL-encoded, atau Base64"""
    if not text:
        return None

    # 1. Regex M3U8 standar (Termasuk 100ycdn & streambylivepulse)
    match = re.search(r'https?://[^\s"\'<>\\]+\.m3u8[^\s"\'<>]*', text)
    if match:
        return match.group(0).replace('\\/', '/')

    # 2. Decode URL Encoding (%3A%2F%2F)
    decoded_text = unquote(text)
    match = re.search(r'https?://[^\s"\'<>\\]+\.m3u8[^\s"\'<>]*', decoded_text)
    if match:
        return match.group(0).replace('\\/', '/')

    # 3. Decode String Base64
    b64_matches = re.findall(r'[A-Za-z0-9+/=]{30,}', text)
    for b64_str in b64_matches:
        try:
            decoded_b64 = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
            if '.m3u8' in decoded_b64:
                m3u_match = re.search(r'https?://[^\s"\'<>\\]+\.m3u8[^\s"\'<>]*', decoded_b64)
                if m3u_match:
                    return m3u_match.group(0).replace('\\/', '/')
        except Exception:
            continue
    return None


def fetch_m3u8_from_ajax_endpoint(ajax_url):
    """
    Mengekstrak M3U8 langsung dari Player Endpoint Xoilac
    """
    if not ajax_url:
        return None

    if '.m3u8' in ajax_url and 'ajax/chanel' not in ajax_url:
        return ajax_url

    try:
        headers = build_dynamic_headers(referer_override='https://xlz.livepingscorex.com/')
        headers['X-Requested-With'] = 'XMLHttpRequest'
        
        # 1. Request ke halaman embed AJAX
        res = requests.get(ajax_url, headers=headers, timeout=10)
        if res.status_code != 200:
            return None

        content = res.text

        # Cari M3U8 langsung di HTML/JS
        extracted = find_m3u8_in_text(content)
        if extracted:
            return extracted

        # 2. Jika disembunyikan dalam iframe / API internal
        # Cari URL iframe atau API source di dalam script
        iframe_src = re.search(r'iframe\s+src=["\']([^"\']+)["\']', content)
        if iframe_src:
            sub_url = iframe_src.group(1)
            if sub_url.startswith('//'):
                sub_url = 'https:' + sub_url
            sub_res = requests.get(sub_url, headers=headers, timeout=10)
            if sub_res.status_code == 200:
                extracted_sub = find_m3u8_in_text(sub_res.text)
                if extracted_sub:
                    return extracted_sub

        # 3. Cari variabel player seperti: source: "...", file: "..."
        source_match = re.search(r'(?:source|file|stream|url)\s*:\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        if source_match:
            candidate = source_match.group(1).replace('\\/', '/')
            m3u_found = find_m3u8_in_text(candidate)
            if m3u_found:
                return m3u_found

        # 4. Fallback Generator (Gunakan channel ID dari URL untuk menyusun stream link)
        # Contoh URL AJAX: .../link/channel6
        channel_match = re.search(r'channel\d+', ajax_url)
        if channel_match:
            channel_id = channel_match.group(0)
            # Konstruksi URL fallback sesuai skema CDN Xoilac
            fallback_cdn = f"https://live1.streambylivepulse.com/live/{channel_id}/playlist.m3u8"
            return fallback_cdn

    except Exception as e:
        print(f"⚠️ Error mengekstrak {ajax_url}: {e}")
        
    return None


def extract_stream_links(url):
    try:
        headers = build_dynamic_headers()
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.select('script')
        
        list_stream_script = None
        for script in scripts:
            html_content = script.string if script.string else script.get_text()
            if html_content and 'var list_stream' in html_content:
                list_stream_script = html_content
                break
        
        if not list_stream_script:
            return []
        
        pattern = r'var\s+list_stream\s*=\s*(\[.*?\]);'
        match = re.search(pattern, list_stream_script, re.DOTALL)
        if not match:
            return []
        
        list_stream_str = match.group(1)
        try:
            list_stream = json.loads(list_stream_str)
        except json.JSONDecodeError:
            return []
        
        final_m3u8_urls = []
        for item in list_stream:
            if isinstance(item, list) and len(item) > 0:
                raw_url = str(item[0]).replace('\\/', '/')
                
                # Resolusi link AJAX ke link CDN .m3u8 asli
                real_m3u8 = fetch_m3u8_from_ajax_endpoint(raw_url)
                if real_m3u8:
                    final_m3u8_urls.append(real_m3u8)
        
        return list(dict.fromkeys(final_m3u8_urls))
    except Exception:
        return []


def get_live_status_from_title(title):
    try:
        time_match = re.search(r'lúc\s+(\d{2}):(\d{2})', title)
        if not time_match:
            return 'comming'
        
        hour, minute = int(time_match.group(1)), int(time_match.group(2))
        
        date_match = re.search(r'ngày\s+(\d{2})/(\d{2})/(\d{4})', title)
        if not date_match:
            return 'comming'
        
        day, month, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        
        match_time = datetime(year, month, day, hour, minute)
        now = datetime.now()
        
        if now < match_time:
            return 'comming'
        elif now >= match_time and now < match_time + timedelta(minutes=120):
            return 'living'
        else:
            return 'end'
    except Exception:
        return 'comming'


def extract_time_from_title(title):
    try:
        time_match = re.search(r'lúc\s+(\d{2}):(\d{2})', title)
        return f"{time_match.group(1)}:{time_match.group(2)}" if time_match else "00:00"
    except Exception:
        return "00:00"


def extract_date_from_title(title):
    try:
        date_match = re.search(r'ngày\s+(\d{2})/(\d{2})/(\d{4})', title)
        return f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}" if date_match else ""
    except Exception:
        return ""


def parse_match_from_element(item):
    link = item.select_one('a.redirectPopup')
    if not link:
        return None
    
    href = link.get('href', '')
    title = link.get('title', '')
    
    live_status = get_live_status_from_title(title)
    actual_base = get_actual_base_url().rstrip('/')
    
    match = {
        'fid': item.get('data-fid', ''),
        'hot': item.get('data-hot', '0') == '1',
        'live': live_status,
        'href': href,
        'title': title
    }
    
    if href:
        full_url = actual_base + href
        stream_links = extract_stream_links(full_url)
        if stream_links:
            for i, stream_url in enumerate(stream_links, 1):
                match[f'link{i}'] = stream_url
    
    return match


def parse_all_matches(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    items = soup.select('.grid-matches__item-match')
    
    matches = []
    for item in items:
        match = parse_match_from_element(item)
        if match and any(k.startswith('link') for k in match.keys()):
            matches.append(match)
    return matches


def fetch_page(page):
    actual_base = get_actual_base_url().rstrip('/')
    url = f"{actual_base}/sport/football/load-more/home/page/{page}/per/{PER_PAGE}?t={int(time.time())}"
    
    try:
        print(f"📤 GET page {page}: {url}")
        headers = build_dynamic_headers()
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            pagination = data.get('data', {}).get('pagination', {})
            html_content = data.get('data', {}).get('html', '')
            matches = parse_all_matches(html_content)
            
            return {
                'success': data.get('success', False),
                'data': {
                    'pagination': pagination,
                    'matches': matches
                }
            }
        return None
    except Exception as e:
        print(f"❌ Exception page {page}: {e}")
        return None


def fetch_pages(max_pages):
    all_matches = []
    total_pages = 0
    
    for page in range(0, max_pages):
        result = fetch_page(page)
        if not result or not result.get('success'):
            break
            
        if page == 0:
            total_pages = result['data']['pagination'].get('total_pages', 0)
            
        matches = result['data'].get('matches', [])
        all_matches.extend(matches)
        print(f"   ✅ Page {page}: got {len(matches)} matches with active CDN .m3u8 (Total: {len(all_matches)})")
        time.sleep(0.3)
        
    return all_matches, total_pages


def create_m3u_file(matches, filename="LiveEvent.m3u"):
    try:
        all_streams = []
        
        for match in matches:
            link_keys = [k for k in match.keys() if k.startswith('link')]
            for key in link_keys:
                stream_url = match[key]
                if stream_url and stream_url.startswith('http'):
                    time_str = extract_time_from_title(match['title'])
                    date_str = extract_date_from_title(match['title'])
                    
                    display_title = match['title']
                    clean_title = re.sub(r'lúc\s+\d{2}:\d{2}\s+', '', display_title)
                    clean_title = re.sub(r'ngày\s+\d{2}/\d{2}/\d{4}', '', clean_title).strip()
                    
                    prefix = "🔴 LIVE | " if match['live'] == 'living' else "⏳ "
                    if match['hot']:
                        prefix += "🔥 "
                    
                    new_title = f"{prefix}{time_str} {clean_title}"
                    if date_str and date_str not in new_title:
                        new_title += f" ({date_str})"
                    
                    all_streams.append({
                        'title': new_title,
                        'url': stream_url,
                        'live': match['live']
                    })
        
        if not all_streams:
            print("⚠️ Tidak ada link .m3u8 aktif yang berhasil diekstrak.")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n# No Active Streams Available\n")
            return False
        
        m3u_content = "#EXTM3U\n"
        m3u_content += "# Xôi Lạc TV Playlist\n"
        m3u_content += f"# Total streams: {len(all_streams)}\n"
        m3u_content += f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for stream in all_streams:
            group_label = "Xôi Lạc - LIVE NOW" if stream["live"] == "living" else "Xôi Lạc - UPCOMING"
            m3u_content += f'#EXTINF:-1 group-title="{group_label}",{stream["title"]}\n'
            m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36\n'
            m3u_content += '#EXTVLCOPT:http-referrer=https://xlz.livepingscorex.com/\n'
            m3u_content += f'{stream["url"]}\n\n'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"\n✅ File M3U Berhasil Dibuat: {filename}")
        print(f"   Total Link CDN M3U8 Siap Putar: {len(all_streams)}")
        return True
    except Exception as e:
        print(f"❌ Error creating M3U: {e}")
        return False


def main():
    print("=" * 60)
    print(" 🚀 SCRAPE PURE CDN M3U8 STREAMS FOR IPTV")
    print("=" * 60)
    
    matches, total_pages = fetch_pages(MAX_PAGES_TO_FETCH)
    
    if matches:
        create_m3u_file(matches, OUTPUT_FILE)
    else:
        print("❌ Gagal mengekstrak link .m3u8.")


if __name__ == "__main__":
    main()
