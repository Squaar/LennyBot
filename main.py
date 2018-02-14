
import lennybot
import logging
import threading
import lennyservice
import os

##TODO: put some timestamps on this log
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(threadname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']


# asyncio loses its event loop when you run it in a thread
def run_lennybot_thread(bot_token, event_loop):
    lennybot.asyncio.set_event_loop(event_loop)
    lennybot.discord_client.run(bot_token)


if __name__ == '__main__':
    bot_loop = lennybot.discord_client.loop
    lennybot_thread = threading.Thread(name='lennybot', target=run_lennybot_thread, args=(OAUTH2_BOT_TOKEN, bot_loop))
    lennybot_thread.start()
    lennyservice.app.run(use_reloader=False, host='0.0.0.0')  # Reloader is BAD for threads!
