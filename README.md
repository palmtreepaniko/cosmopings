[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2.svg)](https://discordpy.readthedocs.io/)
[![YouTube API](https://img.shields.io/badge/YouTube-Data%20API%20v3-red.svg)](https://developers.google.com/youtube/v3)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# ✨ Cosmopings ✨

A Discord bot that monitors a YouTube channel and automatically notifies designated Discord channels when a new cover or live stream is posted.

---

## Features

- Polls the YouTube API and RSS feed every 5 minutes for new uploads
- Detects content type (cover vs. live) using title keywords and description hashtags
- Posts scheduled premiere/stream announcements with Discord relative timestamps
- Sends a follow-up notification when a scheduled event actually goes live
- Handles unscheduled streams that go live without prior announcement
- Prevents duplicate notifications using persistent JSON tracking

---

## How It Works

| Event | Behavior |
|---|---|
| New cover upload | Posts immediately to the covers channel |
| Scheduled premiere | Posts an announcement with a countdown timestamp |
| Premiere goes live | Sends a follow-up "it's live now" notification |
| Unscheduled live stream | Detects and notifies in real time |

Content type is determined by:
- **Keywords** in the title (e.g. `cover`, `live`, `stream`)
- **Hashtags** in the description

---

## Setup

### Prerequisites

- Python 3.8+
- A Discord bot token
- A YouTube Data API v3 key

### Installation

```bash
git clone hub.com/palmtreepaniko/cosmopings
cd cosmopings
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file or set the following environment variables:

```env
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
```

### Configuration

Edit the constants at the top of `bot.py` to match your setup:

```python
CHANNEL_ID = "your_youtube_channel_id"

COVER_CHANNEL_ID = 000000000000000000   # Discord channel ID for covers
LIVE_CHANNEL_ID  = 000000000000000000   # Discord channel ID for live streams

COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS  = ["live", "stream", "livestream"]

COVER_HASHTAGS = ["#your_cover_hashtag"]
LIVE_HASHTAGS  = ["#your_live_hashtag"]
```

### Running the Bot

```bash
python bot.py
```

---

## File Structure

```
cosmopings/
├── bot.py           
├── posted.json      # Tracks already-notified video IDs
├── scheduled.json   # Tracks upcoming scheduled events
└── requirements.txt
```

---

## Requirements

```
discord.py
google-api-python-client
```

---

## Discord Bot Permissions

Make sure your bot has the following permissions:
- `Send Messages`
- `View Channels`

---

## Notes

- The YouTube `search().list` endpoint (used for upcoming stream detection) consumes more API quota. It runs every 6 cycles (~30 minutes) by default to stay within limits.
- `posted.json` and `scheduled.json` are created automatically on first run.
