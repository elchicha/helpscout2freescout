import logging

log_level = "INFO"
hs_logger = logging.getLogger('HelpScout Client')
logging.basicConfig(level=log_level)


fs_logger = logging.getLogger('FreeScout Client')