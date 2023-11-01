class MatchingError(Exception):
    """Base class for all custom exceptions for the matching algorithm"""
    pass

class DataParsingError(MatchingError):
    def __init__(self, failed: str, *args: object) -> None:
        super().__init__(*args)
        self.failed = failed