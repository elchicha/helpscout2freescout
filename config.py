import logging

log_level = "DEBUG"
hs_logger = logging.getLogger('HelpScout Client')
logging.basicConfig(level=log_level)
fs_logger = logging.getLogger('FreeScout Client')
main_logger = logging.getLogger('Migration Client')