


class ReaderError(Exception):
    """reader error

    Args:
        Exception: exception
    """

class KeyNotMatchPatternError(ReaderError):
    """key not match pattern error

    Args:
        ReaderError: reader error
    """

class InvalidFileError(ReaderError):
    """invalid file error

    Args:
        ReaderError: reader error
    """
