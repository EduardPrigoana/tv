import os
import requests
from flask import Flask, Response, render_template
from flask_cors import CORS
import threading
import asyncio
import logging
from datetime import datetime, timezone
import aiohttp

# Setup logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

combined_m3u = None
last_updated = None
lock = threading.Lock()

# Get the sources URL from environment variable
SOURCES_URL = os.getenv('SOURCES')
if not SOURCES_URL:
    raise RuntimeError("Environment variable 'SOURCES' is not set.")

def load_urls():
    try:
        response = requests.get(SOURCES_URL, timeout=5)
        response.raise_for_status()
        urls = [line.strip() for line in response.text.splitlines() if line.strip()]
        if not urls:
            logging.warning(f"No valid URLs found in {SOURCES_URL}.")
        return urls
    except Exception as e:
        logging.error(f"Error fetching {SOURCES_URL}: {e}")
        return []

async def fetch_m3u_async(session, url):
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return ""

async def fetch_all_m3u(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_m3u_async(session, url) for url in urls]
        return await asyncio.gather(*tasks)

def combine_m3u_async(urls):
    unique_streams = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    m3u_contents = loop.run_until_complete(fetch_all_m3u(urls))

    for m3u_content in m3u_contents:
        lines = m3u_content.splitlines()
        current_entry = None
        for line in lines:
            if line.startswith('#EXTINF:'):
                current_entry = line
            elif line and current_entry:
                stream_link = line.strip()
                unique_streams.append(f"{current_entry}\n{stream_link}")
                current_entry = None

    return '#EXTM3U\n' + '\n'.join(unique_streams)

def count_channels(m3u_data):
    return m3u_data.count('#EXTINF:')

def time_ago(last_updated):
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    delta = now - last_updated
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        return f"{seconds // 60} minute{'s' if seconds // 60 != 1 else ''} ago"
    elif seconds < 86400:
        return f"{seconds // 3600} hour{'s' if seconds // 3600 != 1 else ''} ago"
    else:
        return f"{seconds // 86400} day{'s' if seconds // 86400 != 1 else ''} ago"

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    global combined_m3u, last_updated
    with lock:
        if combined_m3u is None:
            urls = load_urls()
            combined_m3u = combine_m3u_async(urls)
            last_updated = datetime.utcnow().replace(tzinfo=timezone.utc)
        channel_count = count_channels(combined_m3u)

    ago_str = time_ago(last_updated)
    last_updated_str = last_updated.strftime('%Y-%m-%d %H:%M:%S GMT') if last_updated else "Unknown"

    return render_template("index.html", channel_count=channel_count, last_updated_str=last_updated_str, ago_str=ago_str)

@app.route('/all.m3u')
def serve_m3u():
    global combined_m3u, last_updated
    with lock:
        if combined_m3u is None:
            urls = load_urls()
            combined_m3u = combine_m3u_async(urls)
            last_updated = datetime.utcnow().replace(tzinfo=timezone.utc)
    return Response(combined_m3u, mimetype='application/vnd.apple.mpegurl')

@app.route('/<path:unused_path>')
def catch_all(unused_path):
    return index()

def regenerate_m3u():
    global combined_m3u, last_updated
    last_urls = []
    while True:
        # Create a new event loop for this background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with lock:
            urls = load_urls()
            if urls != last_urls:
                combined_m3u = combine_m3u_async(urls)
                last_updated = datetime.utcnow().replace(tzinfo=timezone.utc)
                last_urls = urls
                logging.info(f"M3U regenerated at {last_updated}")

        threading.Event().wait(600)  # Wait 10 minutes

threading.Thread(target=regenerate_m3u, daemon=True).start()
