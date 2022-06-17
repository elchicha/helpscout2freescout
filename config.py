import logging
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log_level = "INFO"
hs_logger = logging.getLogger('HelpScout Client')
logging.basicConfig(level=log_level)
fs_logger = logging.getLogger('FreeScout Client')
main_logger = logging.getLogger('Migration Client')