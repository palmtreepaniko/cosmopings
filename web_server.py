import os
import json
import time
from aiohttp import web

START_TIME = time.time()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "web", "index.html")

def load_json_safe(filename):
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def create_app(bot=None):
    app = web.Application()

    async def handle_index(request):
        if os.path.exists(HTML_PATH):
            with open(HTML_PATH, "r", encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html")
        return web.Response(text="<h1>Cosmopings is Online</h1><p>web/index.html not found</p>", content_type="text/html")

    async def handle_health(request):
        """Endpoint for UptimeRobot / uptime monitors to keep the bot alive."""
        return web.json_response({
            "status": "healthy",
            "service": "cosmopings",
            "bot_online": bot.is_ready() if bot else True,
            "uptime_seconds": int(time.time() - START_TIME),
            "timestamp": int(time.time())
        })

    async def handle_status(request):
        """Live API endpoint consumed by the frontend."""
        posted = load_json_safe("posted.json")
        scheduled = load_json_safe("scheduled.json")

        ping_ms = 0.0
        bot_user = "Cosmopings#0000"
        online = False

        if bot:
            online = bot.is_ready()
            ping_ms = round(bot.latency * 1000, 1) if bot.latency and bot.latency > 0 else 38.0
            if bot.user:
                bot_user = str(bot.user)
        else:
            online = True
            ping_ms = 35.0

        return web.json_response({
            "online": online,
            "bot_user": bot_user,
            "ping_ms": ping_ms,
            "uptime_seconds": int(time.time() - START_TIME),
            "posted_count": len(posted),
            "scheduled_count": len(scheduled),
            "recent_posted": posted[-6:] if posted else [],
            "scheduled": scheduled
        })

    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/ping", handle_health)
    app.router.add_get("/api/status", handle_status)

    return app

async def start_web(bot=None, port=None):
    if port is None:
        port = int(os.getenv("PORT", 25888))
    
    app = create_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server successfully started on http://0.0.0.0:{port}")
    print(f"🔗 Public URL: https://2ekkusjbrm.apps.bot-hosting.cloud (Port :{port})")
    return runner

if __name__ == "__main__":
    port = int(os.getenv("PORT", 25888))
    print(f"Starting standalone Cosmopings Web Server on port {port}...")
    web.run_app(create_app(None), host="0.0.0.0", port=port)
