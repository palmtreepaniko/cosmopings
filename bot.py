import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from datetime import datetime, timezone
import json
import os
import xml.etree.ElementTree as ET
import urllib.request


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UCA5BfytqBCeMitzfGPo2dTA"

COVER_CHANNEL_ID = 1451693094859968512
LIVE_CHANNEL_ID = 1451693118012264610
LOG_CHANNEL_ID = 1481394599493763162

CHECK_INTERVAL = 300      
UPCOMING_CHECK_EVERY = 6   

COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS = ["live", "stream", "livestream"]

COVER_HASHTAGS = ["#miracle_melody"]
LIVE_HASHTAGS = ["#miracle_live"]

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
cycle_count = 0
uploads_playlist_id = None

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

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

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_youtube():
    global cycle_count
    cycle_count += 1
    print(f"\n===== CHECKING YOUTUBE (cycle {cycle_count}) =====")

    try:
        posted = load_json("posted.json")
        scheduled = load_json("scheduled.json")

        announced_ids = {item["video_id"] for item in scheduled if item.get("announced", False)}

        latest = get_latest_videos()
        upcoming_rss = get_upcoming_videos_rss()
        upcoming_api = get_upcoming_videos_api() if cycle_count % UPCOMING_CHECK_EVERY == 0 else []

        all_videos = list(set(latest + upcoming_api + upcoming_rss))

        for video_id in all_videos:
            if video_id in posted:
                continue

    
            if video_id in announced_ids:
                continue

            data = get_video_details(video_id)
            if not data:
                continue

            snippet = data["snippet"]
            title = snippet["title"]
            description = snippet.get("description", "")
            live_broadcast_content = snippet.get("liveBroadcastContent", "none")
            scheduled_time = data.get("liveStreamingDetails", {}).get("scheduledStartTime")

            content_type = detect_type(title, description, live_broadcast_content)
            if content_type is None:
                continue

            channel_id = COVER_CHANNEL_ID if content_type == "cover" else LIVE_CHANNEL_ID
            channel = bot.get_channel(channel_id)
            if channel is None:
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            if scheduled_time:
                dt_utc = datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

                if datetime.now(timezone.utc) >= dt_utc:
                    print(f"Skipping already-passed scheduled video {video_id}")
                    posted.append(video_id)
                    save_json("posted.json", posted)
                    continue

                unix_ts = int(dt_utc.timestamp())
                date_str = dt_utc.strftime('%d/%m/%Y %H:%M')

                message = (
                    f"🎵 MIRA is premiering a new cover on {date_str} (GMT), which is <t:{unix_ts}:R>! Don't miss it!~\n{video_url}"
                    if content_type == 'cover'
                    else f"MIRA will be 🔴 LIVE on {date_str} (GMT), which is <t:{unix_ts}:R>! Don't miss it!~\n{video_url}"
                )
                await channel.send(message)
                print(f"Scheduled announcement sent for {video_id}")

                scheduled.append({
                    "video_id": video_id,
                    "time": scheduled_time,
                    "type": content_type,
                    "channel_id": channel_id,
                    "announced": True,
                    "notified": False
                })
                announced_ids.add(video_id)
                save_json("scheduled.json", scheduled)

            elif not scheduled_time and live_broadcast_content == "none":
                if content_type == "live":
                    print(f"Skipping past VOD detected as live for {video_id}")
                    posted.append(video_id)
                    save_json("posted.json", posted)
                    continue

                message = f"🎵 MIRA just dropped a new cover! Go check it out~\n{video_url}"
                await channel.send(message)
                posted.append(video_id)
                save_json("posted.json", posted)
                print(f"Immediate upload notification sent for {video_id}")

            elif live_broadcast_content == "live" and video_id not in announced_ids:
                message = f"🔴 MIRA is live right now! Come join her~\n{video_url}"
                await channel.send(message)
                posted.append(video_id)
                save_json("posted.json", posted)
                print(f"Unscheduled live notification sent for {video_id}")

    except Exception as e:
        print(f"Error in check_youtube: {e}")


@tasks.loop(seconds=300)
async def check_scheduled_start():
    try:
        scheduled = load_json("scheduled.json")
        posted = load_json("posted.json")
        updated_scheduled = []

        for item in scheduled:
            video_id = item["video_id"]
            dt_utc = datetime.strptime(item["time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            content_type = item["type"]
            channel_id = item.get("channel_id", LIVE_CHANNEL_ID)
            notified = item.get("notified", False)

            if not notified and datetime.now(timezone.utc) >= dt_utc:
                data = get_video_details(video_id)
                live_status = data["snippet"].get("liveBroadcastContent", "none") if data else "none"

                if live_status not in ("live", "upcoming"):
                    print(f"Skipping stale notification for {video_id} (already ended)")
                else:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        message = (
                            f"🎵 MIRA just dropped a new cover! Go check it out~\n https://www.youtube.com/watch?v={video_id}"
                            if content_type == "cover"
                            else f"🔴 MIRA is live right now! Come join her~\n https://www.youtube.com/watch?v={video_id}"
                        )
                        await channel.send(message)
                        print(f"START notification sent for {video_id}")

                item["notified"] = True
                if video_id not in posted:
                    posted.append(video_id)
                    save_json("posted.json", posted)
                save_json("scheduled.json", scheduled)

            updated_scheduled.append(item)

        cutoff = datetime.now(timezone.utc).timestamp() - (2 * 24 * 60 * 60)
        updated_scheduled = [
            item for item in updated_scheduled
            if not item.get("notified", False) or
            datetime.strptime(item["time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() > cutoff
        ]

        save_json("scheduled.json", updated_scheduled)

    except Exception as e:
        print(f"Error in check_scheduled_start: {e}")


@bot.event
async def on_ready():
    global uploads_playlist_id
    print(f"Logged in as {bot.user}")
    uploads_playlist_id = get_uploads_playlist()
    print(f"Uploads playlist ID: {uploads_playlist_id}")

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        scheduled = load_json("scheduled.json")
        pending = [item for item in scheduled if not item.get("notified", False)]

        if pending:
            msg = "Bot restarted! These streams were announced and are still pending:\n"
            for item in pending:
                msg += f"- https://www.youtube.com/watch?v={item['video_id']} (scheduled: {item['time']})\n"
        else:
            msg = "Bot restarted! No pending scheduled streams."

        await log_channel.send(msg)

    if not check_youtube.is_running():
        check_youtube.start()
    if not check_scheduled_start.is_running():
        check_scheduled_start.start()

bot.run(DISCORD_TOKEN)
