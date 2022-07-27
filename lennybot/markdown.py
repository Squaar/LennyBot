
'''
https://support.discord.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline-

Italics	*italics* or _italics_
Underline italics	__*underline italics*__
Bold	**bold**
Underline bold	__**underline bold**__
Bold Italics	***bold italics***
underline bold italics	__***underline bold italics***__
Underline	__underline__
Strikethrough	 ~~Strikethrough~~
'''

def codeblock(s):
    return f"'''{s}'''"

def quote(s):
    return f'> {s}'

def blockQuote(s):
    return f'>>> {s}'

def bold(s):
    return f'**{s}**'

def italic(s):
    return f'*{s}*'
