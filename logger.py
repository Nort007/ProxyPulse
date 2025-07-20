import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset color
    }

    def format(self, record: logging.LogRecord):
        log_message = super().format(record)
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset_color = self.COLORS["RESET"]
        colored_message = f"{level_color}{log_message}{reset_color}"

        return colored_message


def setup_colored_logger(
    name: str = "Logger", level: int = logging.CRITICAL, debug: bool = False
):
    """
    Set up a colored logger with custom formatting

    Args:
        name (str): Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured logger instance
    """

    logger = logging.getLogger(name)
    if debug:
        level = logging.DEBUG

    logger.setLevel(level)

    if logger.handlers:
        logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = ColoredFormatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
