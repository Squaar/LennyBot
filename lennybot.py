import discord
import asyncio
import logging
import shlex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

discord_client = discord.Client()
channels = {}
authorized_users = [135265595925987328, 137772624133488641]


@discord_client.event
async def on_ready():
    logger.info('Logged in: %s,%s' % (discord_client.user.name, discord_client.user.id))
    for channel in discord_client.get_all_channels():
        channels['%s/%s' % (channel.server.name, channel.name)] = channel
    logger.info(list(channels.keys()))  # TODO: WHY WONT THIS PRINT?
    logger.info([emoji.name for emoji in discord_client.get_all_emojis()])

    try:
        await discord_client.join_voice_channel(channels['Game Bois/Lenny land'])
    except RuntimeError as e:
        logger.warn(e)


@discord_client.event
async def on_message(message):
    logger.info('%s/%s[%s]: %s' % (message.server, message.channel, message.author, message.content.encode('utf-8')))
    if int(message.author.id) in authorized_users:
        # await discord_client.send_message(message.channel, emoji_alphabet['a'])
        if message.content.startswith('!emojiate'):
            await emojiate(message)
        elif message.content.startswith('!emojify'):
            await emojify(message)
        elif message.content.startswith('!clear-emojiate'):
            await clear_emojiate(message)
        elif message.content.startswith('!channels'):
            await print_channels(message)
        elif message.content.startswith('!say'):
            await say(message)
        elif message.content.startswith('!tts'):
            await say(message, tts=True)


# !emojiate server/channel message_id reactions
async def emojiate(message):
    command = shlex.split(message.content)
    target = await discord_client.get_message(channels[command[1]], command[2])
    for char in command[3].lower():
        await discord_client.add_reaction(target, a_to_emoji(char))


# !clear-emojiate server/channel message_id
async def clear_emojiate(message):
    command = shlex.split(message.content)
    target = await discord_client.get_message(channels[command[1]], command[2])
    await discord_client.clear_reactions(target)


# !say server/channel message
async def say(message, tts=False):
    command = shlex.split(message.content)
    command[2] = ' '.join(command[2:])
    await discord_client.send_message(channels[command[1]], command[2], tts=tts)


# !emojify message
async def emojify(message):
    command = shlex.split(message.content)
    command[1] = ' '.join(command[1:])
    logger.info(command[1])
    await discord_client.send_message(message.channel, str_to_emoji(command[1]))


# !channels [server]
async def print_channels(message):
    command = shlex.split(message.content)
    if len(command) > 1:
        command[1] = ' '.join(command[1:])
        filtered = filter(lambda x: x.lower().startswith(command[1].lower()), list(channels.keys()))
        await discord_client.send_message(message.channel, [channel.split('/')[1] for channel in filtered])
    else:
        await discord_client.send_message(message.channel, list(channels.keys()))


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


if __name__ == '__main__':
    import os
    OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']
    discord_client.run(OAUTH2_BOT_TOKEN)
