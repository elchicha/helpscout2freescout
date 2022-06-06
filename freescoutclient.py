from config import *
import json
import requests
from dotenv import load_dotenv
import os


load_dotenv()
FS_API_KEY = os.getenv("FREESCOUT_API")
FS_URL = os.getenv("FREESCOUT_URL")
HEADERS = { 
    "Content-Type": "application/json",
    "X-FreeScout-API-Key": FS_API_KEY
    }
USERS_ENDPOINT = "api/users"
MAILBOX_ENDPOINT = "api/mailboxes"
CONVERSATIONS_ENDPOINT = "api/conversations"


class FreeScoutClient:
    def __init__(self):
        fs_logger.info("Creating new FreeScout client.")
        self.conf_data = None

    def get_mailboxes(self):
        data = {}
        r = requests.get(FS_URL+"/"+MAILBOX_ENDPOINT, headers=HEADERS, json=data)
        results = r.json()
        return results["_embedded"]["mailboxes"]
    
    def get_users(self):
        data = {}
        r = requests.get(FS_URL+"/"+USERS_ENDPOINT, headers=HEADERS, json=data)
        results = r.json()
        return results["_embedded"]["users"]
    
    def create_conversation(self, fs_conversation):
        json_data = fs_conversation.get_json_data()
        r = requests.request(method="POST",
                            url=FS_URL+"/"+CONVERSATIONS_ENDPOINT, 
                            headers=HEADERS,
                            data=json_data)
        if r.status_code == 200:
            results = r.json()
            if results["message"] == "Error occurred":
                fs_logger.error(results["_embedded"]["errors"][0]["message"])
        if r.status_code in [400]:
            fs_logger.error(r.json())
            fs_logger.error(json_data)
        if r.status_code == 201:
            result = r.json()
            conversation_id = result["id"]
            self.update_conversation_tags(conversation_id, fs_conversation.tags)
            return conversation_id
    
    def update_conversation_tags(self, convId, tags):
        data_tag = []
        for tag in tags:
            data_tag.append(tag["tag"])
        data = {"tags":data_tag}
        json_data = json.dumps(data)
        r = requests.request(method="PUT",
                    url=f"{FS_URL}/{CONVERSATIONS_ENDPOINT}/{convId}/tags",
                    headers=HEADERS,
                    data=json_data)
    
    def list_conversations(self):
        r = requests.get(FS_URL+"/"+CONVERSATIONS_ENDPOINT, headers=HEADERS)
        conversations = r.json()
        return conversations


class FreeScoutConversation:
    def __init__(self):
        self.type = None
        self.mailboxId = None
        self.subject = None
        self.customer = None #Object
        self.threads = [] #Object
        self.imported = True
        self.status = None
        self.createdAt = None
        self.closedAt = None
        self.closedBy = None
        self.tags = []
        self.conf_data = None
        self.assignTo = None

    def lookup_user(self, hs_id):
        for user in self.conf_data["user_mapping"]:
            if user["hs_id"] == hs_id:
                return user["fs_id"]
        fs_logger.error(f"Help Scout User ID not found: {hs_id}")
    
    def get_json_data(self):
        data = {
            "type": self.type,
            "mailboxId": self.mailboxId,
            "subject": self.subject,
            "customer": self.customer,
            "threads": self.threads,
            "imported": self.imported,
            "status": self.status,
            "createdAt": self.createdAt,
            "closedAt": self.closedAt,
            "closedBy": self.closedBy
        }
        json_data = json.dumps(data)
        return json_data

    def append_threads(self, conv_threads):
        for conv_thread in conv_threads:
            fs_thread = ConversationThread()
            fs_thread.conf_data = self.conf_data
            fs_thread.create_from_HelpScout_thread(conv_thread)
            fs_thread_data = fs_thread.get_data()
            self.threads.append(fs_thread_data)


class ConversationThread:
    def __init__(self):
        self.type = ""
        self.text = ""
        self.customer = {}
        self.user = None
        self.imported = True
        self.status = ""
        self.cc = []
        self.bcc = []
        self.createdAt = ""
        self.attachments = []
        self.conf_data = None

    def lookup_user(self, hs_id):
        for user in self.conf_data["user_mapping"]:
            if user["hs_id"] == hs_id:
                return user["fs_id"]    

    def create_from_HelpScout_thread(self, hs_thread):
        self.type = hs_thread["type"]
        self.createdAt = hs_thread["createdAt"]
        if self.type == "lineitem":
            self.type = "note"
            self.text = hs_thread["action"]["text"]
            self.user = self.lookup_user(hs_thread["createdBy"]["id"])
        elif self.type == "phone":
            self.type = "note"
            self.text = hs_thread["body"]
        elif self.type in ["note", "customer", "message", "email"]:
            self.user = self.lookup_user(hs_thread["createdBy"]["id"])
            self.text = hs_thread["body"]
            self.customer = {
                "email": hs_thread["customer"]["email"],
                "firstName": hs_thread["customer"]["first"],
                "lastName": hs_thread["customer"]["last"]
            }
    
    def get_data(self):
        """Return JSON data object with Thread information."""
        data = {
            "type": self.type,
            "text": self.text,
            "customer": self.customer,
            "user": self.user,
            "imported": self.imported,
            "status": self.status,
            "cc": self.cc,
            "bcc": self.bcc,
            "createdAt": self.createdAt,
            "attachments": self.attachments
        }

        json_data = json.dumps(data)
        return data