import logging


class DebugInfoLogLevelFilter(logging.Filter):
    def filter(self, record):
        # Only allow DEBUG + INFO logs
        return record.levelno in [logging.DEBUG, logging.INFO]
