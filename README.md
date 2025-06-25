# GitHub Actions 自动签到脚本  # **PS：只适用于无验证码的网页

这是一个使用 GitHub Actions 实现的自动签到脚本，可以定期对多个网站进行自动签到，并支持通过邮件或 Telegram 发送签到结果通知。项目采用模块化设计，支持轻松添加新的网站支持。


## 功能特点

- 支持多种网站自动签到（V2EX、Lixianla、HnHost等）
- 使用 GitHub Actions 实现定时任务，无需本地运行
- 支持多种通知方式（邮件、Telegram）
- 模块化设计，易于扩展新网站
- 详细的日志记录和错误处理

## 支持的网站

目前支持以下网站的自动签到：
- V2EX
- [Lixianla](https://lixianla.com)
- HnHost
- 更多网站可以通过添加插件支持

## 使用方法

### 1. Fork 仓库

首先，点击页面右上角的 "Fork" 按钮，将本仓库复制到你的 GitHub 账户下。

### 2. 配置 Secrets

在你的仓库页面，依次点击 "Settings" > "Secrets" > "New repository secret"，添加以下 Secrets：

| Secret 名称          | 描述                                                                 |
|----------------------|---------------------------------------------------------------------|
| CONFIG               | 你的配置文件内容（JSON格式），包含所有需要签到的网站信息                          |
| EMAIL_HOST           | 邮件服务器地址（如使用邮件通知）                                       |
| EMAIL_PORT           | 邮件服务器端口（如使用邮件通知）                                       |
| EMAIL_USER           | 发件人邮箱（如使用邮件通知）                                         |
| EMAIL_PASSWORD       | 发件人邮箱密码或授权码（如使用邮件通知）                               |
| EMAIL_RECIPIENTS     | 收件人邮箱列表，逗号分隔（如使用邮件通知）                              |
| TELEGRAM_BOT_TOKEN   | Telegram Bot Token（如使用 Telegram 通知）                            |
| TELEGRAM_CHAT_ID     | Telegram 聊天 ID（如使用 Telegram 通知）                              |

### 3. 配置签到任务

默认情况下，签到任务会每天 UTC 时间 00:00 执行。你可以通过修改 `.github/workflows/checkin.yml` 文件来调整执行时间。

### 4. 启用 GitHub Actions

在你的仓库页面，点击 "Actions" 标签，然后点击绿色按钮启用 GitHub Actions。

## 配置文件示例

配置文件采用 JSON 格式，示例如下：
{
    "global": {
        "timeout": 30,
        "retry_times": 3,
        "log_level": "INFO"
    },
    "sites": [
        {
            "name": "V2EX",
            "type": "v2ex",
            "config": {
                "cookies": {
                    "PB3_SESSION": "your_session_cookie",
                    "v2ex_tabs": "your_tabs_cookie"
                }
            }
        },
        {
            "name": "Lixianla",
            "type": "lixianla",
            "config": {
                "username": "your_username",
                "password": "your_password"
            }
        }
    ]
}
## 添加新网站支持

要添加新网站的支持，只需创建一个新的插件文件并实现必要的接口：

1. 在 `plugins` 目录下创建新文件，例如 `new_site.py`
2. 实现插件类，继承自 `BasePlugin`
3. 实现 `login` 和 `checkin` 方法
4. 添加 `register_plugin` 函数返回你的插件类

详细示例请参考现有插件文件。

## 通知设置

### 邮件通知

要启用邮件通知，需要配置以下 Secrets：
- EMAIL_HOST
- EMAIL_PORT
- EMAIL_USER
- EMAIL_PASSWORD
- EMAIL_RECIPIENTS

### Telegram 通知

要启用 Telegram 通知，需要配置以下 Secrets：
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

## 注意事项

- 请确保你的配置信息安全，不要在公开仓库中泄露敏感信息
- 部分网站可能有反爬虫机制，过于频繁的请求可能导致账号被封禁
- 建议合理设置签到频率，避免对网站造成不必要的负担
- 本项目仅供学习交流使用，请遵守相关网站的使用条款
    
