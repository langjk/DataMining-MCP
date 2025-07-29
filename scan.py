import os
import json
from pathlib import Path

def scan_directory(root_dir):
    file_info = []

    for root, dirs, files in os.walk(root_dir):
        for name in files:
            file_path = Path(root) / name
            file_info.append({
                "file_name": name,
                "file_path": str(file_path),
                "parent_dir": str(Path(root)),
                "file_size_kb": round(file_path.stat().st_size / 1024, 2),
                "last_modified": file_path.stat().st_mtime,
                "extension": file_path.suffix.lower()
            })

    return file_info

# 示例使用
if __name__ == "__main__":
    base_path = "./data"  # 替换为你的根目录路径
    info = scan_directory(base_path)
    with open("file_structure_summary.json", "w") as f:
        json.dump(info, f, indent=2)
