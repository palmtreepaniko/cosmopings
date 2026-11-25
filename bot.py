import asyncio
import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from datetime import datetime, timezone
import json
import os
import re
import xml.etree.ElementTree as ET
import urllib.request
from web_server import start_web


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UCA5BfytqBCeMitzfGPo2dTA"

COVER_CHANNEL_ID = 1451693094859968512
LIVE_CHANNEL_ID = 1451693118012264610

RULES_CHANNEL_ID = 1434900258424356885
NON_VERIFIED_ROLE_ID = 1470919158073135311
MIRACLE_ROLE_ID = 1470919339409670302
VERIFICATION_EMOJI = "✅"
VERIFICATION_STATE_FILE = "verification.json"
RULES_EMBED_COLOR = 0xBFA2DB

CHECK_INTERVAL = 300      
UPCOMING_CHECK_EVERY = 6   

COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS = ["live", "stream", "livestream"]

COVER_HASHTAGS = ["miracle_melody"]
LIVE_HASHTAGS = ["miracle_live"]

SHORTS_MAX_DURATION_SECONDS = 60
SHORTS_TAGS = ["#shorts", "#short"]


NOTIFY_MAX_AGE_HOURS = 24

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
intents.reactions = True
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

def parse_iso8601_duration(duration_str):
    if not duration_str:
        return None
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if not match:
        return None
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds

def is_probable_short(title, description, duration_seconds):
    text = f"{title or ''} {description or ''}".lower()
    if any(tag in text for tag in SHORTS_TAGS):
        return True
    if duration_seconds is not None and 0 < duration_seconds <= SHORTS_MAX_DURATION_SECONDS:
        return True
    return False

def detect_type(title, description, live_broadcast_content):
    title_lower = (title or "").lower()
    desc_lower = (description or "").lower()

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
        maxResults=25
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
        part="snippet,liveStreamingDetails,contentDetails",
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
        scheduled_ids = {item["video_id"] for item in scheduled}

        latest = get_latest_videos()
        upcoming_rss = get_upcoming_videos_rss()
        upcoming_api = get_upcoming_videos_api() if cycle_count % UPCOMING_CHECK_EVERY == 0 else []

        all_videos = list(set(latest + upcoming_api + upcoming_rss))
        print(f"  Candidates this cycle ({len(all_videos)}): {all_videos}")

        for video_id in all_videos:
            if video_id in posted:
                continue

            data = get_video_details(video_id)
            if not data:
                continue

            snippet = data["snippet"]
            title = snippet["title"]
            description = snippet.get("description") or ""
            live_broadcast_content = snippet.get("liveBroadcastContent", "none")

            scheduled_time = data.get("liveStreamingDetails", {}).get("scheduledStartTime")

            is_scheduled_or_live = bool(scheduled_time) or live_broadcast_content in ("live", "upcoming")
            duration_seconds = None
            if not is_scheduled_or_live:
                duration_seconds = parse_iso8601_duration(
                    data.get("contentDetails", {}).get("duration")
                )

            if is_probable_short(title, description, duration_seconds):
                print(f"  {video_id} ('{title}', {duration_seconds}s): Short, skipping")
                posted.append(video_id)
                continue

            content_type = detect_type(title, description, live_broadcast_content)
            if content_type is None:
                print(f"  {video_id} ('{title}'): no cover/live match, skipping")
                continue

            channel_id = COVER_CHANNEL_ID if content_type == "cover" else LIVE_CHANNEL_ID
            channel = bot.get_channel(channel_id)
            if channel is None:
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            if scheduled_time and video_id not in scheduled_ids:
                dt_utc = datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

                if datetime.now(timezone.utc) >= dt_utc:
                    age_hours = (datetime.now(timezone.utc) - dt_utc).total_seconds() / 3600
                    if age_hours > NOTIFY_MAX_AGE_HOURS:
                        print(f"  {video_id}: scheduled time passed {age_hours:.1f}h ago, backlog, not notifying")
                        posted.append(video_id)
                        continue

                    message = (
                        f"🎵 MIRA just dropped a new cover! Go check it out~\n{video_url}"
                        if content_type == "cover"
                        else f"🔴 MIRA is LIVE right now! Come join her~\n{video_url}"
                    )
                    await channel.send(message)
                    posted.append(video_id)
                    print(f"Catch-up notification sent for {video_id}")
                    continue

                unix_ts = int(dt_utc.timestamp())
                date_str = dt_utc.strftime('%d/%m/%Y %H:%M')

                message = (
                        f"🎵 MIRA is premiering a new cover on {date_str} (GMT), which is <t:{unix_ts}:R>! Don't miss it!~\n{video_url}"
                        if content_type == 'cover'
                        else f"MIRA will be 🔴 LIVE on {date_str} (GMT), which is <t:{unix_ts}:R>! Don't miss it!~\n{video_url}"
                    )
                await channel.send(message)
                print(f"Scheduled notification sent for {video_id}")

                scheduled.append({
                    "video_id": video_id,
                    "time": scheduled_time,
                    "type": content_type,
                    "channel_id": channel_id,
                    "notified": False 
                })
                scheduled_ids.add(video_id)

            elif not scheduled_time and live_broadcast_content == "none":
                published_at = snippet.get("publishedAt")
                if published_at:
                    published_dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    age_hours = (datetime.now(timezone.utc) - published_dt).total_seconds() / 3600
                    if age_hours > NOTIFY_MAX_AGE_HOURS:
                        print(f"  {video_id} ('{title}'): uploaded {age_hours:.1f}h ago, backlog, not notifying")
                        posted.append(video_id)
                        continue

                message = f"🎵 MIRA just dropped a new cover! Go check it out~\n{video_url}" if content_type == "cover" else f"🔴 MIRA is live right now! Come join her~\n{video_url}"
                await channel.send(message)
                posted.append(video_id)
                print(f"Immediate upload notification sent for {video_id}")

        save_json("posted.json", posted)
        save_json("scheduled.json", scheduled)

    except Exception as e:
        print(f"Error in check_youtube: {e}")


@tasks.loop(seconds=60)
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

            # If this video was already recorded as announced, never announce it again.
            # This also repairs older scheduled.json entries that lack a "notified" field.
            if video_id in posted:
                if not notified:
                    item["notified"] = True
                    print(f"  {video_id}: already recorded in posted.json; skipping duplicate START notification")
            elif not notified and datetime.now(timezone.utc) >= dt_utc:
                channel = bot.get_channel(channel_id)
                if channel:
                    message = f"🎵 MIRA just dropped a new {content_type}! Go check it out~\n https://www.youtube.com/watch?v={video_id}" if content_type == "cover" else f"🔴 MIRA is live right now! Come join her~\n https://www.youtube.com/watch?v={video_id}"
                    await channel.send(message)
                    print(f"START notification sent for {video_id}")
                    item["notified"] = True
                    posted.append(video_id)
                    # Save immediately after sending so a restart won't resend it.
                    save_json("posted.json", posted)
                    save_json("scheduled.json", scheduled)

            updated_scheduled.append(item)

        save_json("scheduled.json", updated_scheduled)
        save_json("posted.json", posted)

    except Exception as e:
        print(f"Error in check_scheduled_start: {e}")




def build_rules_embed():
    rules_text = """Welcome, my miracles! I'm glad to have each and every one of you here, but you'll need to follow simple rules to be able to interact with others comfortably. My community is based on mutual understanding, love and support, and I'd prefer it to stay this way. 💗

1. All participants must comply with Discord's Terms of Service and Community Guidelines.
2. Be 16 or older! This server doesn't include any hostile materials, but I would like to keep an age line defined just in case.
3. Please avoid using inappropriate or offensive nicknames/avatars.
4. No swearing! I encourage my community to communicate in a polite way.
5. Bullying or any kind of discrimination are strictly prohibited.
6. No doxxing! Please avoid sending personal info about yourself, and don't try to fish it out of others.
7. No politics! This server was created as a safe space to unwind and share your interests.
8. Avoid parasocial behavior! I prefer our relationship to stay within "content creator-audience" borders.
9. Don't bring other people's drama in my space, I'm not into commenting it.
10. Don't spread hate towards me or my friends/collab partners on any of my platforms. I cherish all of them and wish our community to welcome them with the same warm attitude.
11. Don't feed my content to AI! I'm strictly against all GEN AI instruments, as they steal from real contentmakers.
12. Please keep comments, stream chat and server messages in English. We have an international community and I'd love you all to understand each other!
13. If you have any issues, please tag the mods (you can find their work windows in <#1456668824085725419>)! Don't DM them or me unless we approach you first!
14. Don't spam and don't use this server to promote yourself!

To access the server fully, react ✅! 
Please note that it means you agree to the rules and will take full responsibility for breaching them in the future! 

That's it, have a nice time and may the stars let us meet again!~ ✨"""

    embed = discord.Embed(
        title="✨🌸 COMMUNITY RULES 🌸✨",
        description=rules_text,
        color=RULES_EMBED_COLOR
    )
    return embed


def load_verification_state():
    if not os.path.exists(VERIFICATION_STATE_FILE):
        return {}
    try:
        with open(VERIFICATION_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_verification_state(state):
    with open(VERIFICATION_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


verification_setup_lock = asyncio.Lock()


async def ensure_rules_message():
    async with verification_setup_lock:
        state = load_verification_state()
        channel = bot.get_channel(RULES_CHANNEL_ID)
        if channel is None:
            try:
                channel = await bot.fetch_channel(RULES_CHANNEL_ID)
            except discord.NotFound:
                print(f"Verification setup: rules channel {RULES_CHANNEL_ID} was not found.")
                return
            except discord.Forbidden:
                print("Verification setup: Cosmopings cannot access the rules channel.")
                return
            except discord.HTTPException as e:
                print(f"Verification setup: could not fetch rules channel: {e}")
                return

        message = None
        saved_message_id = state.get("rules_message_id")
        if saved_message_id:
            try:
                message = await channel.fetch_message(int(saved_message_id))
            except discord.NotFound:
                message = None
            except discord.Forbidden:
                print("Verification setup: Cosmopings cannot read message history in the rules channel.")
                return
            except discord.HTTPException as e:
                print(f"Verification setup: could not fetch the saved rules message: {e}")
                return

        if message is None:
            try:
                message = await channel.send(embed=build_rules_embed())
                state["rules_message_id"] = message.id
                save_verification_state(state)
                print(f"Posted Community Rules embed: message {message.id}")
            except discord.Forbidden:
                print("Verification setup: Cosmopings needs View Channel, Send Messages, and Embed Links permissions.")
                return
            except discord.HTTPException as e:
                print(f"Verification setup: could not post the rules embed: {e}")
                return

        try:
            await message.edit(embed=build_rules_embed())
            print(f"Updated Community Rules embed: message {message.id}")
        except discord.Forbidden:
            print("Verification setup: Cosmopings cannot edit its rules message. Check channel permissions.")
            return
        except discord.HTTPException as e:
            print(f"Verification setup: could not update the rules embed: {e}")
            return

        try:
            await message.add_reaction(VERIFICATION_EMOJI)
        except discord.Forbidden:
            print("Verification setup: Cosmopings needs Add Reactions permission.")
        except discord.HTTPException as e:
            print(f"Verification setup: could not add the verification reaction: {e}")


@bot.event
async def on_member_join(member):
    if member.guild is None:
        return

    role = member.guild.get_role(NON_VERIFIED_ROLE_ID)
    if role is None:
        print(f"Verification: non-verified role {NON_VERIFIED_ROLE_ID} was not found.")
        return

    bot_member = member.guild.get_member(bot.user.id)
    print(
        "Verification diagnostics: "
        f"guild={member.guild.name} ({member.guild.id}), "
        f"member_guild={member.guild.id}, role_guild={role.guild.id}, "
        f"bot_member_found={bot_member is not None}, "
        f"manage_roles={bot_member.guild_permissions.manage_roles if bot_member else 'unknown'}, "
        f"bot_top_role={bot_member.top_role.name if bot_member else 'unknown'} "
        f"({bot_member.top_role.id if bot_member else 'unknown'}), "
        f"target_role={role.name} ({role.id}), "
        f"target_role_position={role.position}"
    )

    try:
        await member.add_roles(role, reason="New member must accept the community rules.")
        print(f"Assigned non-verified to {member} ({member.id})")
    except discord.Forbidden as e:
        bot_member = member.guild.me
        print(
            "Verification Forbidden while assigning non-verified: "
            f"member={member} ({member.id}), role={role.name} ({role.id}), "
            f"bot_top_role={bot_member.top_role.name if bot_member else 'unknown'} "
            f"({bot_member.top_role.id if bot_member else 'unknown'}), "
            f"status={getattr(e, 'status', 'unknown')}, "
            f"code={getattr(e, 'code', 'unknown')}, error={e!r}"
        )
    except discord.HTTPException as e:
        print(f"Verification: failed to assign non-verified to {member}: {e}")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None or payload.user_id == bot.user.id:
        return
    if payload.channel_id != RULES_CHANNEL_ID or payload.emoji.name != VERIFICATION_EMOJI:
        return

    state = load_verification_state()
    if payload.message_id != state.get("rules_message_id"):
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    member = payload.member
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

    if member.bot:
        return

    non_verified_role = guild.get_role(NON_VERIFIED_ROLE_ID)
    miracle_role = guild.get_role(MIRACLE_ROLE_ID)
    if miracle_role is None:
        print(f"Verification: miracle role {MIRACLE_ROLE_ID} was not found.")
        return

    try:
        if miracle_role not in member.roles:
            await member.add_roles(miracle_role, reason="Accepted the community rules.")
        if non_verified_role is not None and non_verified_role in member.roles:
            await member.remove_roles(non_verified_role, reason="Member completed rules verification.")
        print(f"Verified {member} ({member.id}): assigned miracle and removed non-verified.")
    except discord.Forbidden as e:
        bot_member = guild.me
        print(
            "Verification Forbidden while updating roles: "
            f"member={member} ({member.id}), "
            f"non_verified_role={non_verified_role.id if non_verified_role else 'missing'}, "
            f"miracle_role={miracle_role.id}, "
            f"bot_top_role={bot_member.top_role.name if bot_member else 'unknown'} "
            f"({bot_member.top_role.id if bot_member else 'unknown'}), "
            f"status={getattr(e, 'status', 'unknown')}, "
            f"code={getattr(e, 'code', 'unknown')}, error={e!r}"
        )
    except discord.HTTPException as e:
        print(f"Verification: failed to update roles for {member}: {e}")



@bot.event
async def on_ready():
    global uploads_playlist_id
    print(f"Logged in as {bot.user}")
    await ensure_rules_message()
    try:
        uploads_playlist_id = get_uploads_playlist()
    
    except Exception as e:
        print(f"Failed to fetch uploads playlist: {e}")


    if not check_youtube.is_running():
        check_youtube.start()
    if not check_scheduled_start.is_running():
        check_scheduled_start.start()

async def main():
    port = int(os.getenv("PORT", 25888))
    try:
        await start_web(bot=bot, port=port)
    except Exception as e:
        print(f"Failed to start web server on port {port}: {e}")

    token = os.getenv("DISCORD_TOKEN")
    if not token or token.strip() == "" or "your_" in token.lower():
        print("\n" + "="*60)
        print("CRITICAL: DISCORD_TOKEN is missing or not set!")
        print("Go to your bot-hosting.cloud panel -> Startup / Variables tab")
        print("   and paste your Discord Bot Token into DISCORD_TOKEN.")
        print("Web server is currently RUNNING on port 25888 (Website is alive!)")
        print("="*60 + "\n")
        while True:
            await asyncio.sleep(3600)

    try:
        await bot.start(token)
    except discord.errors.LoginFailure:
        print("\n" + "="*60)
        print("CRITICAL: Invalid Discord Bot Token!")
        print("Your DISCORD_TOKEN was rejected by Discord (401 Unauthorized).")
        print("   1. Open: https://discord.com/developers/applications")
        print("   2. Select your Bot -> Click 'Bot' on the left menu -> Click 'Reset Token'")
        print("   3. Paste the new token into DISCORD_TOKEN in bot-hosting.cloud")
        print("Web server is still RUNNING on port 25888 (Website is alive!)")
        print("="*60 + "\n")
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        print(f"Error during bot execution: {e}")
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
