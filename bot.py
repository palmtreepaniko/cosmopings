import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from datetime import datetime, timezone
import json
import os
import xml.etree.ElementTree as ET
import urllib.request

import os


# ================= CONFIG =================

DISCORD_TOKEN = "your_token_here"
YOUTUBE_API_KEY = "your_key_here"
CHANNEL_ID = "UCA5BfytqBCeMitzfGPo2dTA"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COVER_CHANNEL_ID = 1451693094859968512
LIVE_CHANNEL_ID = 1451693118012264610

CHECK_INTERVAL = 300       
UPCOMING_CHECK_EVERY = 6   


COVER_KEYWORDS = ["cover", "covered", "歌ってみた", "歌わせていただきました"]

LIVE_KEYWORDS = ["live", "stream", "配信", "雑談", "singing", "karaoke"]

COVER_HASHTAGS = ["#miracle_melody", "#cover"]
LIVE_HASHTAGS = ["#miracle_live", "#live", "#stream"]

# ==========================================

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

cycle_count = 0

# ================= JSON =================

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ================= DETECTION =================

def detect_type(title, description, live_broadcast_content):
    title_lower = title.lower()
    desc_lower = description.lower()

    for kw in COVER_KEYWORDS:
        if kw.lower() in title_lower:
            return "cover"
    for kw in LIVE_KEYWORDS:
        if kw.lower() in title_lower:
            return "live"

    for tag in COVER_HASHTAGS:
        if tag in desc_lower:
            return "cover"
    for tag in LIVE_HASHTAGS:
        if tag in desc_lower:
            return "live"

    if live_broadcast_content in ("upcoming", "live"):
        return "live"

    return None

# ================= YOUTUBE =================

uploads_playlist_id = None

def get_uploads_playlist():
    request = youtube.channels().list(
        part="contentDetails",
        id=CHANNEL_ID
    )
    response = request.execute()
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_latest_videos():
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=10
    )
    response = request.execute()
    return [item["snippet"]["resourceId"]["videoId"] for item in response["items"]]

def get_upcoming_videos_api():
    """Costs 100 quota units — only called every 30 minutes"""
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=CHANNEL_ID,
            eventType="upcoming",
            type="video",
            maxResults=5,
            order="date"
        )
        response = request.execute()
        return [item["id"]["videoId"] for item in response.get("items", [])]
    except Exception as e:
        print(f"    API upcoming check failed: {e}")
        return []

def get_upcoming_videos_rss():
    """Free — no quota cost, called every cycle"""
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
        root = ET.fromstring(data)
        ns = {"yt": "http://www.youtube.com/xml/schemas/2015", "atom": "http://www.w3.org/2005/Atom"}
        video_ids = []
        for entry in root.findall("atom:entry", ns):
            vid = entry.find("yt:videoId", ns)
            if vid is not None:
                video_ids.append(vid.text)
        return video_ids
    except Exception as e:
        print(f"    RSS fetch failed: {e}")
        return []

def get_video_details(video_id):
    request = youtube.videos().list(
        part="snippet,liveStreamingDetails",
        id=video_id
    )
    response = request.execute()
    if not response.get("items"):
        return None
    return response["items"][0]

# ================= MAIN CHECK =================

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_youtube():
    global cycle_count
    cycle_count += 1

    print(f"\n===== CHECKING YOUTUBE (cycle {cycle_count}) =====")

    try:
        posted = load_json("posted.json")
        scheduled = load_json("scheduled.json")
        scheduled_ids = {item["video_id"] for item in scheduled}

        latest = get_latest_videos()
        upcoming_rss = get_upcoming_videos_rss()

        if cycle_count % UPCOMING_CHECK_EVERY == 0:
            upcoming_api = get_upcoming_videos_api()
            print(f"Upcoming (API): {upcoming_api}")
        else:
            upcoming_api = []

        all_videos = list(set(latest + upcoming_api + upcoming_rss))

        print(f"Latest: {latest}")
        print(f"Upcoming (RSS): {upcoming_rss}")

        for video_id in all_videos:

            if video_id in posted:
                continue

            data = get_video_details(video_id)
            if not data:
                continue

            snippet = data["snippet"]
            title = snippet["title"]
            description = snippet.get("description", "")
            live_broadcast_content = snippet.get("liveBroadcastContent", "none")

            scheduled_time = None
            if "liveStreamingDetails" in data:
                scheduled_time = data["liveStreamingDetails"].get("scheduledStartTime")

            print(f"--- Video: {title}")
            print(f"    live_broadcast_content: {live_broadcast_content}")
            print(f"    scheduled_time: {scheduled_time}")
            print(f"    description preview: '{description[:100]}'")

            content_type = detect_type(title, description, live_broadcast_content)
            print(f"    content_type: {content_type}")

            if content_type is None:
                print(f"    Skipping — couldn't determine type")
                continue

            channel_id = COVER_CHANNEL_ID if content_type == "cover" else LIVE_CHANNEL_ID
            channel = bot.get_channel(channel_id)

            if channel is None:
                print(f"    Channel {channel_id} not found. Skipping.")
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # ===== SCHEDULED / UPCOMING =====
            if scheduled_time and video_id not in scheduled_ids:
                dt_utc = datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                unix_ts = int(dt_utc.timestamp())
                date_str = dt_utc.strftime('%d/%m/%Y %H:%M')

                if datetime.now(timezone.utc) >= dt_utc and live_broadcast_content == "none":
                    if content_type == "cover":
                        message = (
                            f"🎵 Mira just dropped a new cover! Go give it a listen~ 🎧\n"
                            f"{video_url}"
                        )
                    else:
                        message = (
                            f"🔴 Mira is live right now! Come join her~ 👾\n"
                            f"{video_url}"
                        )
                    await channel.send(message)
                    print(f"    Upload notification sent (premiere ended)!")
                    posted.append(video_id)

                else:
                    if content_type == "cover":
                        message = (
                            f"📅 MIRA premieres a new song cover {date_str}, which is <t:{unix_ts}:R>! Don't miss it!~\n"
                            f"{video_url}"
                        )
                    else:
                        message = (
                            f"📅 MIRA will be 🔴 LIVE {date_str}, which is <t:{unix_ts}:R>! Don't miss it!~\n"
                            f"{video_url}"
                        )
                    await channel.send(message)
                    print(f"    Scheduled notification sent!")

                    scheduled.append({
                        "video_id": video_id,
                        "time": scheduled_time,
                        "type": content_type,
                        "channel_id": channel_id
                    })
                    scheduled_ids.add(video_id)

            # ===== NORMAL UPLOAD =====
            elif not scheduled_time and live_broadcast_content == "none":
                if content_type == "cover":
                    message = (
                        f"Mira just dropped a new cover! Go give it a listen~ 🎧\n"
                        f"{video_url}"
                    )
                else:
                    message = (
                        f"🔴 Mira is live right now! Come join her~ 👾\n"
                        f"{video_url}"
                    )
                await channel.send(message)
                print(f"    Upload notification sent!")
                posted.append(video_id)

            else:
                print(f"    Fell through — scheduled_time: {scheduled_time}, live_broadcast_content: {live_broadcast_content}")

        save_json("posted.json", posted)
        save_json("scheduled.json", scheduled)

    except Exception as e:
        print(f"Error in check_youtube: {e}")

# ================= SCHEDULED START CHECK =================

@tasks.loop(seconds=60)
async def check_scheduled_start():
    try:
        scheduled = load_json("scheduled.json")
        posted = load_json("posted.json")
        remaining_scheduled = []

        for item in scheduled:
            video_id = item["video_id"]
            scheduled_time = item["time"]
            content_type = item["type"]
            channel_id = item.get("channel_id", LIVE_CHANNEL_ID)

            dt_utc = datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) >= dt_utc:
                channel = bot.get_channel(channel_id)
                if channel:
                    if content_type == "cover":
                        await channel.send(
                            f"🎵 Mira is premiering a new cover RIGHT NOW! Go give it a listen~ 🎧\n"
                            f"https://www.youtube.com/watch?v={video_id}"
                        )
                    else:
                        await channel.send(
                            f"🔴 Mira is LIVE right now! Come join her~ 👾\n"
                            f"https://www.youtube.com/watch?v={video_id}"
                        )
                    print(f"START notification sent for {video_id}")

                if video_id not in posted:
                    posted.append(video_id)
            else:
                remaining_scheduled.append(item)

        save_json("scheduled.json", remaining_scheduled)
        save_json("posted.json", posted)

    except Exception as e:
        print(f"Error in check_scheduled_start: {e}")

# ================= READY =================

@bot.event
async def on_ready():
    global uploads_playlist_id
    print(f"Logged in as {bot.user}")
    uploads_playlist_id = get_uploads_playlist()
    print(f"Uploads playlist ID: {uploads_playlist_id}")
    check_youtube.start()
    check_scheduled_start.start()

# ================= RUN =================

bot.run(DISCORD_TOKEN)
