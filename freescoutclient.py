import aiohttp
import asyncio
import base64
import json
import os
import re
import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from dotenv import load_dotenv
from urllib.parse import urlparse
from config import *


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
        self.session = requests.Session()

    def get_mailboxes(self):
        data = {}
        r = self.session.get(FS_URL+"/"+MAILBOX_ENDPOINT, headers=HEADERS, json=data)
        results = r.json()
        return results["_embedded"]["mailboxes"]
    
    def get_users(self):
        data = {}
        r = self.session.get(FS_URL+"/"+USERS_ENDPOINT, headers=HEADERS, json=data)
        results = r.json()
        return results["_embedded"]["users"]

    async def create_conversation(self, fs_conversation):
        async with aiohttp.ClientSession() as session:
            json_data = fs_conversation.get_json_data()        
            async with session.request(
                method="POST", url=FS_URL+"/"+CONVERSATIONS_ENDPOINT, 
                headers=HEADERS,
                data=json_data) as r:
                if r.status == 200:
                    results = await r.json()
                    if results["message"] == "Error occurred":
                        fs_logger.error(results["_embedded"]["errors"][0]["message"])
                if r.status == 201:
                    result = await r.json()
                    conversation_id = result["id"]
                    if fs_conversation.tags:
                        self.update_conversation_tags(conversation_id, fs_conversation.tags)
                    return conversation_id
                if r.status in [400]:
                    fs_logger.error(await r.json())
                    fs_logger.error(json_data)
    
    def update_conversation_tags(self, convId, tags):
        data_tag = [tag["tag"] for tag in tags]
        data = {"tags":data_tag} 
        json_data = json.dumps(data)
        r = self.session.request(method="PUT",
                    url=f"{FS_URL}/{CONVERSATIONS_ENDPOINT}/{convId}/tags",
                    headers=HEADERS,
                    data=json_data)

    def update_conversation_asignee(self, convId, assignTo, byUser, updatedAt):
        data = {"byUser": byUser,
                "assignTo":assignTo,
                "createdAt": updatedAt} 
        json_data = json.dumps(data)
        r = self.session.request(method="PUT",
                    url=f"{FS_URL}/{CONVERSATIONS_ENDPOINT}/{convId}",
                    headers=HEADERS,
                    data=json_data)
        if r.status_code == 400:
            result = r.json()
            fs_logger.error(result)

    def list_conversations(self):
        r = self.session.get(FS_URL+"/"+CONVERSATIONS_ENDPOINT, headers=HEADERS)
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
            "closedBy": self.closedBy,
            "assignTo": self.assignTo
        }
        json_data = json.dumps(data)
        return json_data

    def append_threads(self, conv_threads, hs_access_token=None):
        for conv_thread in conv_threads:
            fs_thread = ConversationThread()
            fs_thread.hs_access_token = hs_access_token
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
        self.hs_access_token = None
        self.action = None

    def lookup_user(self, hs_id):
        for user in self.conf_data["user_mapping"]:
            if user["hs_id"] == hs_id:
                return user["fs_id"]
        return self.conf_data["user_mapping"][0]["fs_id"] 

    def create_from_HelpScout_thread(self, hs_thread):
        self.type = hs_thread["type"]
        self.createdAt = hs_thread["createdAt"]
        self.bcc = hs_thread["bcc"]
        self.cc = hs_thread["cc"]
        if self.type == "lineitem":
            self.action = hs_thread["action"]
            self.type = "note"
            self.text = hs_thread["action"]["text"]
            self.user = self.lookup_user(hs_thread["createdBy"]["id"])
        elif self.type == "phone":
            self.type = "note"
            self.text = hs_thread["body"]
            self.user = self.lookup_user(hs_thread["createdBy"]["id"])
            self.customer = {
                "email": hs_thread["customer"]["email"],
                "firstName": hs_thread["customer"]["first"],
                "lastName": hs_thread["customer"]["last"]
            }
        elif self.type in ["note", "customer", "message", "email"]:
            self.user = self.lookup_user(hs_thread["createdBy"]["id"])
            self.text = hs_thread["body"]
            self.customer = {
                "email": hs_thread["customer"]["email"],
                "firstName": hs_thread["customer"]["first"],
                "lastName": hs_thread["customer"]["last"]
            }
        hs_attachments = hs_thread["_embedded"]["attachments"]
        if len(hs_attachments) > 0:
            for file in hs_attachments:
                file_data = self.download_attachment(
                            file["_links"]["data"]["href"],
                            self.hs_access_token)
                attachment = {"fileName": file["filename"],
                            "mimeType": "application/hal+json",
                            "data": file_data}
                self.attachments.append(attachment)
        self.download_embedded_image(self.text)
    
    def download_attachment(self, file_url, access_token):
        head = {"Authorization": "Bearer "+access_token,
        "Content-Type": "application/json"}
        resp = requests.get(file_url, stream=True, verify=False, headers=head)
        if resp.status_code == requests.codes.ok:
            file_data_json = resp.json()
            return file_data_json["data"]
    
    def download_embedded_image(self, body, provider="cloudfront"):
        """Look in body attribute for img src embedded images hosted on third party server."""
        fs_logger.debug(f"BS parsing: {body}")
        # Some content does not have HTML but may have / characters making it look like a filename.
        import warnings
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
        soup = BeautifulSoup(body, "lxml")
        images = soup.find_all("img")
        for image in images:
            img_url = image["src"]
            if provider not in img_url:
                continue
            regex = "^.*/(\w+\.\w+)"
            imgs = re.findall(regex, img_url)
            if len(imgs) > 0:
                img_filename = imgs[0]
            head = {"Authorization": "Bearer "+self.hs_access_token,
                "Content-Type": "application/json"}
            try:
                resp = requests.get(img_url, stream=True, verify=False, timeout=3, headers=head)
                if resp.status_code == requests.codes.ok:
                    signatures = [{
                        "signature": "iVBORw0KGgo",
                        "mimeType": "image/png"
                        },{
                        "signature": "JVBERi0",
                        "mimeType": "application/pdf"
                        },{
                        "signature": "R0lGODdh",
                        "mimeType": "image/gif"
                        },{
                        "signature": "iVBORw0KGgo",
                        "mimeType": "image/png"
                        },{
                        "signature": "/9j/",
                        "mimeType": "image/jpg"
                        },
                    ]
                    img_b64 = base64.b64encode(resp.content).decode("utf-8")
                    for signature in signatures:
                        if signature["signature"] in img_b64:
                            content_type = signature["mimeType"]
                            attachment = {
                                    "fileName": img_filename,
                                    "mimeType": content_type,
                                    "data": img_b64
                                }
                            self.attachments.append(attachment)
                            break
                    # fs_logger.error(f"Content-Type not detected for embedded image: {img_url}")
            except Exception as e:
                fs_logger.error(f"{e.args[0]} Error accessing {img_url}")
    
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
            "attachments": self.attachments,
            "action": self.action
        }

        json_data = json.dumps(data)
        return data