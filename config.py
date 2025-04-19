import os
import json


class Config:
    def __init__(self, config_path="config.json"):
        """
        Initialize Config class with path to config file
        """
        self.config_path = config_path
        self.config = {}
        self.is_newly_created = False
        self.load_config()

    def load_config(self):
        """
        Load configuration from file or create default if not exists
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                self.is_newly_created = False
            except json.JSONDecodeError:
                print("Error parsing config file. Creating default configuration.")
                self._create_default_config()
                self.is_newly_created = True
        else:
            print("Config file not found. Creating default configuration.")
            self._create_default_config()
            self.is_newly_created = True

    def _create_default_config(self):
        """
        Create default configuration
        """
        self.config = {
            "api_url": "https://api.xwamp.com",
            "username": "user@example.com",
            "token": "your_token_here",
            "language": "auto",
            "target_mark": "",
            "apihz_id": "88888888",
            "apihz_key": "88888888",
            "is_path": False,
            "log_settings": {
                "log_dir": "logs",
                "console_level": "info",
                "file_level": "debug",
                "max_size_mb": 5,
                "backup_count": 3,
            },
        }
        self.save_config()

    def validate_config(self):
        """
        Validate configuration file integrity, ensure all required keys exist
        Add default values for missing keys
        """
        default_config = {
            "api_url": "https://api.xwamp.com",
            "username": "user@example.com",
            "token": "your_token_here",
            "language": "auto",
            "target_mark": "",
            "apihz_id": "88888888",
            "apihz_key": "88888888",
            "is_path": False,
            "log_settings": {
                "log_dir": "logs",
                "console_level": "info",
                "file_level": "debug",
                "max_size_mb": 5,
                "backup_count": 3,
            },
        }

        # Check for missing top-level keys
        for key, default_value in default_config.items():
            if key not in self.config:
                self.config[key] = default_value

        # Check for missing nested log settings
        if isinstance(self.config.get("log_settings"), dict):
            for key, default_value in default_config["log_settings"].items():
                if key not in self.config["log_settings"]:
                    self.config["log_settings"][key] = default_value
        else:
            self.config["log_settings"] = default_config["log_settings"]

        # Save updated config if changes were made
        self.save_config()

    def save_config(self):
        """
        Save current configuration to file
        """
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        """
        Get configuration value by key
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """
        Set configuration value and save to file
        """
        self.config[key] = value
        self.save_config()
