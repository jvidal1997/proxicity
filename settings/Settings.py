from dotenv import dotenv_values
import re
import os


class Settings:
    VAR_PATTERN = re.compile(r"\${(\w+)}")  # matches ${VAR_NAME}

    def __init__(self, env_path):
        self._config = dotenv_values(env_path)
        self._expand_all_vars()

    def _expand_var(self, value):
        """Recursively expand ${VAR} in a string."""
        def replacer(match):
            var_name = match.group(1)
            return self._config.get(var_name, match.group(0))
        new_value = value
        while "${" in new_value:
            new_value = self.VAR_PATTERN.sub(replacer, new_value)
        return new_value

    def _expand_all_vars(self):
        """Expand all variable references in the config dict."""
        for key, value in self._config.items():
            if isinstance(value, str):
                self._config[key] = self._expand_var(value)

    def _parse_value(self, value):
        """Convert strings to Python types automatically."""
        # 1. Parse comma-separated arrays
        if "," in value:
            return [v.strip() for v in value.split(",")]

        # 2. Convert booleans
        lower = value.lower()
        if lower == "true":
            return True
        if lower == "false":
            return False

        # 3. Convert integers
        if value.isdigit():
            return int(value)

        # Otherwise return raw string
        return value

    def __getattr__(self, name):
        if name in self._config:
            return self._parse_value(self._config[name])
        raise AttributeError(f"No such setting: {name}")


# Global settings instance
settings = Settings(".env.dev" if os.path.exists(".env.dev") else ".env.test")
