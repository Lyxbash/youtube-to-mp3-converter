class ConversionAppError(Exception):
    """Base class for errors that should be turned into a clean JSON response."""


class InvalidUrlError(ConversionAppError):
    pass


class VideoUnavailableError(ConversionAppError):
    pass


class DownloadFailedError(ConversionAppError):
    pass


class ConversionError(ConversionAppError):
    pass
