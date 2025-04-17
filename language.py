import locale
import os
import json
from config import Config


class Language:
    def __init__(self, lang_code=None, config_instance=None):
        """
        Initialize language support

        Args:
            lang_code: Manual language code override (en_us/zh_cn)
            config_instance: Existing Config instance to avoid circular import
        """
        # Use provided config or create new one
        self.config = config_instance if config_instance else Config()
        self.translations = {}

        # Load available translations
        self.available_languages = self._get_available_languages()

        # Load translations
        for lang in self.available_languages:
            self.translations[lang] = self._load_language_file(lang)

        # Determine language to use
        self.current_lang = self._determine_language(lang_code)

    def _get_available_languages(self):
        """
        Get list of available languages by scanning lang directory

        Returns:
            list: Available language codes
        """
        lang_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lang")
        available_langs = []

        if os.path.exists(lang_dir):
            for file in os.listdir(lang_dir):
                if file.endswith(".json"):
                    lang_code = os.path.splitext(file)[0]
                    available_langs.append(lang_code)

        return available_langs or ["en_us"]  # Default to English if no languages found

    def _load_language_file(self, lang_code):
        """
        Load language translations from JSON file

        Args:
            lang_code: Language code to load

        Returns:
            dict: Language translations
        """
        lang_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "lang", f"{lang_code}.json"
        )

        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading language file {lang_file}: {str(e)}")

        return {}  # Return empty dict if file doesn't exist or can't be loaded

    def _determine_language(self, lang_code=None):
        """
        Determine which language to use based on priority:
        1. Manual override parameter
        2. Config setting
        3. System language
        4. Default to English

        Returns:
            str: Language code (en_us/zh_cn)
        """
        # 1. Use manual override if provided and available
        if lang_code in self.translations:
            return lang_code

        # 2. Check config file
        config_lang = self.config.get("language")
        if config_lang != "auto" and config_lang in self.translations:
            return config_lang

        # 3. Check system language
        try:
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                if system_lang.startswith("zh"):
                    if "zh_cn" in self.translations:
                        return "zh_cn"
                    elif "zh_tw" in self.translations:
                        return "zh_tw"
        except Exception:
            pass

        # 4. Default to English or first available language
        if "en_us" in self.translations:
            return "en_us"
        elif self.translations:
            return next(iter(self.translations))

        return "en_us"  # Fallback to English ID even if not available

    def get(self, key, *args):
        """
        Get translated text by key

        Args:
            key: Translation key
            *args: Format arguments

        Returns:
            str: Translated text
        """
        # Get translation from current language or fallback to English
        text = self.translations.get(self.current_lang, {}).get(key)
        if text is None:
            text = self.translations.get("en_us", {}).get(key, key)

        # Format with arguments if provided
        if args:
            return text.format(*args)
        return text

    def change_language(self, lang_code):
        """
        Change current language

        Args:
            lang_code: Language code (en_us/zh_cn)

        Returns:
            bool: True if language was changed, False otherwise
        """
        if lang_code in self.translations:
            self.current_lang = lang_code
            # Save to config
            self.config.set("language", lang_code)
            return True
        return False

    def get_available_languages(self):
        """
        Get list of available languages

        Returns:
            dict: Dictionary of available language codes and names
        """
        language_names = {"en_us": "English", "zh_cn": "中文"}

        result = {}
        for lang in self.available_languages:
            result[lang] = language_names.get(lang, lang)

        return result


# Create global language instance
_language_instance = None


def get_language_instance(lang_code=None, config_instance=None):
    """
    Get language instance (singleton pattern)

    Args:
        lang_code: Optional language code override
        config_instance: Existing Config instance to avoid circular import

    Returns:
        Language: Language instance
    """
    global _language_instance
    if _language_instance is None:
        _language_instance = Language(lang_code, config_instance)
    return _language_instance
