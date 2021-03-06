class SharePointError(Exception):
    def __init__(self, msg, details=None):
        if details:
            super().__init__(f"{msg} : {details}")
        else:
            super().__init__(msg)


class SharePointRequestError(SharePointError):
    pass

class SharePointListItemError(SharePointError):
    pass