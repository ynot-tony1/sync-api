"""
A custom logging handler that sends log messages over WebSocket.
"""

import asyncio
import logging
from api.connection_manager import broadcast


class WebSocketLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emits a log record over a WebSocket.
        
        Args:
            record (logging.LogRecord): The log record to send.
        """
        msg: str = self.format(record)
        asyncio.create_task(broadcast(msg))
