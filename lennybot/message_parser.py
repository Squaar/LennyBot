import argparse
import logging
import shlex
import discord
import io
import asyncio

logging.basicConfig(level=logging.INFO, format='[%(asctime)s]%(levelname)s-%(name)s-%(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class LennyMessageParser(argparse.ArgumentParser):
    def __init__(self, *args, funcname=None, func=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.funcname = funcname
        self.func = func
        self.exit_on_error = False

    def parse_message(self, message):
        if isinstance(message, discord.Message):
            args = shlex.split(message.content)
        elif isinstance(message, str):
            args = shlex.split(message)
        else:
            raise TypeError(f'message is {type(message)}. Expected discord.Message or str')
        log.debug(f'parse_args: {args}')
        ret = self.parse_args(args)
        ret.args = args
        ret.message = message
        ret.help = any([arg in args for arg in ('-h', '--help')])
        log.debug(f'arg namespace: {ret}')
        return ret

    def error(self, message):
        raise argparse.ArgumentError(None, message)

    def exit(self, status=0, message=None):
        log.debug(f'Message parse exit status {status}: {message}')


class MessageParseMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_parser = LennyMessageParser(prog='')
        self._subparsers = self._message_parser.add_subparsers()

        help_parser = self._subparsers.add_parser('!help', funcname='help')

        vox_parser = self._subparsers.add_parser('!vox', funcname='vox')
        vox_parser.add_argument('--channel', '-c', nargs='?', default=None, const='__SENDER__',
                                help='Automatically switch to the given Server/Channel or the sender\'s channel and back.')
        vox_parser.add_argument('words', nargs='+')

        fifteenai_parser = self._subparsers.add_parser('!fifteenai', funcname='fifteenai')
        fifteenai_parser.add_argument('--channel', '-c', nargs='?', default=None, const='__SENDER__',
                                help='Automatically switch to the given Server/Channel or the sender\'s channel and back.')
        fifteenai_parser.add_argument('--list-characters', action='store_true',
                                      help='List characters available and exit.')
        fifteenai_parser.add_argument('--character', '-a', help='The character\'s voice to use.')
        fifteenai_parser.add_argument('--emotion', '-e', default='Contextual', help='The emotion to use.')
        fifteenai_parser.add_argument('text', nargs='*', help='What to say')

        for name, parser in self._subparsers.choices.items():
            if parser.funcname:
                if hasattr(self, parser.funcname):
                    parser.set_defaults(func=getattr(self, parser.funcname))
                else:
                    log.warning(f'Could not find func for parser {parser.prog}: {parser.funcname}')

    async def on_message(self, message):
        command = self._message_parser.parse_message(message)
        if hasattr(command, 'help') and command.help:
            await self.helpForSubprocessor(command, self._subprocessorForCommand(command))
        elif hasattr(command, 'func'):
            await command.func(command)

    async def help(self, command):
        return await self.helpForSubprocessor(command, self._message_parser)

    async def helpForSubprocessor(self, command, subprocessor):
        f = io.StringIO()
        f.write('\n')
        subprocessor.print_help(file=f)
        f.seek(0)
        await command.message.channel.send(f.read())

    def _subprocessorForCommand(self, command):
        return self._subparsers._name_parser_map.get(command.args[0])

class MockMessage(discord.Message):
    def __init__(self, content):
        self.content = content
        self.channel = MockChannel()

    def __repr__(self):
        return f'<MockMessage content=\'{self.content}\'>'

    def __str__(self):
        return self.__repr__()

class MockChannel(discord.TextChannel):
    def __init__(self):
        pass

    def __repr__(self):
        return f'<MockChannel>'

    def __str__(self):
        return self.__repr__()

    async def send(self, content=None):
        print(content)

class InteractiveMessageParser(MessageParseMixin):
    def __init__(self):
        super().__init__()
        self._subparsers.add_parser('!exit', funcname='exit', func=self.exit)

    async def run(self):
        self._exit = False
        while not self._exit:
            await self.on_message(MockMessage(input()))

    def exit(self):
        self._exit = True

if __name__ == '__main__':
    # from . import lennybot
    # lenny = lennybot.LennyBot()
    #
    # none = lenny._command_parser.parse_args([])
    # foo = lenny._command_parser.parse_args(['foo'])
    # vox = lenny._command_parser.parse_args(['vox', ''])

    # parser = MessageParseMixin()
    # try:
    #     # none = parser._message_parser.parse_args([])
    #     # foo = parser._message_parser.parse_args(['foo'])
    #     # vox = parser._message_parser.parse_args(['!vox', '-c'])
    #     help = parser._message_parser.parse_message('--help')
    # except Exception as e:
    #     log.exception(e)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(InteractiveMessageParser().run())
    print()