import requests
import json
import os
from datetime import datetime

API_URL = "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def save_to_logs(data):
    """保存请求数据到logs目录"""
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
