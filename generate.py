import requests
import re
import os
from io import BytesIO
from datetime import datetime
import pytz
from PIL import Image

API_URL = "https://raw.githubusercontent.com/sm-monirulislam/Upcoming-and-Live-Sports-Data/refs/heads/main/Sports_data.json"
POSTER_DIR = "posters"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def create_combined_poster(logo1_url, logo2_url, output_path):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res1 = requests.get(logo1_url, headers=headers, timeout=10) if logo1_url else None
        res2 = requests.get(logo2_url, headers=headers, timeout=10) if logo2_url else None

        if not res1 or res1.status_code != 200 or not res2 or res2.status_code != 200:
            return False

        img1 = Image.open(BytesIO(res1.content)).convert('RGBA')
        img2 = Image.open(BytesIO(res2.content)).convert('RGBA')

        bg1 = Image.new("RGB", img1.size, (255, 255, 255))
        bg1.paste(img1, mask=img1.split()[3] if len(img1.split()) == 4 else None)
        bg2 = Image.new("RGB", img2.size, (255, 255, 255))
        bg2.paste(img2, mask=img2.split()[3] if len(img2.split()) == 4 else None)

        size = (300, 300)
        bg1 = bg1.resize(size, Image.Resampling.LANCZOS)
        bg2 = bg2.resize(size, Image.Resampling.LANCZOS)

        canvas = Image.new('RGB', (700, 300), color=(0, 0, 0))
        canvas.paste(bg1, (0, 0))
        canvas.paste(bg2, (400, 0))

        canvas.save(output_path, "JPEG", quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"Error creating poster: {e}")
        return False

os.makedirs(POSTER_DIR, exist_ok=True)

try:
    data = requests.get(API_URL, timeout=30).json()
except Exception as e:
    print(f"Error fetching API: {e}")
    exit(1)

bd_time = datetime.now(pytz.timezone('Asia/Dhaka')).strftime('%Y-%m-%d %I:%M:%S %p')
stream_blocks = []

for match in data.get("matches", []):
    category = match.get("Category", "Sports")
    event_name = match.get("event_name", "Live Event")
    
    event_info = match.get("eventInfo") or {}
    logoA = event_info.get("teamAFlag", "")
    logoB = event_info.get("teamBFlag", "")

    safe_name = sanitize_filename(event_name)
    poster_filename = f"{safe_name}.jpg"
    poster_path = os.path.join(POSTER_DIR, poster_filename)

    if logoA and logoB:
        if create_combined_poster(logoA, logoB, poster_path):
            final_logo = poster_path
        else:
            final_logo = logoA
    else:
        final_logo = logoA or logoB

    for stream in match.get("streams", []):
        stream_name = stream.get("name", "")
        raw_url = stream.get("stream_url", "")
        drm_key = stream.get("drm_key", "")

        if not raw_url:
            continue

        parts = raw_url.split('|')
        clean_url = parts[0].strip()
        headers = parts[1] if len(parts) > 1 else ""

        display_name = f"{event_name} - {stream_name}" if stream_name else event_name

        block = [f'#EXTINF:-1 tvg-logo="{final_logo}" group-title="{category}", {display_name}']

        if headers:
            params = dict(re.findall(r'([^&=]+)=([^&]+)', headers))
            referer = params.get('Referer') or params.get('referer') or params.get('Origin') or params.get('origin')
            user_agent = params.get('User-Agent') or params.get('user-agent')

            if referer:
                block.append(f'#EXTVLCOPT:http-referrer={referer}')
            if user_agent:
                block.append(f'#EXTVLCOPT:http-user-agent={user_agent}')

        if drm_key:
            block.append('#KODIPROP:inputstream.adaptive.license_type=clearkey')
            block.append(f'#KODIPROP:inputstream.adaptive.license_key={drm_key}')

        block.append(clean_url)
        stream_blocks.append("\n".join(block))

header = f"""#EXTM3U
#=================================
#  Developed by: Monirul Islam
#  Telegram: https://t.me/monirul_Islam_SM
#  Telegram channel : https://t.me/sm_iptv_bd
#  Last Updated: {bd_time} (BD Time)
#  Channels Count: {len(stream_blocks)}
#================================="""

header = "\n".join([line.strip() for line in header.split("\n")])

with open("Sports_data.m3u", "w", encoding="utf-8") as f:
    f.write(header + "\n\n" + "\n\n".join(stream_blocks))

print("Sports_data.m3u and posters generated successfully!")
