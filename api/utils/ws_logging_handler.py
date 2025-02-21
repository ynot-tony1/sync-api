import asyncio
import logging
from connection_manager import broadcast

class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        asyncio.create_task(broadcast(msg))