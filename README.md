# TV

Python-based web service designed to aggregate M3U streams from multiple sources, combine them into a single playlist, and offer the ability to create custom playlists from those streams. Currently, it features around 13,000 different channels, though many links are dead.

The service is split into two parts:
- **[Playlist Creator](https://tv.prigoana.com/)**
- **[Playlist Aggregator](https://m3u.prigoana.com/all.m3u)**

## Roadmap
- Combine both scripts into a single, unified solution
- Implement functionality to test for dead links
- Improve code quality and optimize performance
- Transition to a production-grade WSGI server
- Add NSFW streams in a separate playlist
- Docker support
- Front-End improvements

## Deploying

To deploy the service locally, follow these steps:

1. Install the necessary dependencies:
   ```
   pip install -r requirements.txt
   ```
Depending on your use case, run one of the following commands:
To create your own playlists (via the app):
```
python app.py
```
To aggregate the streams (via the generator):
```
python gen.py
```
