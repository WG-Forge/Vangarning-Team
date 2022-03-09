"""
Module's custom exceptions.

"""


class InvalidContentTypeError(Exception):
    """
    Called if content type received from the server has no class
    corresponding to it.
    """


class OutOfBoundsError(Exception):
    """
    Called when coordinates are out of map's bounds.
    """
