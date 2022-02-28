import discord
import logging
import shlex
import werkzeug
from functools import wraps
from .resources import RESOURCE_DICTIONARY
import asyncio  # need to import this for threading

logging.basicConfig(level=logging.INFO, format='[%(asctime)s]%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)

authorized_users = [135265595925987328, 137772624133488641]
lennys_id = 160962479013363712  # human lenny
# lennys_id = 135265595925987328  # squaar
squaars_id = 135265595925987328

##TODO: use embedded objects for say_channels and a help command
##TODO: better logging, esp. when responding to commands
    # log what user requested the command from the context
    # could we do this from authenticate()?
##TODO: better error handling - should report back in chat with stack trace? is there an on_error()?
##TODO: watch for lenny in voice channels and follow


##TODO: this could be done smarter
def authenticate(func):
    @wraps(func)
    def with_authentication(*args, **kwargs):
        ##TODO: throw this in a big ol' or
        if len(args) > 0 and type(args[1]) == discord.message.Message and int(args[1].author.id) in authorized_users:
            return func(*args, **kwargs)
        elif len(args) > 0 and type(args[1]) == werkzeug.local.LocalProxy and int(args[1]['user_id']) in authorized_users:
            return func(*args, **kwargs)
        else:
            raise AuthenticationError('Couldn\'t authenticate: %s; %s; %s' % (func.__name__, args, kwargs), func)
    return with_authentication


class LennyBot(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._realboi = True
        self._dadmode = True
        self._hi_im_lenny = True
        self._voice_client = None
        self._audio_queue = asyncio.Queue()
        self._audio_task = None

    def find_channel(self, server_name, channel_name):
        for server in self.guilds:
            if server.name == server_name:
                for channel in server.channels:
                    if channel.name == channel_name:
                        return channel
        raise ChannelNotFoundError(server_name, channel_name, 'Could not find %s/%s' % (server_name, channel_name))

    ##TODO: self.private_channels is only populated with private channels since logging in. find a way to update it in on_ready
    def find_private_channel(self, recipients):
        if type(recipients) == str:
            recipients = [recipients]
        for channel in self.private_channels:
            if recipients == [recipient.name for recipient in channel.recipients]:
                return channel
        raise ChannelNotFoundError('private', str(recipients), 'Could not find private channel with recipients: %s' % recipients)

    async def find_message(self, server_name, channel_name, message_id, history_limit=10000):
        message_id = int(message_id)
        channel = self.find_channel(server_name, channel_name)
        async for message in channel.history(limit=history_limit):
            if message.id == message_id:
                return message

    def channels_as_dict(self):
        channels = list(self.get_all_channels())
        d = dict((channel.guild.name, {}) for channel in channels)
        for channel in channels:
            d[channel.guild.name][channel.name] = channel
        return d

    def voice_connected(self):
        return self._voice_client and self._voice_client.is_connected()

    async def connect_voice(self, server, channel):
        channel = self.find_channel(server, channel)
        self._voice_client = await channel.connect()

    async def disconnect_voice(self):
        if self.voice_connected():
            await self._voice_client.disconnect()

    async def on_ready(self):
        logger.info('Lennybot logged in: %s, %s' % (self.user.name, self.user.id))
        try:
            # lenny_land = self.find_channel('Game Bois', 'Lenny land')
            # await lenny_land.connect()
            # await self.connect_voice('Game Bois', 'Lenny land')
            await self.connect_voice('Game Bois', 'Bot Testing')
        except RuntimeError as e:
            logger.exception(e)

    ##TODO: private messaging
    async def on_message(self, message):
        logger.info('%s/%s[%s]: %s' % (message.guild, message.channel, message.author, message.content.encode('utf-8')))

        if self._realboi and int(message.author.id) == lennys_id:
            message_content = message.content
            channel = message.channel
            tts = message.tts
            await message.delete()
            await channel.send(message_content, tts=tts)

        elif message.content[0] == '!':
            command = shlex.split(message.content)

            # !emojiate server channel message_id reactions
            if message.content.startswith('!emojiate'):
                await self.emojiate(message, command[1], command[2], command[3], command[4])

            # !emojify message
            elif message.content.startswith('!emojify'):
                await self.emojify(message, ' '.join(command[1:]))

            # !clear-emojiate server channel message_id
            elif message.content.startswith('!clear-emojiate'):
                await self.clear_emojiate(message, command[1], command[2], command[3])

            # !channels [server_filter]
            elif message.content.startswith('!channels'):
                await self.say_channels(message, message.channel, ' '.join(command[1:]))
            # elif message.content.startswith('!private-channels'):
            #     await self.print_private_channels(message)

            # !say server channel message
            elif message.content.startswith('!say'):
                await self.say(message, command[1], command[2], ' '.join(command[3:]))
            elif message.content.startswith('!tts'):
                await self.say(message, command[1], command[2], ' '.join(command[3:]), tts=True)

            # !realboi on/off
            elif message.content.startswith('!realboi'):
                self.realboi(message, command[1])

            # !dadmode on/off
            elif message.content.startswith('!dadmode'):
                self.dadmode(message, command[1])

            # !hi_im_lenny on/off
            elif message.content.startswith('!hi_im_lenny'):
                self.hi_im_lenny_mode(message, command[1])

            elif message.content.startswith('!playaudio'):
                await self.play_audio(message, command[1])

            elif message.content.startswith('!stopaudio'):
                await self.stop_audio(message)

            elif message.content.startswith('!vox'):
                await self.vox(message, command[1])

        else:
            if self._hi_im_lenny and 'lenny' in message.content.lower() and message.author != self.user:
                await self.hi_im_lenny(message)

            if self._dadmode:
                i = self._find_dadjokable(message)
                if i >= 0:
                    dadjoke = self._calc_dadjoke(message, i)
                    await message.channel.send(dadjoke, tts=message.tts)

    async def hi_im_lenny(self, context):
        await context.channel.send('Hello, I\'m the real Lenny!', tts=context.tts)

    async def clear_audio_queue(self):
        for i in range(self._audio_queue.qsize()):
            await self._audio_queue.get()

    async def stop_audio(self, context):
        if self._audio_task:
            self._audio_task.cancel()
            await asyncio.gather(self._audio_task, return_exceptions=True)
        await self.clear_audio_queue()
        if self.voice_connected() and self._voice_client.is_playing():
            self._voice_client.stop()

    async def play_resource(self, context, resource, after=None):
        logger.info(f'Play resource {resource}')
        if after is None:
            after = lambda e: f'Audio error: {e}'
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(resource.path))
        self._voice_client.play(source, after=after)
        # await context.channel.send(f'Playing {resource.name}.')

    async def play_resources(self, context, resources):
        async def worker():
            ready = True
            def after(e):
                if e:
                    logger.error(e)
                nonlocal ready
                ready = True
                self._audio_queue.task_done()

            while True:
                if not ready:
                    await asyncio.sleep(0)  # let the loop run
                    continue
                resource = await self._audio_queue.get()
                await self.play_resource(context, resource, after=after)
                ready = False

        await self.stop_audio(context)
        self._audio_task = asyncio.create_task(worker())
        for resource in resources:
            await self._audio_queue.put(resource)
        await self._audio_queue.join()

    @authenticate
    async def play_audio(self, context, resource_name):
        if not self.voice_connected():
            await context.channel.send('Not connected to voice channel.')
            return
        resource = RESOURCE_DICTIONARY.find_resource(resource_name)
        if not resource:
            await context.channel.send(f'Could\'t find audio {resource_name}.')
            return
        await self.play_resource(context, resource)

    @authenticate
    async def vox(self, context, sentence):
        words = [word.lower() for word in sentence.split()]
        resources = [RESOURCE_DICTIONARY.find_resource(word) for word in words]
        not_found = [word for i, word in enumerate(words) if not resources[i]]
        if not_found:
            await context.channel.send(f'Couldn\t find vox audio {not_found}')
            return
        await self.play_resources(context, resources)
        # for resource in resources:
        #     await self.play_resource(context, resource)


    @authenticate
    async def emojiate(self, context, server, channel, message_id, reactions):
        target = await self.find_message(server, channel, message_id)
        for char in reactions.lower():
            await target.add_reaction(a_to_emoji(char))

    @authenticate
    async def clear_emojiate(self, context, server, channel, message_id):
        target = await self.find_message(server, channel, message_id)
        await target.clear_reactions()

    @authenticate
    async def say(self, context, server, channel, message, tts=False):
        await self.find_channel(server, channel).send(message, tts=tts)

    @authenticate
    async def emojify(self, context, message):
        # TODO: put space between each character here so it doesn't combine emojis
        logger.info(message)
        await context.channel.send(str_to_emoji(message))

    @authenticate
    async def say_channels(self, context, channel, server_filter=None):
        # TODO: allow for regex server_filter?
        if server_filter:
            await context.channel.send(list(self.channels_as_dict()[server_filter].keys()))
        else:
            await context.channel.send(str(dict((server, list(channels.keys())) for server, channels in self.channels_as_dict().items())))

    # self.private_channels is []. Not sure what this is for anymore
    # @authenticate
    # async def print_private_channels(self, context):
    #     await list(self.private_channels)[0].send('lennybot online')
    #     logger.info('private channels %s' % len(self.private_channels))
    #     await context.channel.send([list(map(lambda x: x.name, channel.recipients)) for channel in self.private_channels])
    #     # await self.send_message(message.channel, [channel.id for channel in self.private_channels])

    @authenticate
    async def message_squaar(self, context, message):
        for member in self.get_all_members():
            if int(member.id) == squaars_id:
                await member.send(message)
                return

    @authenticate
    def realboi(self, context, state):
        if (type(state) == str and state.lower() == 'on') or state is True:
            self._realboi = True
        elif (type(state) == str and state.lower() == 'off') or state is False:
            self._realboi = False
        logger.info('Realboi mode: %s' % self._realboi)

    @authenticate
    def dadmode(self, context, state):
        if (type(state) == str and state.lower() == 'on') or state is True:
            self._dadmode = True
        elif (type(state) == str and state.lower() == 'off') or state is False:
            self._dadmode = False
        else:
            logger.warning('Unrecognized state for dadmode: %s' % state)
        logger.info('Dad mode: %s' % self._dadmode)

    @authenticate
    def hi_im_lenny_mode(self, context, state):
        if (type(state) == str and state.lower() == 'on') or state is True:
            self._hi_im_lenny = True
        elif (type(state) == str and state.lower() == 'off') or state is False:
            self._hi_im_lenny = False
        else:
            logger.warning('Unrecognized state for hi_im_lenny_mode: %s' % state)
        logger.info('hi_im_lenny mode: %s' % self._hi_im_lenny)

    # TODO: could use regex?
    # looks for triggers to be either at the beginning of the message or somewhere in the middle with a space to
    # prevent triggering off the end of other words
    def _find_dadjokable(self, message):
        dadjoke_triggers = ['i\'m ', 'i am ' 'im ']
        for trigger in dadjoke_triggers:
            if message.content.find(trigger) == 0:
                return len(trigger)
            elif ' ' + trigger in message.content:
                return message.content.find(' ' + trigger) + len(trigger) + 1  # for the space
        return -1

    ##TODO: implement dadjokes
    # TODO: find a way to determine where to end the joke. punctuation?
    # i: beginning of the dadjokable clause
    def _calc_dadjoke(self, message, i=0):
        return 'Hi %s! I\'m the real Lenny.' % message.content[i:]

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
