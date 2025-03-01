import requests
from flask import Flask, Response
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# List of M3U file URLs
URLS = [
    "https://iptv-org.github.io/iptv/index.country.m3u",
    "https://git.prigoana.com/frost/repo/src/branch/main/tv.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://git.nadeko.net/Mystique/MystiquePlus/raw/branch/main/mystique.m3u",
    "https://m3u.ibert.me/fmml_itv.m3u",
    "https://m3u.ibert.me/fmml_index.m3u",
    "https://m3u.ibert.me/ycl_iptv.m3u",
    "https://m3u.ibert.me/cymz6_lives.m3u",
    "https://m3u.ibert.me/y_g.m3u",
    "https://m3u.ibert.me/j_home.m3u",
    "https://m3u.ibert.me/j_iptv.m3u",
    "https://m3u.ibert.me/o_cn.m3u",
    "https://m3u.ibert.me/o_s_cn_112114.m3u",
    "https://m3u.ibert.me/o_s_cn_cctv.m3u",
    "https://m3u.ibert.me/o_s_cn_cgtn.m3u",
    "https://m3u.ibert.me/cn.m3u",
    "https://m3u.ibert.me/cn_c.m3u",
    "https://m3u.ibert.me/cn_p.m3u",
    "https://m3u.ibert.me/q_bj_iptv_unicom.m3u",
    "https://m3u.ibert.me/q_bj_iptv_unicom_m.m3u",
    "https://m3u.ibert.me/q_bj_iptv_mobile.m3u",
    "https://m3u.ibert.me/q_bj_iptv_mobile_m.m3u"
]

# Cached M3U content and a lock for thread safety
combined_m3u = None
lock = threading.Lock()

def fetch_m3u(url):
    """Fetch M3U content from a given URL with error handling."""
    try:
        response = requests.get(url, timeout=5)  # Set timeout to prevent long waits
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def combine_m3u(urls):
    """Combine M3U content from multiple URLs and remove duplicates."""
    unique_streams = {}
    
    for url in urls:
        m3u_content = fetch_m3u(url)
        lines = m3u_content.splitlines()
        current_entry = None
        
        for line in lines:
            if line.startswith('#EXTINF:'):
                current_entry = line
            elif line and current_entry:
                stream_link = line.strip()
                if stream_link not in unique_streams:
                    unique_streams[stream_link] = f"{current_entry}\n{stream_link}"
                current_entry = None  # Reset after adding
            
    return '#EXTM3U\n' + '\n'.join(unique_streams.values())

@app.route('/all.m3u')
def serve_m3u():
    """Serve the cached combined M3U file, generating it if necessary."""
    global combined_m3u
    with lock:
        if combined_m3u is None:  # Generate if not already done
            combined_m3u = combine_m3u(URLS)
    return Response(combined_m3u, mimetype='application/vnd.apple.mpegurl')

@app.route('/generate')
def generate_m3u():
    """Force regeneration of the M3U file from the sources."""
    global combined_m3u
    with lock:
        combined_m3u = combine_m3u(URLS)  # Regenerate the M3U content
    return Response("M3U playlist regenerated!", mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
