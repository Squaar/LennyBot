from functools import wraps
import discord
import asyncio
import logging
import shlex

logging.basicConfig(level=logging.INFO, format='%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)

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

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.channels = {}

    def find_channel(self, server_name, channel_name):
        for channel in self.get_all_channels():
            if channel.server.name == server_name and channel.name == channel_name:
                return channel
        raise ChannelNotFoundError(server_name, channel_name, 'Could not find %s/%s' % (server_name, channel_name))

    def channels_as_dict(self):
        channels = list(self.get_all_channels())
        d = dict((channel.server.name, {}) for channel in channels)
        for channel in channels:
            d[channel.server.name][channel.name] = channel
        return d

    async def on_ready(self):
        logger.info('Lennybot logged in: %s,%s' % (self.user.name, self.user.id))
        logger.info('Lennybot loop: %s' % id(asyncio.get_event_loop()))
        logger.info('private channels %s' % len(self.private_channels))

        try:
            await self.join_voice_channel(self.find_channel('Game Bois', 'Lenny land'))
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

    # !emojiate server channel message_id reactions
    @authenticate
    async def emojiate(self, message):
        command = shlex.split(message.content)
        target = await self.get_message(self.find_channel(command[1], command[2]), command[3])
        for char in command[4].lower():
            await self.add_reaction(target, self.a_to_emoji(char))

    # !clear-emojiate server channel message_id
    @authenticate
    async def clear_emojiate(self, message):
        command = shlex.split(message.content)
        target = await self.get_message(self.find_channel(command[1], command[2]), command[3])
        await self.clear_reactions(target)

    # !say server channel message
    @authenticate
    async def say(self, message, tts=False):
        command = shlex.split(message.content)
        command[3] = ' '.join(command[3:])
        await self.send_message(self.find_channel(command[1], command[2]), command[3], tts=tts)

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
            await self.send_message(message.channel, list(self.channels_as_dict()[command[1]].keys()))
        else:
            await self.send_message(message.channel, str(dict((server, list(channels.keys())) for server, channels in self.channels_as_dict().items())))

    @authenticate
    async def print_private_channels(self, message):
        # command = shlex.split(message.content)
        await self.send_message(list(self.private_channels)[0], 'lennybot online')
        logger.info('private channels %s' % len(self.private_channels))
        await self.send_message(message.channel, [list(map(lambda x: x.name, channel.recipients)) for channel in self.private_channels])
        # await self.send_message(message.channel, [channel.id for channel in self.private_channels])

    ##TODO: private messaging doesn't work, probably doing it wrong
    async def message_squaar(self, message):
        channel = filter(lambda x: x.id == '411407327938215949', self.private_channels)[0]
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


class ChannelNotFoundError(Exception):
    def __init__(self, server, channel, message=None):
        super().__init__(message)
        self.server = server
        self.channel = channel


if __name__ == '__main__':
    import os
    OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']
    LennyBot().run(OAUTH2_BOT_TOKEN)
