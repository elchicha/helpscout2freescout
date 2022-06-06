from mailbox import Mailbox
from helpscout import HelpScout
from time import timezone
from config import *
from datetime import datetime, timezone
import pytz
from datetime import datetime, timedelta

class HelpScoutClient:
    def __init__(self, app_id, app_secret):
        hs_logger.info("Creating new HelpScout client.")
        self.client = HelpScout(app_id=app_id, app_secret=app_secret)

    def get_conversations_created_by_range(self, start_date, end_date, tz=pytz.utc._tzname):
        start_date_utc = self.convert_date_to_utc(start_date, tz)
        end_date_utc = self.convert_date_to_utc(end_date, tz)
        hs_logger.info(f"Getting conversations for date range {start_date_utc} to {end_date_utc}")
        params = {"query" : f"(createdAt:[{start_date_utc} TO {end_date_utc}])",
                "status": "all",
                "embed": "threads"}
        hs_logger.debug(f"Query: {params}")
        conversations = self.client.conversations.get(params=params)
        hs_logger.info(f"Found {len(conversations)} conversations.")
        return conversations

    def get_conversations_created_since(self, create_date, tz=pytz.utc._tzname):
        create_date_utc = self.convert_date_to_utc(create_date, tz)
        hs_logger.info(f"Getting conversations for today {create_date_utc}.")
        params = f"query=(createdAt:[{create_date_utc} TO *])"
        hs_logger.debug(f"Query: {params}.")
        conversations = self.client.conversations.get(params=params)
        hs_logger.info(f"Found {len(conversations)} conversations.")
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

    def get_conversations_today(self):
        start_date = datetime.now().strftime("%Y-%m-%d 00:00:00")
        return self.get_conversations_created_since(start_date)
    
    def get_conversations_by_year(self, year):
        hs_logger.info(f"Getting conversations for year {year}.")
        params = f"query=(createdAt:[{year}-01-01T00:00:00Z/YEAR TO {year+1}-01-01T00:00:00Z/YEAR])"
        hs_logger.debug(f"Query: {params}")
        conversations = self.client.conversations.get(params=params)
        hs_logger.info(f"Found {len(conversations)} conversations")
        return conversations

    def get_threads_by_conversation(self, conversation_id):
        threads = self.client.conversations[conversation_id].threads.get()
    
    def list_mailboxes(self):
        hit = self.client.hit("mailboxes", "get")
        result = []
        for mailbox in hit[0]["mailboxes"]:
            result.append(HelpScoutMailbox(mailbox["name"], mailbox["id"]))
        return result
        
    def convert_date_to_utc(self, date_in, tz):
        hs_logger.info(f"Convert date: {date_in} Timezone {tz} to UTC.")
        date_orig = datetime.strptime(date_in, "%Y-%m-%d %H:%M:%S")
        local_tz = pytz.timezone(tz)
        date_orig = local_tz.localize(date_orig)
        date_utc = date_orig.astimezone(timezone.utc)
        hs_logger.debug(f"Date converted {date_in}({tz}) to UTC: {date_utc}")
        return date_utc.isoformat().replace("+00:00", "Z")
    
    def get_conversations_by_subject(self, subject_msg):
        params = {"subject" : subject_msg}
        conversations = self.client.conversations.get(params=params)
        return conversations
    
    def get_conversation(self, conversation_id):
        return self.client.hit('conversations', 'get', resource_id=conversation_id)

    def get_users(self):
        return self.client.hit("users", "get")


class HelpScoutMailbox:
    def __init__(self, name, id):
        self.name = name
        self.id = id
    
    def __str__(self):
        return f"{self.id} :: {self.name}"


class HSConversation:
    def __init__(self):
        self.type = None
        self.mailboxId = None
        self.subject = None
        self.customer = None
        self.threads = None
    
    def __str__(self):
        return(self.subject)