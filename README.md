# Apple Spyder

> 监控 Apple 软件发布 RSS 和 Apple 配件 OTA 更新数据，并通过已配置的通知渠道发送提醒。

## 背景

Apple Spyder 是一个用于监控 Apple 软件发布 RSS 和 Apple 配件 OTA 更新数据的服务。

当前仓库基于 Hackl0us 的原始 `apple-spyder` 项目，并在其基础上进行了本地修改与结构重构，涵盖打包方式、配置方式、部署流程、调度器和通知链路等方面。

- 上游仓库：https://github.com/Hackl0us/apple-spyder
- 许可证：GPL-3.0

## 功能特性

- 监控 Apple Developer RSS 发布信息
- 监控 Apple 配件 OTA 更新数据
- 通过 Telegram 和 Weibo 发送通知
- 通过 `telegram.chat_ids` 支持多个 Telegram 目标会话
- 内置支持 cron 表达式的调度器
- 可选的 Web API 和首页


## 安装

Apple Spyder 支持多种安装与部署方式。

### 环境要求

根据不同的运行方式，你可能需要：

- Python 3.11+
- 用于本地开发的 `uv`
- 用于容器部署的 Docker 和 Docker Compose


### 使用 Docker Compose 运行

仓库中已经包含 [docker-compose.yml](./docker-compose.yml)

启动前请先参考下方 uv 运行部分中的配置步骤，创建 `config/config.yaml` 并填入真实配置。

启动：

```bash
docker compose up -d
```

其他常用命令：
```bash
docker compose logs -f # 查看日志
docker compose down # 停止服务
```



### 使用 [uv](https://github.com/astral-sh/uv) 运行

1. 克隆本仓库：

```bash
git clone https://github.com/ByteColtX/apple-spyder.git
cd apple-spyder
```

2. 编辑配置：

```bash
cp config/config.example.yaml config/config.yaml
# 编辑 config/config.yaml，填入真实配置
```

<details>
<summary><b>配置示例</b></summary>

```yaml
# Copy this file to config/config.yaml and fill in your real credentials.
weibo:
  enabled: false
  app_key: your_app_key
  app_secret: your_app_secret
  redirect_uri: https://example.com/callback
  access_token: your_access_token
  real_ip: 127.0.0.1

telegram:
  enabled: true
  bot_token: 123456:your_bot_token
  chat_ids:
    - 123456789
    - 1145141919810

urls:
  apple_developer_rss: https://developer.apple.com/news/releases/rss/releases.rss

web:
  enabled: true
  host: 0.0.0.0
  port: 5005

scheduler:
  enabled: true
  cron_expr: "*/30 * * * *"
  run_on_startup: true

```


</details>


3. 安装依赖：

```bash
uv sync
```
4. 运行服务：

```bash
uv run python -m apple_spyder # 或者 uv run apple-spyder
```



## 数据库

SQLite 数据库会在首次运行时自动初始化。

- 数据库路径：`data/apple-spyder.db`
- Schema 路径：`src/apple_spyder/repositories/init_db.sql`

你不需要手动初始化数据库。


## API


- `GET /apple-spyder/software-release`: 检查 Apple Developer RSS，并在发现新条目时发送通知。

- `GET /apple-spyder/software-release/feed`: 获取当前 Apple Developer RSS 条目，以 JSON 格式返回。

- `GET /apple-spyder/accessory-ota-update`: 检查 Apple 配件 OTA 更新。

- `GET /apple-spyder/test-notify`: 通过已配置渠道发送一条手动测试通知。


## 致谢
- Hackl0us 的原始 `apple-spyder` 项目，提供了核心功能和灵感来源。

## 许可证

本项目采用 GPLv3 许可证。请确保你的使用方式符合许可证要求。
