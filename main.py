from re import T
from helpscoutclient import HelpScoutClient
from freescoutclient import *
import os
from dotenv import load_dotenv
import json
import tqdm
from config import *
import asyncio


class Main:
    def __init__(self):
        load_dotenv()
        self.hs_client = HelpScoutClient(os.getenv("HELPSCOUT_APP_ID"), 
                            os.getenv("HELPSCOUT_APP_SECRET"))
        self.fs_client = FreeScoutClient()
        self.screen_width = 40
        self.config_file = "config.json"
        self.conf_data = None

    def welcome_msg(self):
        print("".center(self.screen_width, "="))
        print("HelpScout -> FreeScout Migration".center(self.screen_width))
        print("V 1.0 - 2022".center(self.screen_width))
        print("Luis Lopez-Echeto".rjust(self.screen_width))
        print("luis@thesvschool.com".rjust(self.screen_width))
        print("github: @elchicha".rjust(self.screen_width))
        print("".center(self.screen_width, "="))
        print()
    
    def load_config(self):
        """Load config.json file with migration settings"""
        with open(self.config_file) as conf_file:
            self.conf_data = json.load(conf_file)
        self.fs_client.conf_data = self.conf_data

    def get_HS_conversations(self):
        """Obtain HelpScout conversations for date range specified in config file."""
        conversations = self.hs_client.get_conversations_created_by_range(
                self.conf_data["start_date"],
                self.conf_data["end_date"],
                self.conf_data["hs_mailbox_id"],
                self.conf_data["time_zone"])
        return conversations
    
    async def create_FS_conversations(self, hs_conversations):
        """Create new FreeScout conversations from HelpScout conversations."""
        fs_logger.debug("Creating FreeScout conversations.")
        async with aiohttp.ClientSession() as session:
            tasks = []
            for hsc in hs_conversations:
                fsc = FreeScoutConversation()
                fsc.type = hsc.type
                fsc.conf_data = self.conf_data
                fsc.mailboxId = self.conf_data["fs_mailbox_id"]
                fsc.subject = ""
                if hasattr(hsc, "subject"):
                    fsc.subject = hsc.subject
                fsc.status = hsc.status
                fsc.tags = hsc.tags
                if hsc.type == "phone":
                    fsc.customer = {
                    "firstName": hsc.primaryCustomer["first"],
                    "lastName": hsc.primaryCustomer["last"]
                    }
                else:
                    fsc.customer = {"email": hsc.primaryCustomer.get("email", "fremont+noemail@thecoderschool.com"),
                                    "firstName": hsc.primaryCustomer["first"],
                                    "lastName": hsc.primaryCustomer["last"]
                                    }
                fsc.createdAt = hsc.createdAt
                if hasattr(hsc, "assignee"):
                    fsc.assignTo = fsc.lookup_user(hsc.assignee["id"])
                if hsc.status == "closed":
                    fsc.closedAt = hsc.closedAt
                fsc.append_threads(hsc._embedded["threads"], self.hs_client.client.access_token)
                tasks.append(asyncio.ensure_future(self.fs_client.create_conversation(fsc)))

            # await asyncio.gather(*tasks)
            conversations = [await f for f in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks), ncols=82)]
            # return conversations

    def run(self):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        self.welcome_msg()
        self.load_config()
        cnvs = self.get_HS_conversations()
        asyncio.run(self.create_FS_conversations(cnvs))
        self.fs_client.list_conversations()


app = Main()
app.run()