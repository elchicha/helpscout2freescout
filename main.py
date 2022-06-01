from helpscoutclient import HelpScoutClient
from freescoutclient import FreeScoutClient
import os
from dotenv import load_dotenv

load_dotenv()
hs_client = HelpScoutClient(os.getenv("APP_ID"), os.getenv("APP_SECRET"))
fs_client = FreeScoutClient()


