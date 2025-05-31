import os
import requests
from flask import Flask, Response, render_template
from flask_cors import CORS
from flask_apscheduler import APScheduler
import logging
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.DEBUG)

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())
CORS(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

combined_m3u = None
last_updated = None

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

def fetch_m3u_sync(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return ""

def fetch_all_m3u(urls):
    return [fetch_m3u_sync(url) for url in urls]

def combine_m3u_sync(urls):
    unique_streams = []
    seen_streams = set()  # Track URLs we've already added
    for m3u_content in fetch_all_m3u(urls):
        lines = m3u_content.splitlines()
        current_entry = None
        for line in lines:
            if line.startswith('#EXTINF:'):
                current_entry = line
            elif line and current_entry:
                stream_link = line.strip()
                if stream_link not in seen_streams:
                    unique_streams.append(f"{current_entry}\n{stream_link}")
                    seen_streams.add(stream_link)  # Mark as seen
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
    if combined_m3u is None:
        do_regenerate_m3u()
    channel_count = count_channels(combined_m3u)
    ago_str = time_ago(last_updated)
    last_updated_str = last_updated.strftime('%Y-%m-%d %H:%M:%S GMT') if last_updated else "Unknown"
    return render_template("index.html", channel_count=channel_count, last_updated_str=last_updated_str, ago_str=ago_str)

@app.route('/all.m3u')
def serve_m3u():
    global combined_m3u, last_updated
    if combined_m3u is None:
        do_regenerate_m3u()
    return Response(combined_m3u, mimetype='application/vnd.apple.mpegurl')

@app.route('/<path:unused_path>')
def catch_all(unused_path):
    return index()

# Core regeneration logic
def do_regenerate_m3u():
    global combined_m3u, last_updated
    urls = load_urls()
    if urls:
        combined_m3u = combine_m3u_sync(urls)
        last_updated = datetime.utcnow().replace(tzinfo=timezone.utc)
        logging.info(f"M3U generated at {last_updated.isoformat()}")
    else:
        logging.warning("No URLs to process.")

# Scheduled Job using APScheduler
@scheduler.task('interval', id='regenerate_m3u_job', minutes=1200, misfire_grace_time=300)
def regenerate_m3u():
    do_regenerate_m3u()

if __name__ == "__main__":
    do_regenerate_m3u()  # Generate immediately on startup
    app.run(host='0.0.0.0', port=5000)
