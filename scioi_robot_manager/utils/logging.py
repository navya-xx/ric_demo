import datetime
import inspect
import logging
import os

from utils import colors


def disableAllOtherLoggers(module_name=None):
    for log_name, log_obj in logging.Logger.manager.loggerDict.items():
        if log_name != module_name:
            log_obj.disabled = True

def disableLoggers(loggers: list):
    for log_name, log_obj in logging.Logger.manager.loggerDict.items():
        if log_name in loggers:
            log_obj.disabled = True

def getLoggerByName(logger_name: str):
    for log_name, log_obj in logging.Logger.manager.loggerDict.items():
        if log_name == logger_name:
            return log_obj
    return None

def setLoggerLevel(logger, level=logging.DEBUG):
    if isinstance(logger, str):
        l = logging.getLogger(logger)
        l.setLevel(level)
    elif isinstance(logger, list) and all(isinstance(l, tuple) for l in logger):
        for logger_tuple in logger:
            l = getLoggerByName(logger_tuple[0])
            if l is not None:
                l.setLevel(logger_tuple[1])
            pass


def rgb_to_256color_escape(text_color_rgb, bg_color_rgb=None, bold=False):
    """
    Convert RGB color values to ANSI escape code for 256-color mode.

    Parameters:
    - text_color_rgb (tuple or list): RGB values (0-255) for text color.
    - bg_color_rgb (tuple or list, optional): RGB values (0-255) for background color.
    - bold (bool, optional): Whether text should be bold (default: False).

    Returns:
    - str: ANSI escape code for the specified colors and style in 256-color mode.
    """
    if len(text_color_rgb) != 3:
        raise ValueError("Text color RGB tuple must contain exactly three values (R, G, B)")
    if not all(0 <= c <= 255 for c in text_color_rgb):
        raise ValueError("Text color RGB values must be between 0 and 255")

    escape_code = "\x1b["

    # Bold attribute
    if bold:
        escape_code += "1;"

    # Text color
    text_color_index = 16 + (36 * round(text_color_rgb[0] / 255 * 5)) + (
                6 * round(text_color_rgb[1] / 255 * 5)) + round(text_color_rgb[2] / 255 * 5)
    escape_code += f"38;5;{text_color_index}"

    # Background color
    if bg_color_rgb is not None:
        if len(bg_color_rgb) != 3:
            raise ValueError("Background color RGB tuple must contain exactly three values (R, G, B)")
        if not all(0 <= c <= 255 for c in bg_color_rgb):
            raise ValueError("Background color RGB values must be between 0 and 255")

        bg_color_index = 16 + (36 * round(bg_color_rgb[0] / 255 * 5)) + (6 * round(bg_color_rgb[1] / 255 * 5)) + round(
            bg_color_rgb[2] / 255 * 5)
        escape_code += f";48;5;{bg_color_index}"

    escape_code += "m"
    return escape_code


reset = "\x1b[0m"
grey = "\x1b[38;20m"
yellow = "\x1b[33;20m"
red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
blue = "\x1b[34;20m"
green = "\x1b[32;20m"
pink = "\x1b[35;20m"
light_pink_256 = "\x1b[38;5;218m"

blue_text_yellow_bg = "\x1b[34;43m"
bold_red_text_white_bg = "\x1b[31;1;47m"
white_text_red_bg = "\x1b[37;41m"
black_text_red_bg = "\x1b[30;41m"
black_text_white_bg = "\x1b[30;47m"


class CustomFormatter(logging.Formatter):
    _filename: str

    def __init__(self, info_color = grey):
        logging.Formatter.__init__(self)

        # self.str_format = f"%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
        # self.str_format = "%(asctime)s - %(name)s (%(filename)s) - %(levelname)-10s %(message)s"
        self.str_format = "%(asctime)s.%(msecs)03d %(levelname)-10s  %(name)s %(filename)-10s  %(message)s"
        self._filename = None

        self.FORMATS = {
            logging.DEBUG: grey + self.str_format + reset,
            logging.INFO: info_color + self.str_format + reset,
            logging.WARNING: yellow + self.str_format + reset,
            logging.ERROR: red + self.str_format + reset,
            logging.CRITICAL: bold_red + self.str_format + reset
        }

    def setFileName(self, filename):
        self._filename = filename

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt,"%H:%M:%S")
        record.filename = self._filename
        record.levelname = '[%s]' % record.levelname
        record.filename = '(%s)' % record.filename
        record.name = '[%s]' % record.name
        record.filename = '%s:' % record.filename

        return formatter.format(record)


class Logger:
    _logger: logging.Logger

    def __init__(self, name, info_color=colors.LIGHT_GREY, background=None):
        self._logger = logging.getLogger(name)
        self._logger.setLevel('INFO')

        if isinstance(info_color, tuple):
            info_color = rgb_to_256color_escape(info_color,background)
        elif isinstance(info_color, list):
            info_color = rgb_to_256color_escape(info_color,background)

        self.formatter = CustomFormatter(info_color=info_color)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(self.formatter)
        self._logger.addHandler(stream_handler)

    def getFileName(self):
        frame = inspect.currentframe().f_back.f_back
        filename = frame.f_globals['__file__']
        filename = os.path.basename(filename)
        lineno = frame.f_lineno
        return filename

    def debug(self, msg, *args, **kwargs):
        self.formatter.setFileName(self.getFileName())
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.formatter.setFileName(self.getFileName())
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.formatter.setFileName(self.getFileName())
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.formatter.setFileName(self.getFileName())
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.formatter.setFileName(self.getFileName())
        self._logger.critical(msg, *args, **kwargs)

    def setLevel(self, level):
        self._logger.setLevel(level)


def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
#
# ch.setFormatter(CustomFormatter())