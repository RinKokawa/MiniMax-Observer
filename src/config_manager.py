import os
import sys
import json

# 项目根目录（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    # 打包后配置写在 exe 同级目录
    bundle_dir = sys._MEIPASS
    PROJECT_ROOT = os.path.dirname(bundle_dir)
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")

DEFAULT_CONFIG = {
    "cookie": "",
    "group_id": "YOUR_GROUP_ID_HERE",
    "refresh_interval": 15,  # minutes
    "auto_start": False,
    "minimize_to_tray": True
}

def ensure_config_file():
    """确保配置文件存在，不存在则创建默认配置"""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG.copy())

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except Exception:
            return DEFAULT_CONFIG.copy()
    # 文件不存在，创建默认配置
    ensure_config_file()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
