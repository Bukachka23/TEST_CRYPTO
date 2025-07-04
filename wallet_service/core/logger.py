import logging
import sys
from pathlib import Path


class Logger:
    def __init__(self, name="pipeline_logger", level=logging.INFO, log_dir="logs"):
        """Initializes and configures a standard Python logger."""
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        # Create logs directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        # Error log file path
        error_log_file = log_path / "error.log"

        # Prevent adding multiple handlers if the logger already exists
        if not self._logger.handlers:
            # Console handler (stdout)
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

            # File handler for errors only
            error_file_handler = logging.FileHandler(error_log_file)
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(formatter)
            self._logger.addHandler(error_file_handler)

    def info(self, msg, *args, **kwargs) -> None:
        """Log an info message."""
        self._logger.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs) -> None:
        """Log an error message."""
        self._logger.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs) -> None:
        """Log a debug message."""
        self._logger.debug(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs) -> None:
        """Log a warning message."""
        self._logger.warning(msg, *args, **kwargs)

    # Optional: Add other logging levels as needed (debug, critical, etc.)
    def exception(self, msg, *args, **kwargs) -> None:
        """Log an exception message."""
        self._logger.exception(msg, *args, **kwargs)
