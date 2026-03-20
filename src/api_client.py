import requests
import json
import os
from datetime import datetime

API_URL = "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_latest_log_data():
    """获取最近一次保存的日志数据"""
    logs_dir = os.path.join(PROJECT_ROOT, "logs")
    if not os.path.exists(logs_dir):
        return None

    # 遍历找到最新的日志文件
    latest_file = None
    latest_mtime = 0

    for root, dirs, files in os.walk(logs_dir):
        for f in files:
            if f.endswith('.json'):
                filepath = os.path.join(root, f)
                mtime = os.path.getmtime(filepath)
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_file = filepath

    if latest_file:
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def data_changed(old_data, new_data):
    """比较两次数据是否有变化"""
    if old_data is None:
        return True

    old_remains = old_data.get("model_remains", [])
    new_remains = new_data.get("model_remains", [])

    # 比较每个模型的配额数据
    for new_model in new_remains:
        new_name = new_model.get("model_name")
        for old_model in old_remains:
            if old_model.get("model_name") == new_name:
                # 比较关键字段
                if (old_model.get("current_interval_usage_count") != new_model.get("current_interval_usage_count") or
                    old_model.get("current_interval_total_count") != new_model.get("current_interval_total_count") or
                    old_model.get("current_weekly_usage_count") != new_model.get("current_weekly_usage_count") or
                    old_model.get("current_weekly_total_count") != new_model.get("current_weekly_total_count")):
                    return True
                break
        else:
            # 新模型不在旧数据中
            return True

    return False

def save_to_logs(data):
    """保存请求数据到logs目录（仅当数据有变化时）"""
    # 检查数据是否有变化
    latest_data = get_latest_log_data()
    if not data_changed(latest_data, data):
        return  # 数据没有变化，不保存

    logs_dir = os.path.join(PROJECT_ROOT, "logs")

    # 按日期和小时创建子目录
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")  # 日期文件夹
    hour_str = now.strftime("%H")        # 小时文件夹
    minute_str = now.strftime("%M")      # 分钟（作为文件名）

    # 创建目录结构: logs/2026-03-19/00/
    hour_dir = os.path.join(logs_dir, date_str, hour_str)
    os.makedirs(hour_dir, exist_ok=True)

    # 文件名使用分钟
    filepath = os.path.join(hour_dir, f"{minute_str}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_remains(cookie: str, group_id: str):
    """拉取配额数据"""
    if not cookie:
        return None, "Cookie 不能为空"

    headers = {
        "Cookie": f"HERTZ-SESSION={cookie}",
        "Accept": "application/json"
    }

    url = f"{API_URL}?GroupId={group_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        base_resp = data.get("base_resp", {})
        status_code = base_resp.get("status_code", 0)

        if status_code == 0:
            save_to_logs(data)
            return data, None
        else:
            error_msg = base_resp.get("status_msg", "未知错误")
            return None, error_msg

    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.RequestException as e:
        return None, f"网络错误: {str(e)}"
    except json.JSONDecodeError:
        return None, "响应解析失败"
