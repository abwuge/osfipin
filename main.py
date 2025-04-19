#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import json
import time
from datetime import datetime, timezone
import threading
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


def make_renewal_api_request(config, domain_id, is_path=False):
    """
    Make API request for domain renewal

    Args:
        config: Configuration instance
        domain_id: Domain ID to renew
        is_path: Whether to use path parameter (default: False)

    Returns:
        dict: Parsed API response
    """
    logger = get_logger()

    # Prepare API URL
    base_url = config.get("api_url")
    endpoint = (
        f"/api/user/OrderDetail/renew?id={domain_id}&is_path={str(is_path).lower()}"
    )
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
        logger.debug("renewal.debug.api.request", url)
        response = requests.request("GET", url, headers=headers, data=payload)
        logger.debug("renewal.debug.api.response", response.status_code)

        # Parse and return JSON response
        return json.loads(response.text)
    except requests.RequestException as e:
        error_msg = f"Renewal request error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except json.JSONDecodeError:
        error_msg = "Invalid JSON response from renewal API"
        logger.error(error_msg)
        raise Exception(error_msg)


def download_certificate(config, cert_id):
    """
    Download certificate using provided ID

    Args:
        config: Configuration instance
        cert_id: Certificate ID to download

    Returns:
        dict: Parsed API response with certificate data
    """
    logger = get_logger()

    # Prepare API URL
    base_url = config.get("api_url")
    endpoint = f"/api/user/OrderDetail/down?id={cert_id}&type=json"
    url = f"{base_url}{endpoint}"

    # Prepare authorization header
    token = config.get("token")
    username = config.get("username")
    auth_value = f"Bearer {token}:{username}"

    # Set up headers
    headers = {"Authorization": auth_value}

    # Make the request
    try:
        logger.debug("certificate.download.request", url)
        response = requests.request("GET", url, headers=headers)
        logger.debug("certificate.download.response", response.status_code)

        # Parse and return JSON response
        return json.loads(response.text)
    except requests.RequestException as e:
        error_msg = f"Certificate download error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except json.JSONDecodeError:
        error_msg = "Invalid JSON response from certificate download API"
        logger.error(error_msg)
        raise Exception(error_msg)


def save_certificate_files(cert_data, mark):
    """
    Save certificate and key files to specified directory

    Args:
        cert_data: Certificate data containing cert and key
        mark: Mark for directory naming

    Returns:
        bool: True if files saved successfully, False otherwise
    """
    import os

    logger = get_logger()

    # Ensure data directory exists
    cert_dir = os.path.join("data", mark)
    os.makedirs(cert_dir, exist_ok=True)

    try:
        # Save certificate file (fullchain.crt)
        cert_file_path = os.path.join(cert_dir, "fullchain.crt")
        with open(cert_file_path, "w", encoding="utf-8") as f:
            f.write(cert_data.get("cert", ""))

        # Save private key file (private.pem)
        key_file_path = os.path.join(cert_dir, "private.pem")
        with open(key_file_path, "w", encoding="utf-8") as f:
            f.write(cert_data.get("key", ""))

        logger.info("certificate.save.success", cert_file_path, key_file_path)
        return True
    except Exception as e:
        logger.error("certificate.save.error", str(e))
        return False


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

    # Use a threading Event to signal that we've found a result
    # This allows us to immediately return as soon as any API succeeds
    success_event = threading.Event()
    result_container = []

    def fetch_time_from_api(api_func, api_name, *args):
        """Worker function to fetch time from a specific API"""
        # If another thread has already succeeded, don't even try
        if success_event.is_set():
            return

        try:
            # Make the API call with appropriate args
            if args:
                result = api_func(*args)
            else:
                result = api_func()

            # If we got a valid result, signal success and store the result
            if result:
                logger.info(f"api.time.{api_name}.success")
                result_container.append(result)
                # Signal to other threads that we're done
                success_event.set()
        except Exception:
            # Only log failures if no success has occurred yet
            if not success_event.is_set():
                logger.debug(f"api.time.{api_name}.exception", str(sys.exc_info()[1]))

    # Create and start threads for each API
    threads = []

    # WorldTime API thread
    wt_thread = threading.Thread(
        target=fetch_time_from_api, args=(_fetch_world_time_api, "worldtime")
    )
    threads.append(wt_thread)

    # WorldClock API thread
    wc_thread = threading.Thread(
        target=fetch_time_from_api, args=(_fetch_world_clock_api, "worldclock")
    )
    threads.append(wc_thread)

    # APIhz API thread
    apihz_thread = threading.Thread(
        target=fetch_time_from_api, args=(_fetch_apihz_api, "apihz", config)
    )
    threads.append(apihz_thread)

    # Start all threads
    for thread in threads:
        thread.daemon = True  # Make threads daemon so they don't block program exit
        thread.start()

    # Wait for either a success or timeout (max 5 seconds)
    success_event.wait(timeout=5)

    # If we got a result, return it immediately
    if result_container:
        return result_container[0]

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

        # Add pause notification before renewal check
        logger.info("renewal.info.pausing")
        time.sleep(1)

        # Get domain_id for potential renewal
        domain_id = found_item.get("id")

        # Check if remaining time is less than 14 days
        if days < 14:
            logger.warning("renewal.warning.expiring", domain_id)

            # Get is_path value from config, default to false
            is_path = config.get("is_path", False)

            try:
                # Call renewal API
                renewal_response = make_renewal_api_request(config, domain_id, is_path)

                # Check if renewal was successful
                if renewal_response.get("isOk", False) and not renewal_response.get(
                    "isError", True
                ):
                    response_id = renewal_response.get("data", {}).get("id")
                    logger.info("renewal.success", response_id)

                    # Wait 1 second before downloading certificate
                    logger.debug("certificate.download.waiting")
                    time.sleep(1)

                    try:
                        # Download certificate after renewal
                        cert_response = download_certificate(config, response_id)

                        # Check if download was successful
                        if cert_response.get("isOk", False) and not cert_response.get(
                            "isError", True
                        ):
                            cert_data = cert_response.get("data", {})

                            # Save certificate files
                            if cert_data and save_certificate_files(
                                cert_data, target_mark
                            ):
                                logger.info("certificate.download.save.success")
                            else:
                                logger.error("certificate.download.save.failed")
                        else:
                            # Extract error message from response
                            error_message = cert_response.get("error", "Unknown error")
                            logger.error("certificate.download.error", error_message)
                    except Exception as e:
                        logger.error("certificate.download.error", str(e))
                else:
                    # Extract error message from response
                    error_message = renewal_response.get("error", "Unknown error")
                    logger.error("renewal.error.api", error_message)
            except Exception as e:
                logger.error("renewal.error.process", str(e))
        else:
            # Certificate doesn't need renewal
            logger.info("renewal.not.needed", domain_id)

    except json.JSONDecodeError:
        logger.error("logger.error.request", "Invalid JSON response")
        sys.exit(1)
    except Exception as e:
        logger.error("logger.error.request", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
