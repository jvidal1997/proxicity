import logging
from logging.handlers import QueueHandler, QueueListener
from queue import SimpleQueue
from pathlib import Path
import threading
import atexit


class AsyncFileLogger:
    """
    Asynchronous file logger that writes to disk immediately via a queue.
    Safe for loops with tqdm or abrupt termination.
    """

    _listeners = {}  # class-level cache to prevent duplicate listeners

    def __init__(self, module_name: str = None, base_dir: str = "out/logs"):
        # Determine module name if not provided
        import inspect
        if module_name is None:
            frame = inspect.stack()[1]
            module_name = Path(frame.filename).stem
        self.module_name = module_name

        # Set up log directory
        self.base_dir = Path(base_dir) / self.module_name
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

        # Ensure listener stops and queue flushes on exit
        atexit.register(self._stop_listener)

    def _stop_listener(self):
        """Stop listener and flush any remaining logs."""
        listener = AsyncFileLogger._listeners.get(self.module_name)
        if listener:
            listener.stop()

    # ------------------------------
    # Logging methods
    # ------------------------------
    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)
