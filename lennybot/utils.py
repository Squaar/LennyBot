import os.path
import datetime
import logging
import asyncio
import functools
import requests

log = logging.getLogger(__name__)

def path_is_within(path, dir):
    path = os.path.abspath(path)
    dir = os.path.abspath(dir)
    return os.path.commonpath((path, dir)) == dir


class Timer:
    def __init__(self, msg, logfn=print):
        self.msg = msg
        self.logfn=logfn

    def __enter__(self):
        self.start = datetime.datetime.now()
        return self

    def __exit__(self, *exc):
        end = datetime.datetime.now()
        delta = end - self.start
        if self.logfn and callable(self.logfn):
            self.logfn(f'{self.msg}: {delta}')
        if exc and not all([val is None for val in exc]):
            log.error(str(exc))
        log.debug(str(exc))

# async def asyncGet(*args, **kwargs):
#     loop = asyncio.get_running_loop()
#     fn = functools.partial(requests.get, *args, **kwargs)
#     resp = await loop.run_in_executor(None, fn)

async def runInExecutor(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    fn = functools.partial(fn, *args, **kwargs)
    ret = await loop.run_in_executor(None, fn)
    return ret


async def getIP():
    resp = await runInExecutor(requests.get, 'https://api.ipify.org?format=json')
    checkResponse(resp)
    return resp.json()['ip']


def checkResponse(resp):
    log.debug(str(resp))
    if not 200 <= resp.status_code < 300:
        raise RuntimeError(resp.text)