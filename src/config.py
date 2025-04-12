import os

db_user = os.getenv("POSTGRES_USER", "myuser")
db_password = os.getenv("POSTGRES_PASSWORD", "mypassword")
db_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
db_port = os.getenv("POSTGRES_PORT", "5432")
db_database = os.getenv("POSTGRES_DB", "scalper")
bot_token = os.getenv("BOT_TOKEN", "")

TRON_NODE = os.getenv("TRON_NODE", "https://api.trongrid.io")
API_KEY_TRON = os.getenv("API_KEY_TRON", "32c30004-baf4-4275-aeea-409aba64c206")