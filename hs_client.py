from dotenv import load_dotenv
from helpscout import HelpScout
from credentials import *


class HSClient:
    def __init__(self, app_id, app_secret):
        logging.debug("Creating new HelpScout client.")
        self.client = HelpScout(app_id=app_id, app_secret=app_secret)
    
    def get_conversations_by_date_range(self, start_date, end_date):
        params = f"query=(createdAt:[{start_date} TO {end_date}])"
        conversations = self.client.conversations.get(params=params)

        return conversations

    def get_conversations_last_month(self):
        params = f"query=(createdAt:[2022-05-01T00:00:00Z/MONTH TO *])&page=1"
        conversations = self.client.conversations.get(params=params)
        print(f"Found {len(conversations)} conversations")
        return conversations

    def get_threads_by_conversation(self, conversation_id):
        threads = self.client.conversations[conversation_id].threads.get()
        for thread in threads:
            print(thread.id, thread.type)


class HSConversation:
    def __init__(self):
        self.type = None
        self.mailboxId = None
        self.subject = None
        self.customer = None
        self.threads = None
    
    def __str__(self):
        return(self.subject)


if __name__ == "__main__":
    hs_client = HSClient(APP_ID, APP_SECRET)