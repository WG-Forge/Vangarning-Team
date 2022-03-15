"""
Contains singleton meta class.

"""


class SingletonMeta(type):
    """
    Meta class for creating singleton classes.

    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
