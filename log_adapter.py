import logging

class CorrelationIdAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})

    def process(self, msg, kwargs):
        correlation_id = kwargs.pop('correlation_id', 'N/A')
        self.extra['correlation_id'] = correlation_id
        return f"{msg}", {'extra': {'correlation_id': correlation_id}}