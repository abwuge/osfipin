#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import json
from datetime import datetime, timezone
import concurrent.futures
from config import Config
from language import get_language_instance
from logger import initialize_logger, get_logger


def make_api_request(config):
    """
    Make API request using configuration
    """
    logger = get_logger()

    # Prepare API URL
    base_url = config.get("api_url")
    endpoint = "/api/user/Order/list"
    url = f"{base_url}{endpoint}"

    # Prepare authorization header with Bearer token:user format
    token = config.get("token")
    username = config.get("username")
    auth_value = f"Bearer {token}:{username}"

    # Set up headers and payload
    headers = {"Authorization": auth_value}
    payload = {}

    # Make the request
    try:
        logger.debug("logger.debug.api.request", url)
        response = requests.request("GET", url, headers=headers, data=payload)
        logger.debug("logger.debug.received.response", response.status_code)
        return response.text
    except requests.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(error_msg)
        return error_msg


def _fetch_world_time_api():
    """
    Fetch time from WorldTimeAPI

    Returns:
        datetime or None: Time from API if successful, None otherwise
    """
    logger = get_logger()

    try:
        logger.debug("api.time.worldtime.fetching")
        response = requests.get("http://worldtimeapi.org/api/ip", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "datetime" in data:
                # Format: 2023-04-17T12:34:56.789123+00:00
                logger.debug("api.time.worldtime.parse.success")
                return datetime.fromisoformat(data["datetime"])
        logger.debug("api.time.worldtime.failed", response.status_code)
    except Exception as e:
        logger.debug("api.time.worldtime.exception", str(e))

    return None


def _fetch_world_clock_api():
    """
    Fetch time from WorldClockAPI

    Returns:
        datetime or None: Time from API if successful, None otherwise
    """
    logger = get_logger()

    try:
        logger.debug("api.time.worldclock.fetching")
        response = requests.get("http://worldclockapi.com/api/json/utc/now", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "currentDateTime" in data:
                time_str = data["currentDateTime"]
                # Format: 2023-04-17T12:34:56.789Z
                # Remove 'Z' if present and parse
                if time_str.endswith("Z"):
                    time_str = time_str[:-1]
                    dt = datetime.fromisoformat(time_str)
                    logger.debug("api.time.worldclock.parse.success")
                    return dt.replace(tzinfo=timezone.utc)
                else:
                    logger.debug("api.time.worldclock.parse.success")
                    return datetime.fromisoformat(time_str)
        logger.debug("api.time.worldclock.failed", response.status_code)
    except Exception as e:
        logger.debug("api.time.worldclock.exception", str(e))

    return None


def _fetch_apihz_api(config):
    """
    Fetch time from apihz time service

    Args:
        config: Configuration instance for API credentials

    Returns:
        datetime or None: Time from API if successful, None otherwise
    """
    logger = get_logger()

    try:
        api_id = config.get("apihz_id")
        api_key = config.get("apihz_key")
        apihz_url = (
            f"https://cn.apihz.cn/api/time/getapi.php?id={api_id}&key={api_key}&type=2"
        )

        logger.debug("api.time.apihz.fetching")
        response = requests.get(apihz_url, timeout=5)
        if response.status_code == 200:
            data = response.json()

            if data.get("code") == 200:
                time_str = data.get("msg")
                # Format: 2024-11-12 13:14:15
                logger.debug("api.time.apihz.parse.success")
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

        logger.debug("api.time.apihz.failed", response.status_code)
    except Exception as e:
        logger.debug("api.time.apihz.exception", str(e))

    return None


def get_current_time(lang, config):
    """
    Get current time from network APIs or local time if all APIs fail

    Args:
        lang: Language instance for localized messages
        config: Configuration instance for API credentials

    Returns:
        datetime: Current time (from network or local)
    """
    logger = get_logger()
    logger.info("logger.info.fetching.network.time")

    # Use ThreadPoolExecutor to make API calls in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Start all API fetch tasks
        futures = {
            executor.submit(_fetch_world_time_api): "worldtime",
            executor.submit(_fetch_world_clock_api): "worldclock",
            executor.submit(_fetch_apihz_api, config): "apihz",
        }

        # Wait for the first successful result or all to complete
        for future in concurrent.futures.as_completed(futures):
            api_name = futures[future]
            try:
                result = future.result()
                if result is not None:
                    # Success - we have a valid datetime
                    # Display which specific API provided the time
                    logger.info(f"api.time.{api_name}.success")

                    # Cancel remaining futures
                    for f in futures:
                        if f != future and not f.done():
                            f.cancel()

                    return result
            except Exception as e:
                logger.debug("api.executor.exception", api_name, str(e))
                continue

    # If all APIs fail, fall back to local time
    logger.warning("logger.error.network.time")
    return datetime.now()


def calculate_time_difference(time_end_str, current_time):
    """
    Calculate the difference between current time and end time

    Args:
        time_end_str: End time in format "YYYY-MM-DD HH:MM:SS"
        current_time: Current datetime object

    Returns:
        tuple: (days, hours, minutes, seconds) remaining
    """
    logger = get_logger()

    # Parse the end time
    time_end = datetime.strptime(time_end_str, "%Y-%m-%d %H:%M:%S")
    logger.debug("logger.debug.end.time.info", time_end_str, current_time)

    # Make both times timezone-naive for comparison if current_time has timezone
    if current_time.tzinfo:
        # Convert to local time and remove tzinfo
        current_time = current_time.astimezone().replace(tzinfo=None)
        logger.debug("logger.debug.time.converted")

    # Calculate difference
    diff = time_end - current_time

    # Extract days, hours, minutes and seconds
    days = diff.days
    seconds = diff.seconds
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    logger.debug("logger.debug.time.difference", days, hours, minutes, seconds)
    return days, hours, minutes, seconds


def main():
    """
    Main function
    """
    # Load configuration first
    config = Config()

    # Call validate_config to ensure all required keys exist
    config.validate_config()

    # Initialize logger with configuration
    log_settings = config.get("log_settings", {})
    logger = initialize_logger(
        log_dir=log_settings.get("log_dir", "logs"),
        console_level=log_settings.get("console_level", "info"),
        file_level=log_settings.get("file_level", "debug"),
        max_size=int(log_settings.get("max_size_mb", 5)) * 1024 * 1024,
        backup_count=int(log_settings.get("backup_count", 3)),
    )

    # Initialize language support with existing config instance
    # to avoid circular imports
    lang = get_language_instance(config_instance=config)

    # Set language instance for logger
    logger.set_language_instance(lang)

    logger.debug("app.started")

    # Check if the config file was newly created
    if config.is_newly_created:
        logger.info("config.created")
        logger.info("config.path", config.config_path)
        sys.exit(0)

    # Display config loading message
    logger.info("config.loaded", config.config_path)

    # Get current time (from network or local)
    current_time = get_current_time(lang, config)

    # Make API request
    logger.info("logger.info.making.request")
    result = make_api_request(config)

    # Parse JSON response
    try:
        response_data = json.loads(result)
        logger.debug("logger.debug.parsed.api.response")

        # Check if API request was successful
        if not response_data.get("isOk", False) or response_data.get("isError", True):
            # Extract error message from response
            error_message = response_data.get("error", "Unknown error")
            logger.error("api.error", error_message)
            sys.exit(1)

        # Get list of items from response
        items = response_data.get("data", {}).get("list", [])
        logger.debug("logger.debug.found.items", len(items))

        # Get target mark from config
        target_mark = config.get("target_mark", "")
        logger.debug("logger.debug.looking.mark", target_mark)

        # Find item with the specified mark
        found_item = None
        for item in items:
            if item.get("mark") == target_mark:
                found_item = item
                logger.debug("logger.debug.found.item.mark")
                break

        # If item not found, display error and exit
        if not found_item:
            logger.error("logger.error.mark.not.found", target_mark)
            sys.exit(1)

        # Get time_end value
        time_end = found_item.get("time_end")
        logger.debug("logger.debug.item.end.time", time_end)

        # Calculate time difference using network time
        days, hours, minutes, seconds = calculate_time_difference(
            time_end, current_time
        )

        # Display time difference
        logger.info("logger.info.time.remaining", days, hours, minutes, seconds)

        # Display certificate information (domains and expiry date)
        domains = found_item.get("domains", [])
        domains_str = ", ".join(domains) if domains else "N/A"
        logger.info("certificate.info", domains_str, time_end)

    except json.JSONDecodeError:
        logger.error("logger.error.request", "Invalid JSON response")
        sys.exit(1)
    except Exception as e:
        logger.error("logger.error.request", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
