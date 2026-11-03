# Cosmopings 🌌

A specialized Discord bot that monitors a YouTube channel and automatically notifies designated Discord channels when a new cover or livestream is published.

Includes a built-in portfolio and status web dashboard compatible with reverse proxy hosts (such as `bot-hosting.cloud`).

## Features
- **Dual-Engine Polling**: Blends fast YouTube RSS feeds with YouTube Data API v3 every 5 minutes to detect new publications without quota waste.
- **Smart Content Classifier**: Distinguishes covers from gaming/chat streams using hashtags (`#miracle_melody` vs. `#miracle_live`) and keywords.
- **Dynamic Localized Timestamps**: Posts premiere and scheduled stream announcements with native Discord relative countdowns (`<t:unix:R>`).
- **Follow-up Live Alerts**: Automatically fires a "it's live now!" notification when a scheduled premiere starts.
- **Unscheduled Stream Detection**: Catches surprise livestreams in real time.
- **Spam & Shorts Filter**: Eliminates YouTube Shorts and backlog uploads older than 24h.
- **Stateful JSON Deduplication**: Avoids duplicate notifications with persistent tracking (`posted.json`, `scheduled.json`).
- **Embedded Web Server & Portfolio**: Native `aiohttp` web server running on port `25888` (or `PORT` env var) serving a cosmic showcase portfolio, live telemetry API (`/api/status`), and health check (`/health`).

## How it works
| Event | Behavior |
|---|---|
| New cover published | Posted immediately in the covers channel |
| Scheduled premiere | Posts an announcement with a countdown |
| Premiere goes live | Sends a "it's live now" follow-up notification |
| Unscheduled live | Detected and notified in real time |

---

## Web Server & Keep-Alive (Port 25888)

When hosted on platforms like `bot-hosting.cloud`, the app provides a public HTTPS reverse proxy URL (e.g. `https://2ekkusjbrm.apps.bot-hosting.cloud` mapped to port `25888`).

The bot automatically runs an asynchronous web server inside the event loop:
- **`GET /`**: Cosmic showcase portfolio website.
- **`GET /health`**: JSON health check for uptime monitors (e.g., [UptimeRobot](https://uptimerobot.com)) to keep your bot container alive 24/7.
- **`GET /api/status`**: Live JSON telemetry (ping, uptime, videos tracked, upcoming schedule).

---

## Installation & Setup

### Requirements
- Python 3.8+
- A Discord bot token
- A YouTube Data API v3 key

### Setup
```bash
git clone https://github.com/palmtreepaniko/cosmopings
cd cosmopings
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file or set the following environment variables:
```env
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
PORT=25888
```

### Configuration
Edit the constants at the top of `bot.py` to match your target YouTube channel and Discord channels:
```python
CHANNEL_ID = "UCA5BfytqBCeMitzfGPo2dTA" # Target YouTube Channel ID
COVER_CHANNEL_ID = 000000000000000000    # Discord channel ID for covers
LIVE_CHANNEL_ID  = 000000000000000000    # Discord channel ID for lives
COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS  = ["live", "stream", "livestream"]
COVER_HASHTAGS = ["miracle_melody"]
LIVE_HASHTAGS  = ["miracle_live"]
```

## Running the Bot
```bash
python bot.py
```

To test just the web server locally:
```bash
python web_server.py
```

## File Structure
```
cosmopings/
├── bot.py           # Main Discord bot & scheduler
├── web_server.py    # aiohttp web server & health endpoints
├── web/
│   └── index.html   # Cosmic portfolio landing page
├── posted.json      # Tracks already-notified videos
├── scheduled.json   # Tracks upcoming scheduled events
├── requirements.txt # Project dependencies
└── README.md
```
