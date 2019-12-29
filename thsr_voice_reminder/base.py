import logging
import pathlib


class Base:
    def __init__(self, child_class, args):
        child_class_name = type(child_class).__name__
        self._logger = Base.create_logger(
            child_class_name, verbose=args.verbose)
        self._args = args
        self._settings = None

    def update_settings(self, settings):
        self._settings = settings

    @staticmethod
    def create_logger(name, verbose=False):
        # Set the logging level
        if verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO

        # Create a logger
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Set the logging path
        path = 'logs/{}.log'.format(name)

        # Make sure the logging directory exists
        path_obj = pathlib.Path(path)
        parent_obj = path_obj.parent
        parent_obj.mkdir(parents=True, exist_ok=True)

        # Create a file handler
        fh = logging.FileHandler(path, mode='w', encoding='utf-8')
        fh.setLevel(level)

        # Create a console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Create a formatter and add it to the handlers
        formatter = logging.Formatter(
            '%(asctime)-15s %(name)s %(levelname)-7s: %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        # Return the logger
        return logger
