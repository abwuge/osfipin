#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import json
from datetime import datetime, timezone
import concurrent.futures
from config import Config
from language import get_language_instance


def make_api_request(config):
    """
    Make API request using configuration
    """
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
        response = requests.request("GET", url, headers=headers, data=payload)
        return response.text
    except requests.RequestException as e:
        return f"Request error: {str(e)}"


def _fetch_world_time_api():
    """
    Fetch time from WorldTimeAPI

    Returns:
        datetime or None: Time from API if successful, None otherwise
    """
    try:
        response = requests.get("http://worldtimeapi.org/api/ip", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "datetime" in data:
                # Format: 2023-04-17T12:34:56.789123+00:00
                return datetime.fromisoformat(data["datetime"])
    except Exception:
        pass
    return None


def _fetch_world_clock_api():
    """
    Fetch time from WorldClockAPI

    Returns:
        datetime or None: Time from API if successful, None otherwise
    """
    try:
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
                    return dt.replace(tzinfo=timezone.utc)
                else:
                    return datetime.fromisoformat(time_str)
    except Exception:
        pass
    return None


def _fetch_apihz_api(config):
    """
    Fetch time from apihz time service

    Args:
        config: Configuration instance for API credentials

    Returns:
        datetime or None: Time from API if successful, None otherwise
    """
    try:
        api_id = config.get("apihz_id")
        api_key = config.get("apihz_key")
        apihz_url = (
            f"https://cn.apihz.cn/api/time/getapi.php?id={api_id}&key={api_key}&type=2"
        )

        response = requests.get(apihz_url, timeout=5)
        if response.status_code == 200:
            data = response.json()

            if data.get("code") == 200:
                time_str = data.get("msg")
                # Format: 2024-11-12 13:14:15
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
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
    print(lang.get("fetching_network_time"))

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
                    print(lang.get(f"{api_name}_api_success"))

                    # Cancel remaining futures
                    for f in futures:
                        if f != future and not f.done():
                            f.cancel()

                    return result
            except Exception:
                continue

    # If all APIs fail, fall back to local time
    print(lang.get("network_time_error"))
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
    # Parse the end time
    time_end = datetime.strptime(time_end_str, "%Y-%m-%d %H:%M:%S")

    # Make both times timezone-naive for comparison if current_time has timezone
    if current_time.tzinfo:
        # Convert to local time and remove tzinfo
        current_time = current_time.astimezone().replace(tzinfo=None)

    # Calculate difference
    diff = time_end - current_time

    # Extract days, hours, minutes and seconds
    days = diff.days
    seconds = diff.seconds
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return days, hours, minutes, seconds


def main():
    """
    Main function
    """
    # Load configuration first
    config = Config()

    # Initialize language support with existing config instance
    # to avoid circular imports
    lang = get_language_instance(config_instance=config)

    # Check if the config file was newly created
    if config.is_newly_created:
        print(lang.get("config_created"))
        print(lang.get("config_path", config.config_path))
        sys.exit(0)

    # Display config loading message
    print(lang.get("config_loaded", config.config_path))

    # Get current time (from network or local)
    current_time = get_current_time(lang, config)

    # Make API request
    print(lang.get("making_request"))
    result = make_api_request(config)

    # Parse JSON response
    try:
        response_data = json.loads(result)

        # Check if API request was successful
        if not response_data.get("isOk", False) or response_data.get("isError", True):
            # Extract error message from response
            error_message = response_data.get("error", "Unknown error")
            print(lang.get("api_error", error_message))
            sys.exit(1)

        # Get list of items from response
        items = response_data.get("data", {}).get("list", [])

        # Get target mark from config
        target_mark = config.get("target_mark", "")

        # Find item with the specified mark
        found_item = None
        for item in items:
            if item.get("mark") == target_mark:
                found_item = item
                break

        # If item not found, display error and exit
        if not found_item:
            print(lang.get("mark_not_found", target_mark))
            sys.exit(1)

        # Get time_end value
        time_end = found_item.get("time_end")

        # Calculate time difference using network time
        days, hours, minutes, seconds = calculate_time_difference(
            time_end, current_time
        )

        # Display time difference
        print(lang.get("time_remaining", days, hours, minutes, seconds))

        # Display certificate information (domains and expiry date)
        domains = found_item.get("domains", [])
        domains_str = ", ".join(domains) if domains else "N/A"
        print(lang.get("certificate_info", domains_str, time_end))

    except json.JSONDecodeError:
        print(lang.get("request_error", "Invalid JSON response"))
        sys.exit(1)
    except Exception as e:
        print(lang.get("request_error", str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
