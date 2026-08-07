import os 
from dotenv import load_dotenv

load_dotenv()

database_name = 'quiz'

config = {
    'host' : os.environ.get('host'),
    'user' : os.environ.get('user'),
    'password' : os.environ.get('password')
}