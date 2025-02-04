from flask import Flask, request, render_template, send_from_directory
import requests
import os

app = Flask(__name__)
M3U_URL = "https://iptv-org.github.io/iptv/index.m3u"
PLAYLIST_DIR = "playlists"

if not os.path.exists(PLAYLIST_DIR):
    os.makedirs(PLAYLIST_DIR)

def fetch_m3u():
    response = requests.get(M3U_URL)
    if response.status_code == 200:
        return response.text
    return ""

def parse_m3u(m3u_content):
    lines = m3u_content.split("\n")
    channels = []
    name, url = None, None
    for line in lines:
        if line.startswith("#EXTINF"):
            parts = line.split(",")
            name = parts[-1].strip() if len(parts) > 1 else "Unknown Channel"
        elif line.startswith("http"):
            url = line.strip()
            if name and url:
                channels.append((name, name, url))
                name, url = None, None
    return channels

@app.route("/")
def index():
    m3u_content = fetch_m3u()
    channels = parse_m3u(m3u_content)
    return render_template("index.html", channels=channels)

@app.route("/generate", methods=["POST"])
def generate_playlist():
    filename = request.form.get("filename", "custom_playlist").strip()
    selected_channels = request.form.getlist("channels")
    if not filename.endswith(".m3u"):
        filename += ".m3u"
    filepath = os.path.join(PLAYLIST_DIR, filename)
    with open(filepath, "w") as f:
        f.write("#EXTM3U\n")
        for channel in selected_channels:
            info, url = channel.split("|", 1)
            f.write(f"#EXTINF:-1,{info}\n{url}\n")
    return f"Playlist created: <a href='/playlists/{filename}'>{filename}</a>"

@app.route("/playlists/<filename>")
def serve_playlist(filename):
    return send_from_directory(PLAYLIST_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

