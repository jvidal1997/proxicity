import re
from pathlib import Path
from dotenv import dotenv_values


class Settings:
    """
    Global settings loader that:
    - Finds the project root dynamically
    - Loads .env.dev if present, else .env
    - Parses values into Python types
    - Makes all variables globally accessible (Settings.KEY)
    - Runs exactly once
    """

    _env = {}          # Stores parsed variables
    ROOT = None        # Absolute project root path
    ENV_FILE = None    # The file actually loaded

    # ------------------------------------------------------------
    # Project Root Detection
    # ------------------------------------------------------------
    @staticmethod
    def _find_project_root() -> Path:
        """
        Dynamically detect the root folder of the project by looking for
        either a .git folder or a .env file. Falls back to cwd.
        """
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / ".git").exists() or (parent / ".env").exists():
                return parent
        return Path.cwd()

    # ------------------------------------------------------------
    # Value Parser
    # ------------------------------------------------------------
    @staticmethod
    def parse_value(value: str):
        """Convert strings to Python types automatically."""
        value = value.strip()

        # 1. Parse comma-separated arrays (before type-coercing)
        if "," in value:
            return [v.strip() for v in value.split(",")]

        # 2. Booleans
        lower = value.lower()
        if lower == "true":
            return True
        if lower == "false":
            return False

        # 3. Integers
        if re.fullmatch(r"-?\d+", value):
            return int(value)

        # 4. Floats
        try:
            return float(value)
        except ValueError:
            pass

        # 5. Email detection
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if re.match(email_regex, value):
            return value

        # 6. Paths — convert to absolute paths if path-like
        # Detect forward/backslashes OR drive letters
        if "/" in value or "\\" in value or re.match(r"^[A-Za-z]:\\", value):
            return str((Settings.ROOT / value).resolve())

        # Otherwise return raw string
        return value

    # ------------------------------------------------------------
    # Loading Environment Variables
    # ------------------------------------------------------------
    @classmethod
    def _load_env(cls):
        """Load and parse the .env file into cls._env."""
        cls.ROOT = cls._find_project_root()

        # Determine which .env file to load
        dev_path = cls.ROOT / ".env.dev"
        default_path = cls.ROOT / ".env"

        cls.ENV_FILE = dev_path if dev_path.exists() else default_path

        raw_vars = dotenv_values(cls.ENV_FILE)

        for key, raw_value in raw_vars.items():
            parsed = cls.parse_value(raw_value)
            cls._env[key] = parsed
            # print()

    # ------------------------------------------------------------
    # Public Accessors
    # ------------------------------------------------------------
    @classmethod
    def get(cls, key, default=None):
        return cls._env.get(key, default)

    @classmethod
    def __getattr__(cls, key):
        if key in cls._env:
            return cls._env[key]
        raise AttributeError(f"{key} not found in Settings")

    @classmethod
    def __getitem__(cls, key):
        if key in cls._env:
            return cls._env[key]
        raise KeyError(f"{key} not found in Settings")

    @classmethod
    def __env__(cls):
        return cls._env

    @property
    def env(self):
        return self._env


# ------------------------------------------------------------
# Initialize at import time (runs exactly once)
# ------------------------------------------------------------
Settings._load_env()

# Export environment dictionary for easy importing
ENV = Settings.__env__()
