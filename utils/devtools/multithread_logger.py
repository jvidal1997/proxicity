"""
Asynchronous, thread-safe file logger.

Provides the `AsyncFileLogger` class, which logs messages to disk via a queue
to avoid blocking execution. Supports info, error, warning, and debug levels.
Designed to safely work in loops with progress bars (e.g., tqdm) or
applications that may terminate abruptly. Automatically manages log file
rotation and flushes remaining messages on exit.

NOTE: The class implements a runtime-configurable instantiation strategy: it behaves as a global singleton when
module-based logging is disabled and as a multiton/factory when module-based logging is enabled.
"""
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import SimpleQueue
from pathlib import Path
import threading
import atexit
from Settings import ENV as PROPERTY


class AsyncFileLogger:
    """
    Asynchronous file logger that writes to disk immediately via a queue.
    Safe for loops with tqdm or abrupt termination.
    """
    _module_logging = PROPERTY["MODULE_BASED_LOGGING"]  # class-level flag to toggle single log file per module

    _global_instance = None # Global shared singleton instance (used when module-based logging is disabled)

    _listeners = {}  # class-level cache to prevent duplicate listeners

    def __new__(cls, module_name: str = None, base_dir: str = "out/logs"):
        """
        Ensure that when module-based logging is disabled, the class behaves like a singleton.
        Otherwise, the class behaves like a factory
        """
        if not cls._module_logging:
            # Return the already created instance
            if cls._global_instance is not None:
                return cls._global_instance

            # Create and store the singleton instance
            instance = super().__new__(cls)
            cls._global_instance = instance
            return instance

        # Otherwise: Factory behavior (one logger per module)
        return super().__new__(cls)

    def __init__(self, module_name: str = None, base_dir: str = "out/logs"):
        """
        Initializes an asynchronous file logger for the given module. Sets up a log directory, creates a new log file
        with an incremented index, and starts a thread-safe listener to write logs to disk.

        When module-based logging is disabled, the initialization runs only once due to the singleton pattern.

        :param module_name: Name of the module to log to.
        :param base_dir: Base directory to write log files into.
        """

        # Prevent re-initialization of the singleton instance
        if not self._module_logging and hasattr(self, "_initialized"):
            return

        # Determine module name if not provided
        import inspect
        if module_name is None:
            frame = inspect.stack()[1]
            module_name = Path(frame.filename).stem

        # If module logging is OFF, override module_name with a fixed one (project_name)
        if not self._module_logging:
            module_name = "proxicity"

        self.module_name = module_name

        # Set up log directory
        self.base_dir = Path(base_dir) / self.module_name if self.module_name else Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Determine log file name with index
        existing_files = list(self.base_dir.glob(f"{self.module_name}_log_*.log"))
        if existing_files:
            indices = [int(f.stem.split("_")[-1]) for f in existing_files
                       if f.stem.split("_")[-1].isdigit()]
            next_index = max(indices, default=0) + 1
        else:
            next_index = 1
        self.log_file = self.base_dir / f"{self.module_name}_log_{next_index}.log"

        # Set up logger
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # prevent double logging

        # Thread-safe queue
        self.queue = SimpleQueue()

        # QueueHandler sends logs to the queue
        queue_handler = QueueHandler(self.queue)
        self.logger.addHandler(queue_handler)

        # File handler writes logs to disk
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

        # QueueListener reads from the queue and writes to file
        self.listener = QueueListener(self.queue, file_handler)
        self.listener.start()

        # Keep track to avoid multiple listeners for same module
        AsyncFileLogger._listeners[self.module_name] = self.listener

        # Ensure this only runs once for global singleton
        self._initialized = True

        # Ensure listener stops and queue flushes on exit
        atexit.register(self._stop_listener)

    def _stop_listener(self):
        """
        Stops the queue listener and flushes any remaining log messages to the file.
        Called automatically on program exit.
        """
        listener = AsyncFileLogger._listeners.get(self.module_name)
        if listener:
            listener.stop()

    # Logging methods
    def info(self, msg: str):
        """
        Logs an info-level message asynchronously to the log file.
        :param msg: Info-level message.
        """
        self.logger.info(msg)

    def error(self, msg: str):
        """
        Logs an error-level message asynchronously to the log file.
        :param msg: Error-level message.
        """
        self.logger.error(msg)

    def warning(self, msg: str):
        """
        Logs a warning-level message asynchronously to the log file.
        :param msg: Warning-level message.
        """
        self.logger.warning(msg)

    def debug(self, msg: str):
        """
        Logs a debug-level message asynchronously to the log file.
        :param msg: Debug-level message.
        """
        self.logger.debug(msg)
