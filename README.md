# MiniMax Observer

一个简洁的 MiniMax API 配额监控工具。

## 功能

- 实时监控 API 配额使用情况
- 支持多模型切换查看
- 每分钟自动刷新（可配置间隔）
- 请求数据自动保存到本地 logs 目录

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制 `config.json.example` 为 `config.json`，然后填写以下信息：

1. **cookie** - HERTZ-SESSION Cookie，登录 MiniMax 后从浏览器获取
2. **group_id** - 从 MiniMax 平台获取

## 使用

```bash
python -m src.main
```

或者

```bash
cd src
python main.py
```

### 设置

点击界面右上角"设置"按钮，可以配置：
- Cookie 和 Group ID
- 刷新间隔（1分钟/5分钟/15分钟/30分钟/1小时）

## 文件结构

```
minimax-monitor/
├── src/
│   ├── __init__.py
│   ├── main.py          # 入口文件
│   ├── api_client.py    # API 请求
│   ├── ui.py           # 界面逻辑
│   ├── database.py     # 数据库
│   ├── config_manager.py # 配置管理
│   └── observer-logo.svg # Logo
├── config.json.example  # 配置示例
├── requirements.txt     # 依赖
└── README.md
```

## 日志

每次请求成功后，会在 `logs/` 目录保存 JSON 文件，命名格式：`YYYY-MM-DD/HH/MM.json`

## 技术栈

- Python 3
- Tkinter (GUI)
- Requests (HTTP)
- Matplotlib (图表)
- Pystray (系统托盘)
- CairoSVG (图标渲染)
