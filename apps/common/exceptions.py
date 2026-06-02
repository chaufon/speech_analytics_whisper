class BaseAnalyticsException(Exception):
    msg = ""

    def __init__(self, msg=None):
        super().__init__(msg or self.msg)
