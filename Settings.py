"""
Dynamic environment configuration loader for the application.

This module provides a robust, auto-initializing configuration system that:
    - Detects the project root dynamically by searching for a `.git` directory
      or a `.env` file, with a fallback to the current working directory.
    - Loads environment variables from `.env.dev` if it exists; otherwise
      falls back to `.env`.
    - Converts raw environment strings into appropriate Python types
      (bools, ints, floats, lists, email strings, and normalized absolute paths).
    - Exposes configuration variables globally through the `Settings` class
      and a plain `ENV` dictionary for convenience.

Core Components:
    - **Settings._find_project_root()**
      Locates the correct project root to ensure `.env` discovery works
      regardless of where the module is executed.

    - **Settings.parse_value()**
      Automatically parses environment variable strings into:
          * lists (comma-separated)
          * booleans
          * integers / floats
          * emails
          * filesystem paths (normalized to absolute paths)
          * raw strings (fallback)

    - **Settings._load_env()**
      Loads environment variables from the selected file, parses each value,
      and stores the results in the internal `_env` dictionary. This method
      is executed automatically once at import time.

    - **Public accessors**
      * `Settings.get(key, default)`
      * Attribute-style access (`Settings.KEY`)
      * Dictionary-style access (`Settings["KEY"]`)
      * Full environment access (`Settings.__env__()`)

Initialization:
    The environment is loaded immediately during module import, guaranteeing
    that all dependent modules have access to parsed configuration values
    without requiring explicit initialization calls.

Exports:
    - `ENV`: a direct reference to the parsed environment dictionary, suitable
      for lightweight imports where class-based access is unnecessary.

Intended Use:
    Import `Settings` or `ENV` from this module to access application-wide
    configuration values in a safe, typed, and consistent manner.

Dependencies:
    - python-dotenv
    - re
    - pathlib.Path
"""
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

    # Project Root Detection
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

    # Value Parser
    @staticmethod
    def parse_value(value: str):
        """
        Convert strings to Python types automatically by detecting the following formats:
            1. Parse comma-separated values -> list
            2. Booleans -> bool
            3. Integers -> number
            4. Floats -> number
            5. Emails -> string
            6. Filepaths -> string
            7. Strings -> string
        """
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

    # Loading Environment Variables
    @classmethod
    def _load_env(cls):
        """Load and parse the .env file into class variable `cls._env`."""
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

    # Public Accessors
    @classmethod
    def get(cls, key, default=None):
        """
        Retrieve a value from `cls._env[key]`.
        :param key: the key of the value to retrieve
        :param default: default value to return if `key` is not found
        :return: value from `cls._env[key]`
        """
        return cls._env.get(key, default)

    @classmethod
    def __getattr__(cls, key):
        """
        Retrieve a value from `cls._env[key]`.
        :param key: key of the value to retrieve
        :return: value from `cls._env[key]`
        """
        if key in cls._env:
            return cls._env[key]
        raise AttributeError(f"{key} not found in Settings")

    @classmethod
    def __getitem__(cls, key):
        """
        Retrieve a value from `cls._env[key]`.
        :param key: key of the value to retrieve
        :return: value from `cls._env[key]`
        """
        if key in cls._env:
            return cls._env[key]
        raise KeyError(f"{key} not found in Settings")

    @classmethod
    def __env__(cls):
        """
        Retrieve all environment variables from `cls._env`.
        :return: all environment variables from `cls._env`
        """
        return cls._env

    @property
    def env(self):
        """
        Retrieve all environment variables from `cls._env`.
        :return: all environment variables from `cls._env`
        """
        return self._env


# Initialize at import time (runs exactly once)
Settings._load_env()

# Export environment dictionary for easy importing
ENV = Settings.__env__()
