#!/usr/bin/env python3
"""清理logs目录中的重复数据"""

import os
import sys
import json
import hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

def get_data_hash(data):
    """获取数据的哈希值，用于比较是否相同"""
    model_remains = data.get("model_remains", [])
    hash_data = []
    for model in sorted(model_remains, key=lambda x: x.get("model_name", "")):
        hash_data.append((
            model.get("model_name"),
            model.get("current_interval_usage_count"),
            model.get("current_interval_total_count"),
            model.get("current_weekly_usage_count"),
            model.get("current_weekly_total_count"),
        ))
    return hashlib.md5(str(hash_data).encode()).hexdigest()

def get_all_logs():
    """获取所有日志文件"""
    logs = []
    if not os.path.exists(LOGS_DIR):
        return logs

    for root, dirs, files in os.walk(LOGS_DIR):
        for f in sorted(files):
            if f.endswith('.json'):
                filepath = os.path.join(root, f)
                mtime = os.path.getmtime(filepath)
                logs.append((filepath, mtime))
    return logs

def cleanup_logs():
    """清理重复的日志文件"""
    logs = get_all_logs()
    if not logs:
        print("没有找到日志文件")
        return 0

    seen_hashes = {}  # hash -> (filepath, mtime)
    duplicates = []

    print(f"正在扫描 {len(logs)} 个日志文件...")

    for filepath, mtime in logs:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data_hash = get_data_hash(data)

            if data_hash in seen_hashes:
                # 重复数据，保留较早的那个
                duplicates.append(filepath)
            else:
                seen_hashes[data_hash] = (filepath, mtime)

        except Exception as e:
            print(f"  跳过 {filepath}: {e}")

    # 删除重复文件
    deleted_count = 0
    for filepath in duplicates:
        os.remove(filepath)
        print(f"  删除: {filepath}")
        deleted_count += 1

    print(f"\n完成！删除了 {deleted_count} 个重复文件，保留了 {len(seen_hashes)} 个唯一数据")

    # 清理空目录
    cleanup_empty_dirs()

    return deleted_count

def cleanup_empty_dirs():
    """清理空目录"""
    for root, dirs, files in os.walk(LOGS_DIR, topdown=False):
        for d in dirs:
            dirpath = os.path.join(root, d)
            if not os.listdir(dirpath):  # 目录为空
                os.rmdir(dirpath)
                print(f"  删除空目录: {dirpath}")

if __name__ == "__main__":
    print("MiniMax Observer - 日志清理工具")
    print("=" * 40)
    cleanup_logs()
