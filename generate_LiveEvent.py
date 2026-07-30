import requests
import json
import re
from bs4 import BeautifulSoup
import time
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse
import base64

# ============================================
# CẤU HÌNH klot
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


def build_dynamic_headers():
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
        "referer": actual_url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }


def generate_cdn_stream_urls(channel_id):
    """
    Menghasilkan variasi link CDN berdasarkan pola yang didapat dari DevTools
    """
    if not channel_id:
        return []
    
    # Pastikan format channel bersih (contoh: channel16)
    clean_channel = channel_id.lower().strip()
    
    urls = [
        # Format Provider 1 (Statis Direct Pulse 1)
        f"https://live1.streambylivepulse.com/live/{clean_channel}/playlist.m3u8",
        # Format Provider 1 (Statis Direct Pulse 2)
        f"https://live2.streambylivepulse.com/live/{clean_channel}.m3u8",
        # Format Provider 2 (Direct 100ycdn)
        f"https://live1.100ycdn.com/live/{clean_channel}/playlist.m3u8",
        # Format Alternative Stream
        f"https://live2.streambylivepulse.com/live/{clean_channel}/playlist.m3u8"
    ]
    return urls


def extract_channels_from_detail_page(url):
    """Mencari channel ID (channel1, channel2, dll) dari script detail pertandingan"""
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
        
        found_channels = []
        for item in list_stream:
            if isinstance(item, list) and len(item) > 0:
                raw_url = str(item[0])
                # Cari pola "channelXX" di dalam URL AJAX
                ch_match = re.search(r'channel\d+', raw_url, re.IGNORECASE)
                if ch_match:
                    found_channels.append(ch_match.group(0))
        
        return list(dict.fromkeys(found_channels))
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
        'title': title,
        'streams': []
    }
    
    if href:
        full_url = actual_base + href
        channels = extract_channels_from_detail_page(full_url)
        
        stream_list = []
        for ch in channels:
            cdn_links = generate_cdn_stream_urls(ch)
            for cdn_url in cdn_links:
                stream_list.append({
                    'channel': ch,
                    'url': cdn_url
                })
        match['streams'] = stream_list
    
    return match


def parse_all_matches(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    items = soup.select('.grid-matches__item-match')
    
    matches = []
    for item in items:
        match = parse_match_from_element(item)
        if match and match['streams']:
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
        print(f"   ✅ Page {page}: dapet {len(matches)} pertandingan berkanal (Total: {len(all_matches)})")
        time.sleep(0.3)
        
    return all_matches, total_pages


def create_m3u_file(matches, filename="LiveEvent.m3u"):
    try:
        all_entries = []
        
        for match in matches:
            time_str = extract_time_from_title(match['title'])
            date_str = extract_date_from_title(match['title'])
            
            display_title = match['title']
            clean_title = re.sub(r'lúc\s+\d{2}:\d{2}\s+', '', display_title)
            clean_title = re.sub(r'ngày\s+\d{2}/\d{2}/\d{4}', '', clean_title).strip()
            
            prefix = "🔴 LIVE | " if match['live'] == 'living' else "⏳ "
            if match['hot']:
                prefix += "🔥 "
            
            base_title = f"{prefix}{time_str} {clean_title}"
            if date_str and date_str not in base_title:
                base_title += f" ({date_str})"
            
            for idx, stream in enumerate(match['streams'], 1):
                # Memberi label Server/Provider pada nama channel IPTV
                srv_num = (idx % 4) or 4
                stream_title = f"{base_title} [CH: {stream['channel'].upper()} - Srv {srv_num}]"
                
                all_entries.append({
                    'title': stream_title,
                    'url': stream['url'],
                    'live': match['live']
                })
        
        if not all_entries:
            print("⚠️ Tidak ada stream yang terkumpul.")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n# No Streams Available\n")
            return False
        
        m3u_content = "#EXTM3U\n"
        m3u_content += "# Xôi Lạc TV Multi-CDN Playlist\n"
        m3u_content += f"# Total streams: {len(all_entries)}\n"
        m3u_content += f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for entry in all_entries:
            group_label = "Xôi Lạc - LIVE NOW" if entry["live"] == "living" else "Xôi Lạc - UPCOMING"
            m3u_content += f'#EXTINF:-1 group-title="{group_label}",{entry["title"]}\n'
            m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36\n'
            m3u_content += '#EXTVLCOPT:http-referrer=https://xlz.livepingscorex.com/\n'
            m3u_content += f'{entry["url"]}\n\n'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"\n✅ File M3U Berhasil Dibuat: {filename}")
        print(f"   Total Link M3U8 Multi-Server Terkumpul: {len(all_entries)}")
        return True
    except Exception as e:
        print(f"❌ Error creating M3U: {e}")
        return False


def main():
    print("=" * 60)
    print(" 🚀 SCRAPE MULTI-CDN M3U8 STREAMS FOR IPTV")
    print("=" * 60)
    
    matches, total_pages = fetch_pages(MAX_PAGES_TO_FETCH)
    
    if matches:
        create_m3u_file(matches, OUTPUT_FILE)
    else:
        print("❌ Gagal mengumpulkan jadwal pertandingan.")


if __name__ == "__main__":
    main()
