# cosmopings

![Project Status](https://img.shields.io/badge/status-work--in--progress-orange)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Discord.py](https://img.shields.io/badge/Discord.py-Bot-5865F2)
![YouTube](https://img.shields.io/badge/YouTube-Data%20API%20v3-red)
![License](https://img.shields.io/badge/license-MIT-green)

**An automated Discord bot for YouTube cover and livestream notifications.**

cosmopings is a specialized Discord bot that monitors a YouTube channel and automatically notifies designated Discord channels whenever a new cover, scheduled premiere, or livestream is detected.

Built to keep a community updated without requiring manual announcements, cosmopings combines YouTube RSS feeds and the YouTube Data API v3 to detect new content and deliver contextual Discord notifications.

> **Work in Progress:** cosmopings is actively maintained and developed. Features, improvements, and fixes may be introduced over time.

---

## Features

- **Dual-Engine Polling** — Combines YouTube RSS feeds with YouTube Data API v3 polling every 5 minutes to detect new publications efficiently.
- **Smart Content Classifier** — Distinguishes covers from gaming and chatting livestreams using hashtags (`#miracle_melody`, `#miracle_live`) and keywords.
- **Localized Timestamps** — Uses Discord's native relative timestamps (`<t:unix:R>`) for scheduled premieres and livestream announcements.
- **Premiere Follow-up Alerts** — Automatically sends an additional notification when a scheduled premiere goes live.
- **Unscheduled Livestream Detection** — Detects surprise livestreams and notifies the community.
- **Spam & Shorts Filtering** — Filters out YouTube Shorts and older backlog uploads.
- **Persistent Deduplication** — Uses JSON files to track previously announced and scheduled content, preventing duplicate notifications across restarts.

## How It Works

| YouTube Event | Discord Behavior |
|---|---|
| New cover published | Sends an announcement to the covers channel |
| Scheduled premiere | Posts an announcement with a countdown |
| Premiere goes live | Sends a follow-up live notification |
| Unscheduled livestream | Detects and announces the stream |

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| discord.py | Discord bot functionality |
| YouTube Data API v3 | YouTube content detection |
| YouTube RSS | Lightweight publication polling |
| JSON | Persistent notification tracking |

## Installation

### Requirements

- Python 3.8+
- A Discord bot token
- A YouTube Data API v3 key
- Git

### 1. Clone the repository

```bash
git clone https://github.com/palmtreepaniko/cosmopings.git
cd cosmopings
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
PORT=25888
```

**Important:** Never commit your `.env` file or expose your bot token and API key.

### 4. Configure the bot

Edit the constants at the top of `bot.py` to match your target YouTube channel and Discord channels:

```python
CHANNEL_ID = "UCA5BfytqBCeMitzfGPo2dTA"

COVER_CHANNEL_ID = 000000000000000000
LIVE_CHANNEL_ID = 000000000000000000

COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS = ["live", "stream", "livestream"]

COVER_HASHTAGS = ["miracle_melody"]
LIVE_HASHTAGS = ["miracle_live"]
```

Replace the Discord channel ID placeholders with your own channel IDs.

## Running the Bot

Start the Discord bot:

```bash
python bot.py
```

## Project Structure

```text
cosmopings/
│
├── bot.py             # Main Discord bot and scheduler
├── web_server.py      # aiohttp web server and health endpoints
│
├── web/
│   └── index.html     # Cosmic portfolio landing page
│
├── posted.json        # Previously announced content
├── scheduled.json     # Upcoming scheduled events
│
├── requirements.txt   # Python dependencies
├── .gitignore
└── README.md
```

## Roadmap

- [x] YouTube RSS monitoring
- [x] YouTube Data API integration
- [x] Cover and livestream classification
- [x] Scheduled premiere announcements
- [x] Live follow-up notifications
- [x] Duplicate notification prevention
- [ ] Further reliability and error-handling improvements
- [ ] Additional monitoring and notification refinements


## Project Goal

cosmopings was created to automate YouTube content announcements for a Discord community, making sure members are notified about new covers, scheduled premieres, and livestreams.

The project also explores asynchronous programming, API integration, automated monitoring, and Discord bot development.

---

**Developed by [palmtreepaniko](https://github.com/palmtreepaniko)**
