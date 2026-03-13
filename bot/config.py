import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it to your .env file.")

# Your Telegram user ID - only this ID can use /admin
ADMIN_ID: int = 961369378

# Protected number - cannot be used as a test target by anyone
PROTECTED_NUMBER: str = "87075046930"

# Default daily test limit for new users
DEFAULT_DAILY_LIMIT: int = 10

# Dashboard update interval in seconds
DASHBOARD_UPDATE_INTERVAL: float = 2.0

# Proxy file path relative to project root
PROXY_FILE: str = "proxies.txt"

# SQLite database file path
DB_FILE: str = "bot_data.db"

# Default workers shown in wizard
DEFAULT_WORKERS: int = 4

# Timezone for midnight reset (IST = UTC+5:30)
IST_OFFSET_HOURS: float = 5.5
