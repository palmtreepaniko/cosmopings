✨ Cosmopings ✨
A Discord bot that monitors a YouTube channel and automatically notifies designated Discord channels when a new cover or livestream is published.

## Features
- Polls the YouTube API and RSS feed every 5 minutes to detect new publications
- Detects content type (cover vs. live) using keywords in the title and hashtags in the description
- Posts premiere/scheduled stream announcements with Discord relative timestamps
- Sends a follow-up notification when a scheduled event actually goes live
- Handles unscheduled lives that start without prior announcement
- Avoids duplicate notifications through persistent JSON tracking

## How it works
| Event | Behavior |
|---|---|
| New cover published | Posted immediately in the covers channel |
| Scheduled premiere | Posts an announcement with a countdown |
| Premiere goes live | Sends a "it's live now" follow-up notification |
| Unscheduled live | Detected and notified in real time |

Content type is determined by:
- Keywords in the title (e.g. cover, live, stream)
- Hashtags in the description

## Installation
### Requirements
- Python 3.8+
- A Discord bot token
- A YouTube Data API v3 key

### Setup
```
git clone https://github.com/palmtreepaniko/cosmopings
cd cosmopings
pip install -r requirements.txt
```

### Environment variables
Create a `.env` file or set the following environment variables:
```
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
```

### Configuration
Edit the constants at the top of `bot.py` to match your setup:
```
CHANNEL_ID = "your_youtube_channel_id"
COVER_CHANNEL_ID = 000000000000000000   # Discord channel ID for covers
LIVE_CHANNEL_ID  = 000000000000000000   # Discord channel ID for lives
COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS  = ["live", "stream", "livestream"]
COVER_HASHTAGS = ["#your_cover_hashtag"]
LIVE_HASHTAGS  = ["#your_live_hashtag"]
```

## Running the bot
```
python bot.py
```

## File structure
```
cosmopings/
├── bot.py           
├── posted.json      # Tracks already-notified videos
├── scheduled.json   # Tracks upcoming scheduled events
└── requirements.txt
```

## Dependencies
- discord.py
- google-api-python-client

## Discord bot permissions
Make sure your bot has the following permissions:
- Send Messages
- View Channels

## Notes
- The YouTube `search().list` endpoint (used for detecting upcoming streams) consumes more API quota. It runs every 6 cycles (~30 minutes) by default to stay within limits.
- `posted.json` and `scheduled.json` are created automatically on first run.
