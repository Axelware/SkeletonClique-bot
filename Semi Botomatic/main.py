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

    loggers = {
        'discord':   None,
        'bot':       None,
        'cogs':      None,
        'utilities': None,
        'slate':     None,
        'aiohttp':   None
    }

    for log_name in loggers:

        log = logging.getLogger(log_name)
        loggers[log_name] = log

        handler = logging.handlers.RotatingFileHandler(filename=f'logs/{log_name}.log', mode='w', backupCount=5, encoding='utf-8', maxBytes=2**22)
        log.addHandler(handler)
        if os.path.isfile(f'logs/{log_name}.log'):
            handler.doRollover()

        formatter = logging.Formatter(fmt=f'%(asctime)s | %(levelname)s: %(name)s: %(message)s', datefmt='%d/%m/%Y at %I:%M:%S %p')
        handler.setFormatter(formatter)

    loggers['discord'].setLevel(logging.INFO)
    loggers['bot'].setLevel(logging.DEBUG)
    loggers['cogs'].setLevel(logging.DEBUG)
    loggers['utilities'].setLevel(logging.DEBUG)
    loggers['slate'].setLevel(logging.DEBUG)
    loggers['aiohttp'].setLevel(logging.DEBUG)

    try:
        yield
    finally:
        [log.handlers[0].close() for log in loggers.values()]


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
