from . import lennybot
from . import lennyservice
import logging
import threading
import asyncio
import os

##TODO: put some timestamps on this log
logging.basicConfig(level=logging.INFO, format='%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)

OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']


# asyncio loses its event loop when you run it in a thread
# passing the loop through bot's constructor still makes it disappear
def run_lennybot_thread(bot, event_loop):
    lennybot.asyncio.set_event_loop(event_loop)  # must set event loop in asyncio module on linux
    bot.run(OAUTH2_BOT_TOKEN)

def main():
    # bot_loop = asyncio.get_event_loop()
    # bot = lennybot.LennyBot()
    # lennybot_thread = threading.Thread(name='t_lennybot', target=run_lennybot_thread, args=(bot, bot_loop))
    # lennybot_thread.start()
    # lennyservice.LennyService(bot, __name__).run(use_reloader=False, host='0.0.0.0')  # Reloader is BAD for threads!

    bot_loop = asyncio.get_event_loop()
    bot = lennybot.LennyBot()
    run_lennybot_thread(bot, bot_loop)

if __name__ == '__main__':
    main()
