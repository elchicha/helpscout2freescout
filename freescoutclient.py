from config import *
import requests
from dotenv import load_dotenv
import os

USERS_ENDPOINT = 'https://mail.tcsfmt.com/api/users'
MAILBOX_ENDPOINT = 'https://mail.tcsfmt.com/api/mailboxes'
CONVERSATION_ENDPOINT = ""
load_dotenv()
FS_API_KEY = os.getenv("FREESCOUT_API")

HEADERS = { 
    "Content-Type": "application/json",
    "X-FreeScout-API-Key": FS_API_KEY
    }


class FreeScoutClient:
    def __init__(self):
        fs_logger.info("Creating new HelpScout client.")

    def get_mailboxes(self):
        data = {}
        r = requests.get(MAILBOX_ENDPOINT, headers=HEADERS, json=data)
        results = r.json()
        return results["_embedded"]["mailboxes"]
    
    def get_users():
        data = {}
        r = requests.get(USERS_ENDPOINT, headers=HEADERS, json=data)
        results = r.json()
        return results["_embedded"]["users"]


class User:
    def __init__(self, id, email):
        self.id = id
        self.email = email
    
    def __str__(self):
        return f"{self.email} (id:{self.id})"