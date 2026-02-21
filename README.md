🎵 Cosmopings

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2.svg)](https://discordpy.readthedocs.io/)
[![YouTube API](https://img.shields.io/badge/YouTube-Data%20API%20v3-red.svg)](https://developers.google.com/youtube/v3)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-ready Discord bot that monitors a YouTube channel and automatically posts notifications for:

* 🎵 New cover uploads
* 🔴 Livestreams
* 📅 Scheduled premieres & upcoming streams
* ⏰ “Starting Now” alerts

Designed to be lightweight, reliable, and safe for deployment (Railway, VPS, etc.).

---

Features

* Hybrid YouTube detection system:

  * YouTube Data API v3
  * RSS feed fallback
* Smart content classification:

  * Keyword-based detection
  * Hashtag-based detection
  * Live broadcast metadata detection
* Scheduled premiere handling
* Automatic “Starting NOW” notification
* Duplicate prevention via JSON persistence
* Environment variable configuration (secure for deployment)

---

Architecture Overview

The bot runs two background tasks:

1️ `check_youtube`

* Polls latest uploads
* Detects upcoming streams
* Determines content type (cover / live)
* Sends scheduled or immediate notifications

2️`check_scheduled_start`

* Monitors scheduled premieres
* Sends alert when start time is reached

State persistence:

* `posted.json` → already announced videos
* `scheduled.json` → pending scheduled content

---

 Installation

1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install discord.py google-api-python-client
```

---

 Environment Variables

This project uses environment variables for security.

Set the following:

```bash
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
```

Example (Linux / macOS)

```bash
export DISCORD_TOKEN=your_token_here
export YOUTUBE_API_KEY=your_api_key_here
```

Example (Windows PowerShell)

```powershell
setx DISCORD_TOKEN "your_token_here"
setx YOUTUBE_API_KEY "your_api_key_here"
```

---

Running the Bot

```bash
python bot.py
```

Expected output:

```
Logged in as YourBotName
Uploads playlist ID: ...
===== CHECKING YOUTUBE (cycle 1) =====
```
