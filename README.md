# cosmopings

![Project Status](https://img.shields.io/badge/status-work--in--progress-orange)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Discord.py](https://img.shields.io/badge/Discord.py-Bot-5865F2)
![YouTube](https://img.shields.io/badge/YouTube-Data%20API%20v3-red)

**An automated Discord bot for YouTube cover and livestream notifications.**

cosmopings monitors a YouTube channel and automatically notifies designated Discord channels when a new cover, scheduled premiere, or livestream is detected.

It combines YouTube RSS feeds with the YouTube Data API v3 to identify new content and send contextual Discord announcements.

> **Work in Progress:** cosmopings is actively being developed. Features, improvements, and fixes may change over time.

---

## Features

- **Dual-Engine Polling** — Combines YouTube RSS feeds with YouTube Data API v3 checks every 5 minutes.
- **Smart Content Classifier** — Distinguishes covers from livestreams using hashtags (`#miracle_melody`, `#miracle_live`) and keywords.
- **Discord Timestamps** — Uses native relative timestamps (`<t:unix:R>`) for scheduled announcements.
- **Premiere Follow-up Alerts** — Sends a notification when a scheduled premiere goes live.
- **Unscheduled Livestream Detection** — Detects surprise livestreams and notifies the community.
- **Shorts & Backlog Filtering** — Filters YouTube Shorts and older uploads.
- **Persistent Deduplication** — Tracks announced and scheduled videos in JSON files to help prevent duplicate notifications after restarts.
- **Community Verification** — Assigns a temporary role to new members and grants the verified role when they accept the server rules.

## How It Works

| YouTube / Discord Event | Bot Behavior |
|---|---|
| New cover published | Announces it in the covers channel |
| Scheduled premiere | Posts an announcement with a countdown |
| Premiere goes live | Sends a follow-up live notification |
| Unscheduled livestream | Detects and announces the stream |
| New member joins | Assigns the non-verified role |
| Member reacts to the rules | Assigns the verified role and removes the non-verified role |

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| discord.py | Discord bot and event handling |
| YouTube Data API v3 | YouTube video and livestream information |
| YouTube RSS | Lightweight upload detection |
| JSON | Persistent notification and verification state |

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

### 2. Create and activate a virtual environment (recommended)

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Set the required environment variables in PowerShell:

```powershell
$env:DISCORD_TOKEN="your_discord_bot_token"
$env:YOUTUBE_API_KEY="your_youtube_api_key"
```

Keep these credentials private. Never commit bot tokens or API keys to GitHub.

### 5. Configure the bot

Edit the constants near the top of `bot.py` to match your YouTube channel and Discord server:

```python
CHANNEL_ID = "YOUR_YOUTUBE_CHANNEL_ID"

COVER_CHANNEL_ID = 000000000000000000
LIVE_CHANNEL_ID = 000000000000000000

RULES_CHANNEL_ID = 000000000000000000
NON_VERIFIED_ROLE_ID = 000000000000000000
MIRACLE_ROLE_ID = 000000000000000000

COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS = ["live", "stream", "livestream"]

COVER_HASHTAGS = ["miracle_melody"]
LIVE_HASHTAGS = ["miracle_live"]
```

Replace the example IDs with the IDs from your own Discord server. Enable the necessary privileged intents in the Discord Developer Portal and grant the bot the permissions it needs to read channel history, send messages, manage roles, and add reactions.

### 6. Run the bot

```bash
python bot.py
```

## Project Structure

```text
cosmopings/
├── bot.py             # Discord bot, YouTube monitoring and verification
├── posted.json        # Previously announced video IDs (created at runtime)
├── scheduled.json     # Scheduled video notifications (created at runtime)
├── verification.json  # Rules message state (created at runtime)
├── requirements.txt   # Python dependencies
├── .gitignore
└── README.md
```

The JSON state files are created or updated by the bot while it runs. They may not exist in a fresh clone until the relevant features are used.

## Roadmap

- [x] YouTube RSS monitoring
- [x] YouTube Data API integration
- [x] Cover and livestream classification
- [x] Scheduled premiere announcements
- [x] Live follow-up notifications
- [x] Duplicate notification prevention
- [x] Discord community rules verification
- [ ] Further reliability and error-handling improvements
- [ ] Additional notification and moderation refinements

## Project Goal

cosmopings was created to automate YouTube content announcements for a Discord community, keeping members informed about new covers, scheduled premieres, and livestreams.

The project also explores Python automation, asynchronous programming, API integration, and Discord bot development.

---

**Developed by [palmtreepaniko](https://github.com/palmtreepaniko)**
