import os 
from dotenv import load_dotenv

load_dotenv()

proxy_token = os.environ.get('proxy_token')
telegram_token = os.environ.get('telegram_token')
