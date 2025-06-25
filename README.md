# 网站批量自动签到脚本

## 功能介绍

这是一个可以批量对多个网站进行自动签到的脚本，支持自定义扩展，目前已支持V2EX、GitHub等网站。脚本采用异步方式执行，提高签到效率，同时提供完善的日志记录和结果反馈。

## 安装依赖
pip install aiohttp beautifulsoup4
## 使用方法

1. 复制`config.json.example`为`config.json`
2. 根据需要修改配置文件，添加要签到的网站信息
3. 运行脚本：`python main.py`

## 配置说明

配置文件结构如下：
{
    "global": {
        "timeout": 30,  # 全局超时时间(秒)
        "retry_times": 3  # 失败重试次数
    },
    "sites": [
        {
            "name": "网站名称",
            "type": "网站类型",
            # 其他网站特定配置
        }
    ]
}
## 扩展支持

如果你想添加对新网站的支持，可以按照以下步骤操作：

1. 在`checkin_sites.py`中创建新的签到类，继承自`BaseCheckin`
2. 实现`login`和`checkin`方法
3. 在`SUPPORTED_SITES`字典中注册新的签到类

## 定时任务

你可以使用系统的定时任务功能(如crontab)来定期执行签到脚本：
# 每天早上8点执行签到
0 8 * * * cd /path/to/script && python3 main.py    
