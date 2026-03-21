import os
from dotenv import load_dotenv

load_dotenv()

API_ID: int = int(os.environ["API_ID"])
API_HASH: str = os.environ["API_HASH"]
SESSION_STRING: str = os.environ["SESSION_STRING"]
MONGO_URI: str = os.environ["MONGO_URI"]
CONTROL_GROUP_ID: int = int(os.environ["CONTROL_GROUP_ID"])