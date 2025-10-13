import logging
from datetime import datetime

# List of valid logging levels
VALID_LOGGING_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# Function to configure and return a logger
def configure_logger(file_name, enabled=True, logging_level='INFO'):
    """
    Configure a logger with the specified file name, logging level, and enabled state.

    Parameters:
    - file_name (str): The name of the logger.
    - enabled (bool): Whether the logger is enabled or disabled. Default is True (enabled).
    - logging_level (str): The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default is 'INFO'.

    Returns:
    - logging.Logger: The configured logger object.
    """
    # Ensure the provided logging level is valid, otherwise default to "INFO"
    if logging_level not in VALID_LOGGING_LEVELS:
        logging_level = "INFO"

    # Configure the logging settings
    logging.basicConfig(
        filename=f"./logs/{timestamp}.log",  # Specify the log file path
        filemode='+a',            # Append mode to avoid overwriting logs
        level=logging_level,      # Set the logging level
        format="%(asctime)s.%(msecs)03d %(levelname)s {%(threadName)s} [%(module)s] "
               "(%(funcName)s) {%(pathname)s:%(lineno)d} %(message)s",  # Log message format
        datefmt="%Y-%m-%d %H:%M:%S",  # Date format for log entries
    )

    # Create a logger with the specified name
    logger = logging.getLogger(file_name)

    # Disable the logger if 'enabled' is False
    if not enabled:
        logger.disabled = True

    return logger
