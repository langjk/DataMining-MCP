# cache_utils.py
# 用于将内容保存为 JSON 文件或从 JSON 文件中加载内容（本地缓存）

import os
import json

def save_cache(content, folder, filename):
    """
    将内容保存为 JSON 文件
    """
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{filename}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

def load_cache(folder, filename):
    """
    从 JSON 文件中加载内容
    """
    path = os.path.join(folder, f"{filename}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"缓存文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
