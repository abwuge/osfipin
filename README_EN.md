<div align="center">
  <h1>OSFIPIN Auto Renewal (API)</h1>
  
  [![English](https://badgen.net/badge/Language/English/blue?icon=github)](README_EN.md) [![简体中文](https://badgen.net/badge/语言/简体中文/red?icon=github)](README.md) [![LICENSE](https://badgen.net/static/license/MIT/black)](LICENSE)
</div>

---

> OSFIPIN has no reason to judge that my domain name is illegal. I no longer use OSFIPIN, but use certbot, and this project is no longer maintained.

## 📝 Introduction

This is a Python script that automatically renews SSL certificates through the OSFIPIN API.

All you need:
- Your OSFIPIN account and API key
- The note of the certificate that needs to be automatically renewed
- Run this script regularly

The script will automatically apply for a new certificate when it's renewable, and return the complete certificate chain (`fullchain.crt`) and private key (`private.pem`)

## ⚙️ Installation and Dependencies

### System Requirements

- Python 3.6 or higher
- Internet connection (for API requests and network time)

### Installation Steps

1. Clone or download this repository:

```bash
git clone https://github.com/abwuge/osfipin.git
cd osfipin
```

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

If you are in China, you can try using the Tsinghua mirror to speed up the download:
```bash
pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

## 🔧 Configuration

When you run the program for the first time, a default `config.json` configuration file will be automatically created. You need to edit this file and enter your account information:

```json
{
    "api_url": "https://api.xwamp.com",
    "username": "your_email@example.com",
    "token": "your_api_token",
    "language": "en_us",
    "target_mark": "your_domain_mark",
    "apihz_id": "88888888",
    "apihz_key": "88888888",
    "is_path": false,
    "log_settings": {
        "log_dir": "logs",
        "console_level": "info",
        "file_level": "debug",
        "max_size_mb": 5,
        "backup_count": 3
    }
}
```

Configuration details:

- `api_url`: OSFIPIN API URL (usually doesn't need modification)
- `username`: Your OSFIPIN account email
- `token`: Your API token (obtained from OSFIPIN control panel)
- `language`: Language setting (`zh_cn` or `en_us` or `auto` to detect system language)
- `target_mark`: The certificate mark name to monitor
- `apihz_id`: API ID for apihz service, default is 88888888
- `apihz_key`: API key for apihz service, default is 88888888
- `is_path`: Whether to use path parameter mode, usually set to false
- `log_settings`: Logging configuration
  - `log_dir`: Directory for storing logs
  - `console_level`: Console log level (info, debug, warning, error)
  - `file_level`: File log level
  - `max_size_mb`: Maximum size of each log file in MB
  - `backup_count`: Number of log files to retain

The apihz service is one solution for obtaining network time, and the program will try multiple APIs to get accurate network time.

## 🚀 Usage

After completing the configuration, please try running the main program directly:
```bash
python main.py
```

The program will:
1. Try to get accurate network time from multiple APIs, or use local time if all fail
2. Connect to the Xwamp API to retrieve certificate information
3. Calculate and display the remaining certificate validity time
4. Show the certificate's domains and expiration date
5. Check if the certificate is about to expire (less than 14 days)
6. If needed, automatically apply for and download a new certificate, saving it to the data directory

Example output (English):
```
Loaded configuration from: config.json
Fetching network time...
Successfully fetched time from WorldTimeAPI
Making API request...
Time remaining: 80 days 15 hours 23 minutes 45 seconds
Certificate info - Domains: example.com, www.example.com, Valid until: 2025-07-06 12:00:00
Pausing for 1 second to avoid high concurrency issues...
Certificate does not need renewal. Domain ID: 12345
```

When a certificate needs renewal, example output:
```
Loaded configuration from: config.json
Fetching network time...
Successfully fetched time from WorldTimeAPI
Making API request...
Time remaining: 10 days 5 hours 45 minutes 20 seconds
Certificate info - Domains: example.com, www.example.com, Valid until: 2025-05-01 12:00:00
Pausing for 1 second to avoid high concurrency issues...
Certificate will expire in less than 14 days! Domain ID: 12345
Successfully renewed certificate. Response ID: 67890
Waiting 1 second before downloading certificate...
Certificate downloaded and saved successfully
```

### Automated Scheduling

To ensure certificates are updated automatically, it's recommended to add the script to crontab scheduled tasks. On Linux systems, follow these steps:

1. Open the crontab editor:
```bash
crontab -e
```

2. Add the following content to set execution at a fixed time between 5-8 AM (choose a time when server load is typically low):
```
# Execute certificate update daily at 5:20 AM
20 5 * * * cd /path/to/osfipin && /usr/bin/python3 main.py >> /path/to/osfipin/logs/cron.log 2>&1
```

3. Save and close the editor

You can choose any time between 5-8 AM according to your needs by modifying the hour and minute values in the command above.

On Windows systems, you can set up similar scheduled tasks using Task Scheduler.

## 🌐 Multi-language Support

This program supports multiple languages, currently including:
- Simplified Chinese (zh_cn)
- English (en_us)

You can change the language by:
1. Modifying the `language` setting in `config.json`
2. Setting it to `auto` to use your system's default language

## 🤝 Contribution Guidelines

Contributions of code, issue reports, or feature requests are welcome!

The code uses `ruff` for code formatting and inspection.

---

Thank you for using this tool!

