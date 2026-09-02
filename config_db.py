import os 
from dotenv import load_dotenv

load_dotenv()

database_name = os.environ.get('database_name')

config = {
    'host' : os.environ.get('host'),
    'user' : os.environ.get('user'),
    'password' : os.environ.get('password')
}