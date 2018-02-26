
import lennybot
import lennyservice
import logging
import threading
import asyncio
import os

##TODO: put some timestamps on this log
logging.basicConfig(level=logging.INFO, format='%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)

OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']


def run_lennybot_thread(bot, event_loop):
    bot.loop = event_loop
    bot.run(OAUTH2_BOT_TOKEN)


if __name__ == '__main__':
    bot_loop = asyncio.get_event_loop()
    bot = lennybot.LennyBot(loop=bot_loop)
    lennybot_thread = threading.Thread(name='t_lennybot', target=run_lennybot_thread, args=(bot, bot_loop))
    lennybot_thread.start()
    lennyservice.LennyService(bot, __name__).run(use_reloader=False, host='0.0.0.0')  # Reloader is BAD for threads!
