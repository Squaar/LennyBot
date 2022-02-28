import argparse
import logging
import shlex
import discord

logging.basicConfig(level=logging.INFO, format='[%(asctime)s]%(levelname)s-%(name)s-%(message)s')
log = logging.getLogger(__name__)

class LennyMessageParser(argparse.ArgumentParser):
    def __init__(self, *args, funcname=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.funcname = funcname
        self.exit_on_error = False

    def parse_message(self, message):
        if isinstance(message, discord.Message):
            args = shlex.split(message.content)
        elif isinstance(message, str):
            args = shlex.split(message)
        else:
            raise TypeError(f'message is {type(message)}. Expected discord.Message or str')
        ret = self.parse_args(args)
        ret.message = message
        return ret

    def error(self, message):
        raise argparse.ArgumentError(None, message)


    # def parse_args(self, *args, **kwargs):
    #     try:
    #         return super().parse_args(*args, **kwargs)
    #     except argparse.ArgumentError as e:
    #         return e


class MessageParseMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_parser = LennyMessageParser(prog='')
        subparsers = self._message_parser.add_subparsers()

        vox_parser = subparsers.add_parser('!vox', funcname='vox')
        vox_parser.add_argument('--channel', '-c', nargs='?', default=None, const='__SENDER__',
                                help='Automatically switch to the given Server/Channel or the sender\'s channel and back.')
        vox_parser.add_argument('words', nargs='+')

        for name, parser in subparsers.choices.items():
            if parser.funcname:
                if hasattr(self, parser.funcname):
                    parser.set_defaults(func=getattr(self, parser.funcname))
                else:
                    log.warning(f'Could not find func for parser {parser.prog}: {parser.funcname}')

    async def on_message(self, message):
        command = self._message_parser.parse_message(message)
        if hasattr(command, 'func'):
            await command.func(command)



if __name__ == '__main__':
    # from . import lennybot
    # lenny = lennybot.LennyBot()
    #
    # none = lenny._command_parser.parse_args([])
    # foo = lenny._command_parser.parse_args(['foo'])
    # vox = lenny._command_parser.parse_args(['vox', ''])

    parser = MessageParseMixin()
    try:
        none = parser._message_parser.parse_args([])
        # foo = parser._message_parser.parse_args(['foo'])
        vox = parser._message_parser.parse_args(['!vox', '-c'])
    except Exception as e:
        log.exception(e)

    print()