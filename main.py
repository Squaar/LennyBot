
import lennybot
import logging
import threading
import lennyservice
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(threadname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']

bot_loop = lennybot.discord_client.loop
lennybot_thread = threading.Thread(name='lennybot', target=lennybot.discord_client.run, args=(OAUTH2_BOT_TOKEN,))
lennybot_thread.start()
lennyservice.app.run(use_reloader=False)  # Reloader is BAD for threads!
