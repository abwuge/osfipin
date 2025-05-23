<div align="center">
  <h1>来此加密自动重申 (API)</h1>
  
  [![English](https://badgen.net/badge/Language/English/blue?icon=github)](README_EN.md) [![简体中文](https://badgen.net/badge/语言/简体中文/red?icon=github)](README.md) [![LICENSE](https://badgen.net/static/license/MIT/black)](LICENSE)
</div>

---

> 来此加密无理由判定本人域名违规，本人不再使用来此加密，改用 certbot 了，本项目不再维护。

## 📝 简介

这是一个使用Python通过来此加密API自动重申SSL证书的脚本。

只需：
- 您的来此加密账户和API密钥
- 需要自动重申的证书的备注
- 定时运行该脚本

脚本即可在可重申时自动为您重新申请证书，返回完整证书链（`fullchain.crt`）和私钥（`private.pem`）

## ⚙️ 安装和依赖

### 系统要求

- Python 3.6 或更高版本
- 互联网连接（用于API请求和获取网络时间）

### 安装步骤

1. 克隆或下载此仓库：

```bash
git clone https://github.com/abwuge/osfipin.git
cd osfipin
```

2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

如果您在中国，可以尝试使用清华源加速下载：
```bash
pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

## 🔧 配置

首次运行程序时会自动创建一个默认的`config.json`配置文件。您需要编辑此文件并填入您的账户信息：

```json
{
    "api_url": "https://api.xwamp.com",
    "username": "your_email@example.com",
    "token": "your_api_token",
    "language": "zh_cn",
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

配置项说明：

- `api_url`：来此加密API地址（通常不需要修改）
- `username`：您的来此加密账户邮箱
- `token`：您的API令牌（在来此加密控制面板获取）
- `language`：语言设置（`zh_cn`或`en_us`或`auto`自动检测系统语言）
- `target_mark`：要监控的证书备注
- `apihz_id`：接口盒子的API ID，默认使用88888888
- `apihz_key`：接口盒子的API密钥，默认使用88888888
- `is_path`：是否使用路径参数模式，通常设为false
- `log_settings`：日志配置
  - `log_dir`：日志存储目录
  - `console_level`：控制台日志级别（info、debug、warning、error）
  - `file_level`：文件日志级别
  - `max_size_mb`：单个日志文件最大大小（MB）
  - `backup_count`：保留的日志文件数量

其中，接口盒子是获取网络时间的一种方案，程序会尝试多种API来获取精确的网络时间。

## 🚀 使用方法

配置完成后，请首先尝试直接运行主程序：
```bash
python main.py
```

程序将：
1. 尝试从多个API获取精确的网络时间，若均失败则使用本地时间
2. 连接到来此加密API获取证书信息
3. 计算并显示证书剩余有效时间
4. 显示证书的域名和到期日期
5. 检查证书是否即将过期（少于14天）
6. 如需要，自动申请并下载新证书，保存到data目录下

示例输出（中文）：
```
已加载配置文件：config.json
正在获取网络时间...
成功从接口盒子获取时间
正在发送API请求...
剩余时间：80 天 15 小时 23 分钟 45 秒
证书信息 - 域名: example.com, www.example.com, 有效期至: 2025-07-06 12:00:00
暂停1秒以避免高并发问题...
证书无需重申。域名ID: 12345
```

当证书需要续期时，输出示例：
```
已加载配置文件：config.json
正在获取网络时间...
成功从WorldTimeAPI获取时间
正在发送API请求...
剩余时间：10 天 5 小时 45 分钟 20 秒
证书信息 - 域名: example.com, www.example.com, 有效期至: 2025-05-01 12:00:00
暂停1秒以避免高并发问题...
证书将在不到14天内过期！域名ID: 12345
成功续期证书。响应ID: 67890
等待1秒后开始下载证书...
证书下载并保存成功
```

### 自动定时执行

为了确保证书能够自动更新，建议将脚本添加到crontab定时任务中。在Linux系统上，您可以按照以下步骤操作：

1. 打开crontab编辑器：
```bash
crontab -e
```

2. 添加以下内容，设置在每天早上5-8点之间的固定时间执行（建议选择一个服务器负载较低的时间）：
```
# 在每天凌晨5:20执行证书更新
20 5 * * * cd /path/to/osfipin && /usr/bin/python3 main.py >> /path/to/osfipin/logs/cron.log 2>&1
```

3. 保存并关闭编辑器

您也可以根据需要选择早上5-8点之间的任意时间，只需修改上面命令中的小时和分钟数字。

在Windows系统上，您可以使用任务计划程序设置类似的定时任务。

## 🌐 多语言支持

此程序支持多种语言，目前包括：
- 简体中文 (zh_cn)
- 英文 (en_us)

可以通过以下方式更改语言：
1. 在`config.json`中修改`language`设置
2. 将其设为`auto`以使用系统默认语言

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出功能请求！

代码使用`ruff`进行代码格式化和检查。

---

感谢使用本工具！

