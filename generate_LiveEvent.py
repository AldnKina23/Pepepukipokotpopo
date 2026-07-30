import requests
import json
import re
from bs4 import BeautifulSoup
import time
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote
import base64

# ============================================
# CẤU HÌNH LUDA
# ============================================

BASE_URL = "https://xoilaczzuuz.tv/"
PER_PAGE = 20
OUTPUT_FILE = "LiveEvent.m3u"
MAX_PAGES_TO_FETCH = 5  # Ambil hingga 5 halaman (cukup untuk jadwal hari ini & besok)


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


def decode_m3u8_payload(text):
    match = re.search(r'https?://[^\s"\'<>\\]+\.m3u8[^\s"\'<>]*', text)
    if match:
        return match.group(0).replace('\\/', '/')

    decoded_text = unquote(text)
    match = re.search(r'https?://[^\s"\'<>\\]+\.m3u8[^\s"\'<>]*', decoded_text)
    if match:
        return match.group(0).replace('\\/', '/')

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


def extract_url_stream_from_link(link_url):
    if not link_url:
        return None
        
    if '.m3u8' in link_url and 'ajax/chanel' not in link_url:
        return link_url

    try:
        headers = build_dynamic_headers(referer_override='https://xlz.livepingscorex.com/')
        headers['X-Requested-With'] = 'XMLHttpRequest'
        
        response = requests.get(link_url, headers=headers, timeout=8)
        if response.status_code != 200:
            return link_url  # Return original link as fallback

        content = response.text

        try:
            data = response.json()
            if isinstance(data, dict):
                for key in ['url', 'stream', 'link', 'data', 'file', 'hls']:
                    val = data.get(key)
                    if val:
                        if isinstance(val, dict):
                            val = val.get('url') or val.get('file')
                        if val and '.m3u8' in str(val):
                            return str(val).replace('\\/', '/')
                        decoded = decode_m3u8_payload(str(val))
                        if decoded:
                            return decoded
        except Exception:
            pass

        extracted = decode_m3u8_payload(content)
        if extracted:
            return extracted

        # Jika belum live, kembalikan link originalnya agar playlist tidak kosong
        return link_url
    except Exception:
        return link_url


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
        
        final_urls = []
        for item in list_stream:
            if isinstance(item, list) and len(item) > 0:
                raw_stream_url = str(item[0]).replace('\\/', '/')
                resolved_url = extract_url_stream_from_link(raw_stream_url)
                if resolved_url:
                    final_urls.append(resolved_url)
                else:
                    final_urls.append(raw_stream_url)
        
        return list(dict.fromkeys(final_urls))
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
    
    # Ambil semua match tanpa membatasi berdasar BLV
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
        if match:
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
        print(f"   ✅ Page {page}: got {len(matches)} matches (Total accumulator: {len(all_matches)})")
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
            print("❌ No streams collected!")
            return False
        
        m3u_content = "#EXTM3U\n"
        m3u_content += "# Xôi Lạc TV Playlist (Hari Ini & Besok)\n"
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
        
        print(f"\n✅ M3U File berhasil dibuat: {filename}")
        print(f"   Total Pertandingan & Link Terkumpul: {len(all_streams)}")
        return True
    except Exception as e:
        print(f"❌ Error creating M3U: {e}")
        return False


def main():
    print("=" * 60)
    print(" 🚀 SCRAPE ALL MATCHES (LIVE + UPCOMING HARI INI & BESOK)")
    print("=" * 60)
    
    matches, total_pages = fetch_pages(MAX_PAGES_TO_FETCH)
    
    if matches:
        print(f"\n📊 Total pertandingan ditemukan dari {MAX_PAGES_TO_FETCH} halaman: {len(matches)}")
        create_m3u_file(matches, OUTPUT_FILE)
    else:
        print("❌ Gagal mengambil daftar pertandingan.")


if __name__ == "__main__":
    main()
