import sqlite3
import os
import sys
from datetime import datetime, timezone, timedelta

# 项目根目录（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    PROJECT_ROOT = os.path.dirname(bundle_dir)
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(PROJECT_ROOT, "data.db")

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            daily_used INTEGER,
            daily_total INTEGER,
            weekly_used INTEGER,
            weekly_total INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_history(timestamp)
    """)

    conn.commit()
    conn.close()

def save_usage(data: dict):
    """保存使用数据"""
    if not data or "model_remains" not in data:
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    for model in data["model_remains"]:
        # current_interval_usage_count 是剩余次数，需要计算已用次数
        interval_total = model.get("current_interval_total_count", 0)
        interval_remain = model.get("current_interval_usage_count", 0)
        interval_used = interval_total - interval_remain

        # 本周已用 = 本周总额 - 本周剩余
        weekly_total = model.get("current_weekly_total_count", 0)
        weekly_remain = model.get("current_weekly_usage_count", 0)
        weekly_used = weekly_total - weekly_remain if weekly_total > 0 else 0

        cursor.execute("""
            INSERT INTO usage_history (timestamp, model_name, daily_used, daily_total, weekly_used, weekly_total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            model.get("model_name"),
            interval_used,
            interval_total,
            weekly_used,
            weekly_total
        ))

    conn.commit()
    conn.close()

def get_history(days: int = 7):
    """获取历史记录"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 获取每天的汇总数据 - 使用MAX而非SUM，因为API返回的是累计值
    cursor.execute("""
        SELECT
            date(timestamp/1000, 'unixepoch', 'localtime') as day,
            model_name,
            MAX(daily_used) as daily_used,
            MAX(daily_total) as daily_total,
            MAX(weekly_used) as weekly_used,
            MAX(weekly_total) as weekly_total
        FROM usage_history
        WHERE timestamp >= ?
        GROUP BY day, model_name
        ORDER BY day DESC, model_name
    """, ((datetime.now() - timedelta(days=days)).timestamp() * 1000,))

    rows = cursor.fetchall()
    conn.close()

    return rows

def get_latest():
    """获取最新一条记录"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, model_name, daily_used, daily_total, weekly_used, weekly_total
        FROM usage_history
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


class Database:
    """数据库操作类"""

    @staticmethod
    def save_usage(data: dict):
        save_usage(data)

    @staticmethod
    def get_history(days: int = 7):
        return get_history(days)

    @staticmethod
    def get_latest():
        return get_latest()
