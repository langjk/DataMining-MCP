# gpt_dispatcher.py
# 工具调用响应调度器，仅负责解析 GPT 指令并执行对应工具

import json
from scan import scan_directory
from csv_reader import read_csv_clean
from cache_utils import save_cache, load_cache
from data_analyzer import DataAnalyzer

def dispatch_gpt_response(gpt_reply: str):
    """
    解析 GPT 返回的 JSON 指令，并调用相应工具。
    返回统一结构：{"type": "tool_result" / "noop" / "error", "data": object}
    """
    try:
        data = json.loads(gpt_reply)
        if not isinstance(data, dict) or "tool" not in data:
            return {"type": "error", "content": "GPT 返回格式错误，缺少 tool 字段。"}

        tool = data["tool"]
        args = data.get("args", {})

        if tool == "scan":
            result = scan_directory(args.get("path", "./data"))
            return {
                "type": "tool_result",
                "tool": "scan",
                "data": result
            }

        elif tool == "csv_reader":
            df, meta = read_csv_clean(
                path=args["path"],
                nrows=args.get("num_rows"),
                remove_header_repeats=True
            )
            return {
                "type": "tool_result",
                "tool": "csv_reader",
                "data": {
                    "fields": df.columns.tolist(),
                    "preview": df.head().to_dict(orient="records"),
                    "metadata": meta
                }
            }

        elif tool == "cache":
            mode = args.get("mode")
            key = args.get("key")
            if mode == "write":
                content = args.get("content", {})
                save_cache(key, content)
                return {
                    "type": "tool_result",
                    "tool": "cache",
                    "data": {"status": "saved", "key": key}
                }
            elif mode == "read":
                content = load_cache(key)
                return {
                    "type": "tool_result",
                    "tool": "cache",
                    "data": {"status": "loaded", "key": key, "content": content}
                }
            else:
                return {"type": "error", "content": f"无效缓存模式：{mode}"}

        elif tool == "data_analysis":
            analyzer = DataAnalyzer()
            analysis_type = args.get("analysis_type", "comprehensive")
            file_path = args.get("file_path")
            columns = args.get("columns")
            time_column = args.get("time_column")
            
            if not file_path:
                return {"type": "error", "content": "data_analysis 工具需要 file_path 参数"}
            
            try:
                # 读取数据
                df, meta = read_csv_clean(file_path)
                
                # 根据分析类型调用相应方法
                if analysis_type == "comprehensive":
                    result = analyzer.comprehensive_analysis(df, columns, time_column)
                    # 精简综合分析结果
                    simplified_result = _simplify_comprehensive_analysis(result)
                elif analysis_type == "statistics":
                    result = analyzer.basic_statistics(df, columns)
                    simplified_result = _simplify_statistics(result)
                elif analysis_type == "stability":
                    result = analyzer.stability_analysis(df, columns)
                    simplified_result = _simplify_stability_analysis(result)
                elif analysis_type == "trend":
                    result = analyzer.trend_analysis(df, columns, time_column)
                    simplified_result = _simplify_trend_analysis(result)
                elif analysis_type == "outlier":
                    result = analyzer.outlier_detection(df, columns)
                    simplified_result = _simplify_outlier_detection(result)
                else:
                    return {"type": "error", "content": f"未识别的分析类型：{analysis_type}"}
                
                return {
                    "type": "tool_result",
                    "tool": "data_analysis",
                    "data": {
                        "analysis_type": analysis_type,
                        "file_path": file_path,
                        "file_metadata": meta,
                        "analysis_results": simplified_result
                    }
                }
            except Exception as e:
                return {"type": "error", "content": f"数据分析失败：{str(e)}"}

        elif tool == "batch_comparison":
            analyzer = DataAnalyzer()
            batch1_path = args.get("batch1_path")
            batch2_path = args.get("batch2_path")
            batch1_name = args.get("batch1_name", "批次1")
            batch2_name = args.get("batch2_name", "批次2")
            columns = args.get("columns")
            
            if not batch1_path or not batch2_path:
                return {"type": "error", "content": "batch_comparison 工具需要 batch1_path 和 batch2_path 参数"}
            
            try:
                # 读取两个批次的数据
                df1, meta1 = read_csv_clean(batch1_path)
                df2, meta2 = read_csv_clean(batch2_path)
                
                # 执行批次对比分析
                result = analyzer.batch_comparison(df1, df2, columns, batch1_name, batch2_name)
                
                # 精简批次对比结果用于GPT处理
                simplified_result = _simplify_batch_comparison(result)
                
                return {
                    "type": "tool_result",
                    "tool": "batch_comparison",
                    "data": {
                        "batch1_metadata": {"filename": meta1.get("filename", ""), "rows": meta1.get("rows", 0)},
                        "batch2_metadata": {"filename": meta2.get("filename", ""), "rows": meta2.get("rows", 0)},
                        "analysis_results": result,  # 完整结果用于右侧面板显示
                        "comparison_results": simplified_result  # 精简结果用于GPT分析
                    }
                }
            except Exception as e:
                return {"type": "error", "content": f"批次对比分析失败：{str(e)}"}

        elif tool == "noop":
            return {"type": "noop", "content": data.get("reply", "")}

        return {"type": "error", "content": f"未识别的工具类型：{tool}"}

    except Exception as e:
        return {"type": "error", "content": f"工具调用异常：{str(e)}"}

def _simplify_comprehensive_analysis(result):
    """精简综合分析结果，保留关键信息"""
    simplified = {
        "data_quality": result.get("data_quality", {}),
        "summary": result.get("summary", {}),
        "key_metrics_statistics": {},
        "key_metrics_stability": {},
        "key_metrics_trends": {},
        "outlier_summary": {}
    }
    
    # 选择前5个关键指标的统计信息
    stats = result.get("basic_statistics", {})
    count = 0
    for metric, data in stats.items():
        if count >= 5:
            break
        simplified["key_metrics_statistics"][metric] = {
            "mean": round(data.get("mean", 0), 4),
            "std": round(data.get("std", 0), 4),
            "cv": round(data.get("cv", 0), 4),
            "range": [data.get("min", 0), data.get("max", 0)]
        }
        count += 1
    
    # 选择前5个关键指标的稳定性信息
    stability = result.get("stability_analysis", {})
    count = 0
    for metric, data in stability.items():
        if count >= 5:
            break
        simplified["key_metrics_stability"][metric] = {
            "stability_rating": data.get("stability_rating", ""),
            "stability_index": round(data.get("stability_index", 0), 4),
            "max_change_rate": round(data.get("max_change_rate", 0), 4)
        }
        count += 1
    
    # 选择前5个关键指标的趋势信息
    trends = result.get("trend_analysis", {})
    count = 0
    for metric, data in trends.items():
        if count >= 5:
            break
        if "error" not in data:
            simplified["key_metrics_trends"][metric] = {
                "trend_direction": data.get("trend_direction", ""),
                "trend_strength": data.get("trend_strength", ""),
                "is_significant": data.get("is_significant", False),
                "relative_change": round(data.get("relative_change", 0), 2)
            }
        count += 1
    
    # 异常检测总结
    outliers = result.get("outlier_detection", {})
    total_outliers = 0
    outlier_metrics = []
    for metric, data in outliers.items():
        outlier_count = data.get("outlier_count", 0)
        if outlier_count > 0:
            total_outliers += outlier_count
            outlier_metrics.append({
                "metric": metric,
                "count": outlier_count,
                "percentage": round(data.get("outlier_percentage", 0), 2)
            })
    
    simplified["outlier_summary"] = {
        "total_outliers": total_outliers,
        "affected_metrics": len(outlier_metrics),
        "top_outlier_metrics": outlier_metrics[:3]  # 只显示前3个
    }
    
    return simplified

def _simplify_statistics(result):
    """精简统计分析结果"""
    simplified = {}
    for metric, data in result.items():
        simplified[metric] = {
            "mean": round(data.get("mean", 0), 4),
            "std": round(data.get("std", 0), 4),
            "cv": round(data.get("cv", 0), 4),
            "range": [data.get("min", 0), data.get("max", 0)]
        }
    return simplified

def _simplify_stability_analysis(result):
    """精简稳定性分析结果"""
    simplified = {}
    for metric, data in result.items():
        simplified[metric] = {
            "stability_rating": data.get("stability_rating", ""),
            "stability_index": round(data.get("stability_index", 0), 4),
            "max_change_rate": round(data.get("max_change_rate", 0), 4)
        }
    return simplified

def _simplify_trend_analysis(result):
    """精简趋势分析结果"""
    simplified = {}
    for metric, data in result.items():
        if "error" not in data:
            simplified[metric] = {
                "trend_direction": data.get("trend_direction", ""),
                "trend_strength": data.get("trend_strength", ""),
                "is_significant": data.get("is_significant", False),
                "correlation": round(data.get("correlation", 0), 4),
                "relative_change": round(data.get("relative_change", 0), 2)
            }
        else:
            simplified[metric] = {"error": data.get("error", "")}
    return simplified

def _simplify_outlier_detection(result):
    """精简异常检测结果"""
    simplified = {}
    for metric, data in result.items():
        simplified[metric] = {
            "outlier_count": data.get("outlier_count", 0),
            "outlier_percentage": round(data.get("outlier_percentage", 0), 2),
            "has_outliers": data.get("outlier_count", 0) > 0
        }
    return simplified

def _simplify_batch_comparison(result):
    """精简批次对比结果"""
    simplified = {
        "batch1_name": result.get("batch1_name", ""),
        "batch2_name": result.get("batch2_name", ""),
        "comparison_summary": {},
        "key_differences": []
    }
    
    comparison = result.get("comparison", {})
    
    # 统计改进情况
    improvement_counts = {"显著改善": 0, "稳定性改善": 0, "数值改善": 0, "需要关注": 0}
    significant_diffs = 0
    key_metrics = []
    
    for metric, data in comparison.items():
        improvement = data.get("improvement", "")
        if improvement in improvement_counts:
            improvement_counts[improvement] += 1
        
        if data.get("significant_difference", False):
            significant_diffs += 1
        
        # 保存关键差异（前5个指标）
        if len(key_metrics) < 5:
            key_metrics.append({
                "metric": metric,
                "mean_change_percent": round(data.get("mean_change_percent", 0), 2),
                "stability_comparison": data.get("stability_comparison", ""),
                "improvement": improvement,
                "significant": data.get("significant_difference", False)
            })
    
    simplified["comparison_summary"] = {
        "total_metrics": len(comparison),
        "significant_differences": significant_diffs,
        "improvement_distribution": improvement_counts
    }
    
    simplified["key_differences"] = key_metrics
    
    return simplified
