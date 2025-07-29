# csv_reader.py
# 智能数据分析助手 MCP 子模块：CSV 文件读取与清洗工具

import pandas as pd
import os

def read_csv_clean(path, nrows=None, ncols=None, remove_header_repeats=True):
    """
    读取 CSV 文件，自动处理中文编码与重复表头行

    参数:
        path (str): 文件路径
        nrows (int): 可选，仅读取前 N 行
        ncols (int): 可选，仅保留前 M 列
        remove_header_repeats (bool): 是否删除与首行重复的表头行

    返回:
        df (DataFrame): 清洗后的数据
        metadata (dict): 文件编码、行数、列数、去重信息等
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ 文件未找到: {path}")

    encodings = ['utf-8-sig', 'gbk', 'utf-16', 'latin1']
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc, engine='python', on_bad_lines='skip')
            used_encoding = enc
            break
        except Exception:
            continue
    else:
        raise ValueError(f"❌ 无法识别编码: {path}")

    duplicate_count = 0
    if remove_header_repeats and not df.empty:
        first_row = df.iloc[0]
        duplicate_rows = df.apply(lambda row: row.equals(first_row), axis=1)
        duplicate_count = duplicate_rows.sum()
        df = df[~duplicate_rows]
    
    # 修复列名编码问题
    column_mapping = {
        'ʱ��': '时间',
        'Ч��': '效率'
    }
    df.columns = [column_mapping.get(col, col) for col in df.columns]

    if ncols:
        df = df.iloc[:, :ncols]
    if nrows:
        df = df.head(nrows)

    metadata = {
        "encoding": used_encoding,
        "rows": len(df),
        "columns": df.shape[1],
        "duplicate_header_rows_removed": int(duplicate_count),
        "filename": os.path.basename(path)
    }

    return df, metadata

def read_csv_preview(path, num_rows=30):
    """
    简化接口：读取 CSV 文件前 num_rows 行，返回字段列表和部分数据
    """
    df, meta = read_csv_clean(path, nrows=num_rows)
    return {
        "columns": list(df.columns),
        "preview": df.to_dict(orient="records"),
        "metadata": meta
    }