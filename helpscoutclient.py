from helpscout import HelpScout
from time import timezone
from config import *

from datetime import datetime, timedelta

class HelpScoutClient:
    def __init__(self, app_id, app_secret):
        hs_logger.info("Creating new HelpScout client.")
        self.client = HelpScout(app_id=app_id, app_secret=app_secret)

    def get_conversations_created_since(self, create_date):
        year = create_date.strftime("%Y")
        month = create_date.strftime("%m")
        day = create_date.strftime("%d")
        params = f"query=(createdAt:[{year}-{month}-{day}T00:00:00Z TO *])"
        hs_logger.debug(f"Query params: {params}")
        conversations = self.client.conversations.get(params=params)
        hs_logger.info(f"Found {len(conversations)} conversations")
        return conversations

    def get_previous_month(self):
        first_day_this_month = datetime.now().replace(day=1)
        last_month = first_day_this_month - timedelta(days=1)
        hs_logger.debug(f"Current month: {first_day_this_month.month}  Last month: {last_month.month}")
        return last_month.month

    def get_conversations_last_month(self):
        prev_month = self.get_previous_month()
        start_date = datetime.now().replace(day=1, month=prev_month)
        return self.get_conversations_created_since(start_date)

    def get_conversations_last_week(self):
        start_date = datetime.now() - timedelta(days=7)
        return self.get_conversations_created_since(start_date)
    
    def get_conversations_by_year(self, year):
        hs_logger.info(f"Getting conversations for year {year}.")
        params = f"query=(createdAt:[{year}-01-01T00:00:00Z/YEAR TO {year+1}-01-01T00:00:00Z/YEAR])"
        hs_logger.debug(f"Query params: {params}")
        conversations = self.client.conversations.get(params=params)
        hs_logger.info(f"Found {len(conversations)} conversations")
        return conversations

    def get_threads_by_conversation(self, conversation_id):
        threads = self.client.conversations[conversation_id].threads.get()



class HSConversation:
    def __init__(self):
        self.type = None
        self.mailboxId = None
        self.subject = None
        self.customer = None
        self.threads = None
    
    def __str__(self):
        return(self.subject)