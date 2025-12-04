import logging
import time
logger = logging.getLogger("cmd1")
#logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


logger.info('cmd1, sleep for 15')
time.sleep(15)
