import asyncio
import contextlib
import logging
import logging.handlers
import os
import sys

import setproctitle

import config
from bot import SemiBotomatic


@contextlib.contextmanager
def logger():

    logs = {'discord': None, 'bot': None, 'cogs': None, 'utilities': None, 'slate': None}

    for log_name in logs:

        log = logging.getLogger(log_name)
        handler = logging.handlers.RotatingFileHandler(filename=f'logs/{log_name}.log', mode='w', backupCount=5, encoding='utf-8', maxBytes=2**22)
        handler.setFormatter(logging.Formatter(f'%(asctime)s | %(levelname)s: %(name)s: %(message)s', datefmt='%d/%m/%Y at %I:%M:%S %p'))
        if os.path.isfile(f'logs/{log_name}.log'):
            handler.doRollover()
        log.addHandler(handler)

        logs[log_name] = log

    logs['discord'].setLevel(logging.INFO)
    logs['bot'].setLevel(logging.DEBUG)
    logs['cogs'].setLevel(logging.DEBUG)
    logs['utilities'].setLevel(logging.DEBUG)
    logs['slate'].setLevel(logging.DEBUG)

    try:
        yield
    finally:
        [log.handlers[0].close() for log in logs.values()]


if __name__ == '__main__':

    os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
    os.environ['JISHAKU_HIDE'] = 'True'

    setproctitle.setproctitle('SemiBotomatic')

    try:
        import uvloop
        if sys.platform != 'win32':
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        uvloop = None
    else:
        del uvloop

    with logger():
        SemiBotomatic().run(config.TOKEN)
