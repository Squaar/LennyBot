from functools import wraps
import discord
import asyncio
import logging
import shlex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# discord_client = discord.Client()
# channels = {}
authorized_users = [135265595925987328, 137772624133488641]

##TODO: rewrite so methods take specific args, call with info from the message
# this way we can call them from other places too
# but it also needs a reference to the channel
# can we just add discord_client methods to the event loop from the service directly?


##TODO: this could be done smarter
def authenticate(func):
    @wraps(func)
    def with_authentication(*args, **kwargs):
        ##TODO: throw this in a big ol' or
        if len(args) > 0 and type(args[1]) == discord.message.Message and int(args[1].author.id) in authorized_users:
            return func(*args, **kwargs)
        elif kwargs.get('auth_user') in authorized_users or kwargs.get('uath_user') in map(str, authorized_users):
            return func(*args, **kwargs)
        else:
            raise AuthenticationError('Couldn\'t authenticate: %s; %s; %s' % (func.__name__, args, kwargs), func)
    return with_authentication


class LennyBot(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.channels = {}

    async def on_ready(self):
        logger.info('Lennybot logged in: %s,%s' % (self.user.name, self.user.id))
        logger.info('Lennybot loop: %s' % id(asyncio.get_event_loop()))
        for channel in self.get_all_channels():
            self.channels['%s/%s' % (channel.server.name, channel.name)] = channel

        try:
            await self.join_voice_channel(self.channels['Game Bois/Lenny land'])
        except RuntimeError as e:
            logger.warn(e)

    ##TODO: private messaging
    async def on_message(self, message):
        logger.info('%s/%s[%s]: %s' % (message.server, message.channel, message.author, message.content.encode('utf-8')))
        if message.content.startswith('!emojiate'):
            await self.emojiate(message)
        elif message.content.startswith('!emojify'):
            await self.emojify(message)
        elif message.content.startswith('!clear-emojiate'):
            await self.clear_emojiate(message)
        elif message.content.startswith('!channels'):
            await self.print_channels(message)
        elif message.content.startswith('!private-channels'):
            await self.print_private_channels(message)
        elif message.content.startswith('!say'):
            await self.say(message)
        elif message.content.startswith('!tts'):
            await self.say(message, tts=True)

    # !emojiate server/channel message_id reactions
    @authenticate
    async def emojiate(self, message):
        command = shlex.split(message.content)
        target = await self.get_message(self.channels[command[1]], command[2])
        for char in command[3].lower():
            await self.add_reaction(target, self.a_to_emoji(char))

    # !clear-emojiate server/channel message_id
    @authenticate
    async def clear_emojiate(self, message):
        command = shlex.split(message.content)
        target = await self.get_message(self.channels[command[1]], command[2])
        await self.clear_reactions(target)

    # !say server/channel message
    @authenticate
    async def say(self, message, tts=False):
        command = shlex.split(message.content)
        command[2] = ' '.join(command[2:])
        await self.send_message(self.channels[command[1]], command[2], tts=tts)

    # !emojify message
    @authenticate
    async def emojify(self, message):
        command = shlex.split(message.content)
        command[1] = ' '.join(command[1:])
        logger.info(command[1])
        await self.send_message(message.channel, self.str_to_emoji(command[1]))

    # !channels [server]
    @authenticate
    async def print_channels(self, message):
        command = shlex.split(message.content)
        if len(command) > 1:
            command[1] = ' '.join(command[1:])
            filtered = filter(lambda x: x.lower().startswith(command[1].lower()), list(self.channels.keys()))
            await self.send_message(message.channel, [channel.split('/')[1] for channel in filtered])
        else:
            await self.send_message(message.channel, list(self.channels.keys()))

    @authenticate
    async def print_private_channels(self, message):
        # command = shlex.split(message.content)
        await self.send_message(message.channel, [list(map(lambda x: x.name, channel.recipients)) for channel in self.private_channels])
        # await self.send_message(message.channel, [channel.id for channel in self.private_channels])

    async def message_squaar(self, message):
        channel = filter(lambda x: x.id == '411407327938215949', self.private_channels)[0]
        logger.info('messaging squaar: %s' % message)
        await self.send_message(channel, message)


def str_to_emoji(string):
    string = string.lower()
    result = ''
    for char in string:
        result += a_to_emoji(char)
    return result


def a_to_emoji(char):
    if type(char) != str or len(char) != 1:
        raise ValueError('Char must be a 1 character string.')
    char = char.lower()
    if ord(char) >= ord('a') and ord(char) <= ord('z'):
        return chr(127365 + ord(char))
    return char


class AuthenticationError(Exception):
    def __init__(self, message=None, func=None):
        super().__init__(message)
        self.func = func


if __name__ == '__main__':
    import os
    OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']
    LennyBot().run(OAUTH2_BOT_TOKEN)
