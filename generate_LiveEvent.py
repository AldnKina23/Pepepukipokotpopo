import requests
import json
import re
from bs4 import BeautifulSoup
import time
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse

# ============================================
# CONFIG mai
# ============================================

BASE_URL = "https://xoilaczzvvz.tv/"
PER_PAGE = 30
OUTPUT_FILE = "LiveEvent.m3u"


# ============================================
# GET ACTUAL BASE URL
# ============================================
def get_actual_base_url():
    try:
        response = requests.get(BASE_URL, allow_redirects=True, timeout=10)
        actual_url = response.url
        if not actual_url.endswith('/'):
            actual_url += '/'
        return actual_url
    except Exception as e:
        print(f"⚠️ Cannot get actual URL: {e}")
        if not BASE_URL.endswith('/'):
            return BASE_URL + '/'
        return BASE_URL


# ============================================
# BUILD DYNAMIC HEADERS
# ============================================
def build_dynamic_headers():
    actual_url = get_actual_base_url()
    parsed = urlparse(actual_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    return {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,vi;q=0.8",
        "cache-control": "no-cache",
        "origin": domain,
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": actual_url,
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    }


# ============================================
# EXTRACT M3U8 STREAM WITH AUTH TOKENS
# ============================================
def extract_url_stream_from_link(link_url):
    try:
        headers = build_dynamic_headers()
        headers['referer'] = 'https://xlz.livepingscorex.com/'
        
        response = requests.get(link_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        # 1. Check if response is JSON containing direct m3u8 link or play object
        try:
            data = response.json()
            if isinstance(data, dict):
                stream_url = data.get('data') or data.get('url') or data.get('stream') or data.get('link')
                if stream_url and '.m3u8' in str(stream_url):
                    return str(stream_url).replace('\\/', '/')
        except Exception:
            pass

        content = response.text
        
        # 2. Search for full m3u8 URL with query params (wsSecret / auth_key)
        m3u8_token_match = re.search(r'https?://[^\s"\']+\.m3u8\?[^\s"\']+', content)
        if m3u8_token_match:
            return m3u8_token_match.group(0).replace('\\/', '/')

        # 3. Search for standard m3u8 URL without query params
        m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8', content)
        if m3u8_match:
            return m3u8_match.group(0).replace('\\/', '/')

        # 4. Search for js variable var urlStream
        match = re.search(r'var\s+urlStream\s*=\s*["\']([^"\']+)["\'];', content)
        if match:
            return match.group(1).replace('\\/', '/')

        return None
    except Exception:
        return None


# ============================================
# EXTRACT STREAM LINKS FROM DETAIL PAGE
# ============================================
def extract_stream_links(url):
    try:
        headers = build_dynamic_headers()
        response = requests.get(url, headers=headers, timeout=20)
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
                stream_url = str(item[0]).replace('\\/', '/')
                url_stream = extract_url_stream_from_link(stream_url)
                if url_stream:
                    final_urls.append(url_stream)
                else:
                    final_urls.append(stream_url)
        
        return list(dict.fromkeys(final_urls))
    except Exception:
        return []


# ============================================
# TITLE PARSERS
# ============================================
def extract_time_from_title(title):
    try:
        time_match = re.search(r'lúc\s+(\d{2}):(\d{2})', title)
        if time_match:
            return f"{time_match.group(1)}:{time_match.group(2)}"
        return ""
    except Exception:
        return ""


def extract_date_from_title(title):
    try:
        date_match = re.search(r'ngày\s+(\d{2})/(\d{2})/(\d{4})', title)
        if date_match:
            return f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
        return ""
    except Exception:
        return ""


# ============================================
# PARSE MATCH ELEMENT
# ============================================
def parse_match_from_element(item):
    link = item.select_one('a.redirectPopup')
    if not link:
        return None
    
    href = link.get('href', '')
    title = link.get('title', '')
    
    # Ambil kompetisi/liga jika ada
    league_elem = item.select_one('.grid-match-item__league')
    league_title = league_elem.text.strip() if league_elem else ""

    actual_base = get_actual_base_url().rstrip('/')
    
    match = {
        'fid': item.get('data-fid', ''),
        'hot': item.get('data-hot', '0') == '1',
        'href': href,
        'title': title,
        'league': league_title
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


# ============================================
# FETCH TRẬN HOT PAGE
# ============================================
def fetch_hot_matches():
    actual_base = get_actual_base_url().rstrip('/')
    # URL Khusus Trận Hot (Laga Penting)
    url = f"{actual_base}/sport/football/load-more/hot/page/0/per/{PER_PAGE}?t={int(time.time())}"
    
    try:
        print(f"📤 Fetching HOT Matches: {url}")
        headers = build_dynamic_headers()
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            html_content = data.get('data', {}).get('html', '')
            matches = parse_all_matches(html_content)
            return matches
        else:
            print(f"❌ Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []


# ============================================
# CREATE M3U PLAYLIST
# ============================================
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
                    
                    new_title = "🔥 "
                    if time_str:
                        new_title += f"[{time_str}] "
                    
                    if match.get('league'):
                        new_title += f"({match['league']}) "

                    new_title += clean_title
                    
                    if date_str and date_str not in new_title:
                        new_title += f" - {date_str}"
                    
                    all_streams.append({
                        'title': new_title,
                        'url': stream_url
                    })
        
        if not all_streams:
            print("❌ No HOT stream links found!")
            return False
        
        m3u_content = "#EXTM3U\n"
        m3u_content += "# Xôi Lạc TV HOT Matches Playlist\n"
        m3u_content += f"# Total streams: {len(all_streams)}\n"
        m3u_content += f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for stream in all_streams:
            m3u_content += f'#EXTINF:-1 group-title="Xôi Lạc HOT Event",{stream["title"]}\n'
            m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36\n'
            m3u_content += '#EXTVLCOPT:http-referrer=https://xlz.livepingscorex.com/\n'
            m3u_content += f'{stream["url"]}\n\n'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"✅ HOT M3U file created: {filename}")
        print(f"   Total valid streams: {len(all_streams)}")
        return True
    except Exception as e:
        print(f"❌ Error creating M3U: {e}")
        return False


# ============================================
# MAIN
# ============================================
def main():
    print("=" * 60)
    print("        🚀 FETCH HOT MATCHES ONLY (Trận Hot)")
    print("=" * 60)
    
    matches = fetch_hot_matches()
    
    if matches:
        print(f"\n📊 Found {len(matches)} HOT matches.")
        for i, m in enumerate(matches[:5], 1):
            print(f"  {i}. {m['title']}")
        
        print("\n📊 Creating M3U playlist...")
        create_m3u_file(matches, OUTPUT_FILE)
        print("\n✅ DONE!")
    else:
        print("❌ No HOT matches available at the moment.")


if __name__ == "__main__":
    main()
