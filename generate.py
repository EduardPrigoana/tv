import requests
from flask import Flask, Response

app = Flask(__name__)

# List of M3U file URLs
urls = [
    "https://iptv-org.github.io/iptv/index.country.m3u",
    "https://forge.fsky.io/frost/repo/raw/branch/main/tv.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlist.m3u8",
    "https://free-git.org/cute/iptv/raw/branch/master/streams/us_redtraffic.m3u",
    "https://free-git.org/cute/iptv/raw/branch/master/streams/us_adultiptv.m3u",
    "https://free-git.org/cute/iptv/raw/commit/69e7168eb61dff2ee7cfc442da30e9bab9a00206/streams/cy_mycamtv.m3u",
    "https://raw.githubusercontent.com/reklamalinir/freeadultiptv/refs/heads/master/live_adult_channels.m3u",
    "http://adultiptv.net/chs.m3u",
    "https://raw.githubusercontent.com/reklamalinir/freeadultiptv/refs/heads/master/live_adult_channels.m3u"
]

combined_m3u = None  # Variable to store the combined M3U content

def fetch_m3u(url):
    """Fetch M3U content from a given URL."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    return response.text

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
                # Use the stream link as the key to ensure uniqueness
                stream_link = line.strip()
                if stream_link not in unique_streams:
                    unique_streams[stream_link] = current_entry + '\n' + stream_link
                current_entry = None  # Reset current entry after adding
            
    # Return the combined M3U content
    return '#EXTM3U\n' + '\n'.join(unique_streams.values())

@app.route('/all.m3u')
def serve_m3u():
    """Serve the combined M3U file."""
    global combined_m3u
    if combined_m3u is None:  # Generate if not already done
        combined_m3u = combine_m3u(urls)
    return Response(combined_m3u, mimetype='application/vnd.apple.mpegurl')

@app.route('/generate')
def generate_m3u():
    """Regenerate the M3U file from the sources."""
    global combined_m3u
    combined_m3u = combine_m3u(urls)  # Regenerate the M3U content
    return Response("M3U playlist regenerated!", mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
