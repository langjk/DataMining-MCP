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
    print(f"🔧 [DEBUG] dispatch_gpt_response 收到GPT回复: {gpt_reply[:200]}...")
    
    try:
        data = json.loads(gpt_reply)
        if not isinstance(data, dict) or "tool" not in data:
            print("🔧 [DEBUG] GPT返回格式错误")
            return {"type": "error", "content": "GPT 返回格式错误，缺少 tool 字段。"}

        tool = data["tool"]
        args = data.get("args", {})
        
        print(f"🔧 [DEBUG] 调用工具: {tool}")
        print(f"🔧 [DEBUG] 工具参数: {args}")

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

        elif tool == "multi_batch_analysis":
            analyzer = DataAnalyzer()
            batch_paths = args.get("batch_paths", [])
            batch_names = args.get("batch_names", [])
            analysis_type = args.get("analysis_type", "stability_trend")  # stability_trend, outlier_detection, comprehensive
            columns = args.get("columns")
            time_column = args.get("time_column")
            
            if not batch_paths or len(batch_paths) < 2:
                return {"type": "error", "content": "multi_batch_analysis 工具需要至少2个批次路径"}
            
            try:
                # 读取所有批次数据
                batch_data = []
                batch_metadata = []
                
                for i, path in enumerate(batch_paths):
                    df, meta = read_csv_clean(path)
                    batch_name = batch_names[i] if i < len(batch_names) else f"批次{i+1}"
                    batch_data.append((df, batch_name))
                    batch_metadata.append({
                        "filename": meta.get("filename", ""),
                        "rows": meta.get("rows", 0),
                        "batch_name": batch_name
                    })
                
                # 执行多批次分析
                if analysis_type == "stability_trend":
                    # 分析所有批次的稳定性变化趋势（使用全面对比分析）
                    result = _analyze_multi_batch_comprehensive_comparison(analyzer, batch_data, columns)
                elif analysis_type == "outlier_detection":
                    # 找出异常批次
                    result = _analyze_multi_batch_outliers(analyzer, batch_data, columns)
                elif analysis_type == "comprehensive":
                    # 全面分析所有批次（包括所有统计指标对比）
                    result = _analyze_multi_batch_comprehensive_comparison(analyzer, batch_data, columns)
                else:
                    return {"type": "error", "content": f"未识别的多批次分析类型：{analysis_type}"}
                
                return {
                    "type": "tool_result",
                    "tool": "multi_batch_analysis",
                    "data": {
                        "analysis_type": analysis_type,
                        "batch_metadata": batch_metadata,
                        "analysis_results": result,
                        "total_batches": len(batch_paths)
                    }
                }
            except Exception as e:
                return {"type": "error", "content": f"多批次分析失败：{str(e)}"}

        elif tool == "time_series_analysis":
            print("🔧 [DEBUG] 开始时间序列分析")
            analyzer = DataAnalyzer()
            file_path = args.get("file_path")
            columns = args.get("columns")
            time_column = args.get("time_column")
            
            print(f"🔧 [DEBUG] 文件路径: {file_path}")
            print(f"🔧 [DEBUG] 指定列: {columns}")
            print(f"🔧 [DEBUG] 时间列: {time_column}")
            
            if not file_path:
                return {"type": "error", "content": "time_series_analysis 工具需要 file_path 参数"}
            
            try:
                # 读取数据
                print(f"🔧 [DEBUG] 正在读取文件: {file_path}")
                df, meta = read_csv_clean(file_path)
                print(f"🔧 [DEBUG] 数据读取成功，形状: {df.shape}")
                
                # 时间序列分析
                print("🔧 [DEBUG] 开始执行时间序列分析")
                result = _analyze_time_series(analyzer, df, columns, time_column)
                print(f"🔧 [DEBUG] 时间序列分析完成，分析结果数量: {len(result.get('series_analysis', {}))}")
                
                print("🔧 [DEBUG] 返回时间序列分析结果")
                return {
                    "type": "tool_result",
                    "tool": "time_series_analysis",
                    "data": {
                        "file_path": file_path,
                        "file_metadata": meta,
                        "analysis_results": result
                    }
                }
            except Exception as e:
                print(f"🔧 [DEBUG] 时间序列分析异常: {str(e)}")
                return {"type": "error", "content": f"时间序列分析失败：{str(e)}"}

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

def _analyze_multi_batch_comprehensive_comparison(analyzer, batch_data, columns):
    """全面的多批次对比分析（支持所有统计指标）"""
    import numpy as np
    
    batch_comprehensive_data = {}
    multi_metrics_trends = {}
    
    # 为每个批次进行全面分析
    for df, batch_name in batch_data:
        # 获取全面的分析结果
        comprehensive_result = analyzer.comprehensive_analysis(df, columns, None)
        
        # 提取各类指标
        basic_stats = comprehensive_result.get('basic_statistics', {})
        stability_analysis = comprehensive_result.get('stability_analysis', {})
        trend_analysis = comprehensive_result.get('trend_analysis', {})
        outlier_detection = comprehensive_result.get('outlier_detection', {})
        
        batch_comprehensive_data[batch_name] = {
            'basic_statistics': basic_stats,
            'stability_analysis': stability_analysis,
            'trend_analysis': trend_analysis,
            'outlier_detection': outlier_detection
        }
    
    # 获取要分析的列
    if columns:
        target_columns = [col for col in columns if col in batch_data[0][0].columns]
    else:
        target_columns = [col for col in batch_data[0][0].columns if batch_data[0][0][col].dtype in ['int64', 'float64']][:10]
    
    # 对每个指标进行多批次对比分析
    for column in target_columns:
        batch_names = []
        
        # 收集各类指标数据
        means = []
        stds = []
        mins = []
        maxs = []
        cvs = []
        stability_indices = []
        outlier_counts = []
        trend_correlations = []
        
        for df, batch_name in batch_data:
            batch_data_item = batch_comprehensive_data[batch_name]
            
            # 基础统计数据
            basic_stats = batch_data_item['basic_statistics']
            stability_data = batch_data_item['stability_analysis']
            trend_data = batch_data_item['trend_analysis']
            outlier_data = batch_data_item['outlier_detection']
            
            if column in basic_stats:
                batch_names.append(batch_name)
                means.append(basic_stats[column].get('mean', 0))
                stds.append(basic_stats[column].get('std', 0))
                mins.append(basic_stats[column].get('min', 0))
                maxs.append(basic_stats[column].get('max', 0))
                cvs.append(basic_stats[column].get('cv', 0))
                
                # 稳定性数据
                if column in stability_data:
                    stability_indices.append(stability_data[column].get('stability_index', 0))
                else:
                    stability_indices.append(0)
                
                # 异常检测数据
                if column in outlier_data:
                    outlier_counts.append(outlier_data[column].get('outlier_count', 0))
                else:
                    outlier_counts.append(0)
                
                # 趋势数据
                if column in trend_data and 'error' not in trend_data[column]:
                    trend_correlations.append(trend_data[column].get('correlation', 0))
                else:
                    trend_correlations.append(0)
        
        if len(batch_names) >= 2:
            # 计算各指标的趋势
            x = np.arange(len(batch_names))
            
            multi_metrics_trends[column] = {
                'batch_names': batch_names,
                'metrics': {
                    'mean': {
                        'values': [round(v, 4) for v in means],
                        'trend_slope': round(np.polyfit(x, means, 1)[0], 6) if len(means) > 1 else 0,
                        'trend_direction': _get_trend_direction(np.polyfit(x, means, 1)[0]) if len(means) > 1 else '稳定',
                        'change_percent': round(((means[-1] - means[0]) / means[0] * 100), 2) if means[0] != 0 else 0,
                        'range': round(max(means) - min(means), 4),
                        'best_batch': batch_names[np.argmax(means)] if means else '',
                        'worst_batch': batch_names[np.argmin(means)] if means else ''
                    },
                    'std': {
                        'values': [round(v, 4) for v in stds],
                        'trend_slope': round(np.polyfit(x, stds, 1)[0], 6) if len(stds) > 1 else 0,
                        'trend_direction': _get_trend_direction(np.polyfit(x, stds, 1)[0]) if len(stds) > 1 else '稳定',
                        'change_percent': round(((stds[-1] - stds[0]) / stds[0] * 100), 2) if stds[0] != 0 else 0,
                        'range': round(max(stds) - min(stds), 4),
                        'best_batch': batch_names[np.argmin(stds)] if stds else '',  # 标准差越小越好
                        'worst_batch': batch_names[np.argmax(stds)] if stds else ''
                    },
                    'cv': {
                        'values': [round(v, 4) for v in cvs],
                        'trend_slope': round(np.polyfit(x, cvs, 1)[0], 6) if len(cvs) > 1 else 0,
                        'trend_direction': _get_trend_direction(np.polyfit(x, cvs, 1)[0]) if len(cvs) > 1 else '稳定',
                        'change_percent': round(((cvs[-1] - cvs[0]) / cvs[0] * 100), 2) if cvs[0] != 0 else 0,
                        'range': round(max(cvs) - min(cvs), 4),
                        'best_batch': batch_names[np.argmin(cvs)] if cvs else '',  # 变异系数越小越好
                        'worst_batch': batch_names[np.argmax(cvs)] if cvs else ''
                    },
                    'min': {
                        'values': [round(v, 4) for v in mins],
                        'trend_slope': round(np.polyfit(x, mins, 1)[0], 6) if len(mins) > 1 else 0,
                        'trend_direction': _get_trend_direction(np.polyfit(x, mins, 1)[0]) if len(mins) > 1 else '稳定',
                        'change_percent': round(((mins[-1] - mins[0]) / mins[0] * 100), 2) if mins[0] != 0 else 0,
                        'range': round(max(mins) - min(mins), 4)
                    },
                    'max': {
                        'values': [round(v, 4) for v in maxs],
                        'trend_slope': round(np.polyfit(x, maxs, 1)[0], 6) if len(maxs) > 1 else 0,
                        'trend_direction': _get_trend_direction(np.polyfit(x, maxs, 1)[0]) if len(maxs) > 1 else '稳定',
                        'change_percent': round(((maxs[-1] - maxs[0]) / maxs[0] * 100), 2) if maxs[0] != 0 else 0,
                        'range': round(max(maxs) - min(maxs), 4)
                    },
                    'stability_index': {
                        'values': [round(v, 4) for v in stability_indices],
                        'trend_slope': round(np.polyfit(x, stability_indices, 1)[0], 6) if len(stability_indices) > 1 else 0,
                        'trend_direction': _get_trend_direction(np.polyfit(x, stability_indices, 1)[0]) if len(stability_indices) > 1 else '稳定',
                        'change_percent': round(((stability_indices[-1] - stability_indices[0]) / stability_indices[0] * 100), 2) if stability_indices[0] != 0 else 0,
                        'range': round(max(stability_indices) - min(stability_indices), 4),
                        'best_batch': batch_names[np.argmax(stability_indices)] if stability_indices else '',
                        'worst_batch': batch_names[np.argmin(stability_indices)] if stability_indices else ''
                    },
                    'outlier_count': {
                        'values': outlier_counts,
                        'trend_slope': round(np.polyfit(x, outlier_counts, 1)[0], 6) if len(outlier_counts) > 1 else 0,
                        'trend_direction': _get_trend_direction(np.polyfit(x, outlier_counts, 1)[0]) if len(outlier_counts) > 1 else '稳定',
                        'change_percent': round(((outlier_counts[-1] - outlier_counts[0]) / outlier_counts[0] * 100), 2) if outlier_counts[0] != 0 else 0,
                        'range': max(outlier_counts) - min(outlier_counts) if outlier_counts else 0,
                        'best_batch': batch_names[np.argmin(outlier_counts)] if outlier_counts else '',  # 异常值越少越好
                        'worst_batch': batch_names[np.argmax(outlier_counts)] if outlier_counts else ''
                    }
                }
            }
    
    return {
        'analysis_type': 'multi_batch_comprehensive',
        'batch_comprehensive_data': batch_comprehensive_data,
        'multi_metrics_trends': multi_metrics_trends,
        'summary': {
            'total_batches': len(batch_data),
            'analyzed_metrics': len(multi_metrics_trends),
            'available_metric_types': ['mean', 'std', 'cv', 'min', 'max', 'stability_index', 'outlier_count']
        }
    }

def _get_trend_direction(slope):
    """根据斜率判断趋势方向"""
    if slope > 0.001:
        return '上升'
    elif slope < -0.001:
        return '下降'
    else:
        return '稳定'

def _analyze_multi_batch_outliers(analyzer, batch_data, columns):
    """找出异常批次"""
    import numpy as np
    from scipy import stats
    
    batch_stats = {}
    outlier_analysis = {}
    
    # 计算每个批次的基础统计信息
    for df, batch_name in batch_data:
        stats_result = analyzer.basic_statistics(df, columns)
        batch_stats[batch_name] = stats_result
    
    # 分析哪些批次是异常的
    if columns:
        target_columns = [col for col in columns if col in batch_data[0][0].columns]
    else:
        target_columns = [col for col in batch_data[0][0].columns if batch_data[0][0][col].dtype in ['int64', 'float64']][:10]
    
    batch_outlier_scores = {batch_name: 0 for _, batch_name in batch_data}
    
    for column in target_columns:
        means = []
        stds = []
        batch_names = []
        
        for df, batch_name in batch_data:
            if column in batch_stats[batch_name]:
                mean_val = batch_stats[batch_name][column].get('mean', 0)
                std_val = batch_stats[batch_name][column].get('std', 0)
                means.append(mean_val)
                stds.append(std_val)
                batch_names.append(batch_name)
        
        if len(means) >= 3:
            # 计算Z-score来识别异常批次
            mean_z_scores = np.abs(stats.zscore(means)) if len(means) > 2 else [0] * len(means)
            std_z_scores = np.abs(stats.zscore(stds)) if len(stds) > 2 else [0] * len(stds)
            
            for i, batch_name in enumerate(batch_names):
                # 综合评分：均值偏离 + 稳定性偏离
                outlier_score = mean_z_scores[i] + std_z_scores[i]
                batch_outlier_scores[batch_name] += outlier_score
            
            outlier_analysis[column] = {
                'batch_means': dict(zip(batch_names, means)),
                'batch_stds': dict(zip(batch_names, stds)),
                'mean_z_scores': dict(zip(batch_names, mean_z_scores)),
                'std_z_scores': dict(zip(batch_names, std_z_scores))
            }
    
    # 排序找出最异常的批次
    sorted_batches = sorted(batch_outlier_scores.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'analysis_type': 'multi_batch_outlier_detection',
        'batch_outlier_scores': batch_outlier_scores,
        'outlier_details': outlier_analysis,
        'ranked_batches': sorted_batches,
        'most_abnormal_batches': sorted_batches[:3],  # 前3个最异常的批次
        'summary': {
            'total_batches': len(batch_data),
            'analyzed_metrics': len(outlier_analysis),
            'most_abnormal': sorted_batches[0][0] if sorted_batches else None,
            'most_normal': sorted_batches[-1][0] if sorted_batches else None
        }
    }

def _analyze_multi_batch_comprehensive(analyzer, batch_data, columns, time_column):
    """综合分析所有批次"""
    comprehensive_results = {}
    
    # 对每个批次进行综合分析
    for df, batch_name in batch_data:
        result = analyzer.comprehensive_analysis(df, columns, time_column)
        comprehensive_results[batch_name] = _simplify_comprehensive_analysis(result)
    
    # 生成批次间对比摘要
    comparison_summary = _generate_multi_batch_summary(comprehensive_results)
    
    return {
        'analysis_type': 'multi_batch_comprehensive',
        'batch_results': comprehensive_results,
        'comparison_summary': comparison_summary,
        'total_batches': len(batch_data)
    }

def _analyze_time_series(analyzer, df, columns, time_column):
    """时间序列分析，用于单批次变化曲线"""
    import numpy as np
    import pandas as pd
    
    print(f"🔧 [DEBUG] _analyze_time_series 开始")
    print(f"🔧 [DEBUG] 输入参数 - columns: {columns}, time_column: {time_column}")
    print(f"🔧 [DEBUG] 数据形状: {df.shape}, 列名: {list(df.columns)}")
    
    if not time_column or time_column not in df.columns:
        # 如果没有时间列，使用索引作为时间
        print("🔧 [DEBUG] 没有时间列，创建time_index")
        df = df.copy()
        df['time_index'] = range(len(df))
        time_column = 'time_index'
        print(f"🔧 [DEBUG] 时间列设为: {time_column}")
    
    # 选择要分析的列
    if columns:
        # 用户指定的列，尝试转换为数值型
        target_columns = []
        for col in columns:
            if col in df.columns and col != time_column:
                try:
                    # 尝试转换为数值型
                    pd.to_numeric(df[col], errors='coerce')
                    target_columns.append(col)
                except:
                    continue
    else:
        # 自动选择数值型列，排除时间列
        target_columns = []
        for col in df.columns:
            if col != time_column:
                if df[col].dtype in ['int64', 'float64', 'float32', 'int32']:
                    target_columns.append(col)
                else:
                    # 尝试转换object类型的列
                    try:
                        numeric_series = pd.to_numeric(df[col], errors='coerce')
                        if not numeric_series.isna().all():  # 如果不是全部为NaN
                            target_columns.append(col)
                    except:
                        continue
        target_columns = target_columns[:10]
    
    print(f"🔧 [DEBUG] 最终目标列: {target_columns}")
    
    time_series_analysis = {}
    
    for column in target_columns:
        print(f"🔧 [DEBUG] 处理列: {column}")
        if column != time_column:
            # 尝试转换为数值型并去除NaN
            try:
                numeric_values = pd.to_numeric(df[column], errors='coerce')
                # 创建一个临时DataFrame确保索引对应
                temp_df = pd.DataFrame({
                    'values': numeric_values,
                    'time': df[time_column]
                }).dropna()
                values = temp_df['values']
                time_values = temp_df['time']
            except:
                # 使用原始数据
                temp_df = pd.DataFrame({
                    'values': df[column],
                    'time': df[time_column]
                }).dropna()
                values = temp_df['values']
                time_values = temp_df['time']
            
            if len(values) >= 2:
                print(f"🔧 [DEBUG] 列 {column} 有 {len(values)} 个有效数据点")
                # 计算基本统计
                mean_val = values.mean()
                std_val = values.std()
                
                # 计算变化率
                changes = values.diff().dropna()
                max_change = changes.abs().max() if len(changes) > 0 else 0
                
                # 趋势分析
                x = np.arange(len(values))
                if len(values) > 1:
                    slope = np.polyfit(x, values, 1)[0]
                    correlation = np.corrcoef(x, values)[0, 1] if len(values) > 2 else 0
                else:
                    slope = 0
                    correlation = 0
                
                time_series_analysis[column] = {
                    'values': values.tolist()[:100],  # 限制数据点数量
                    'time_points': time_values.tolist()[:100],
                    'mean': round(mean_val, 4),
                    'std': round(std_val, 4),
                    'max_change': round(max_change, 4),
                    'trend_slope': round(slope, 6),
                    'correlation': round(correlation, 4),
                    'trend_direction': '上升' if slope > 0.001 else ('下降' if slope < -0.001 else '稳定'),
                    'data_points': len(values)
                }
    
    return {
        'analysis_type': 'time_series',
        'time_column': time_column,
        'series_analysis': time_series_analysis,
        'total_data_points': len(df),
        'debug_info': {
            'target_columns': target_columns,
            'df_columns': list(df.columns),
            'df_dtypes': dict(df.dtypes.astype(str)),
            'analysis_count': len(time_series_analysis),
            'df_shape': df.shape,
            'specified_columns': columns
        }
    }

def _generate_multi_batch_summary(comprehensive_results):
    """生成多批次对比摘要"""
    import numpy as np
    
    batch_names = list(comprehensive_results.keys())
    
    # 统计各批次的关键指标
    summary = {
        'best_stability_batch': None,
        'worst_stability_batch': None,
        'most_outliers_batch': None,
        'least_outliers_batch': None,
        'batch_rankings': {}
    }
    
    # 简单的排名逻辑（可以根据需要扩展）
    stability_scores = {}
    outlier_counts = {}
    
    for batch_name, result in comprehensive_results.items():
        # 计算稳定性综合评分
        stability_data = result.get('key_metrics_stability', {})
        if stability_data:
            avg_stability = np.mean([data.get('stability_index', 0) for data in stability_data.values()])
            stability_scores[batch_name] = avg_stability
        
        # 计算异常值总数
        outlier_data = result.get('outlier_summary', {})
        outlier_counts[batch_name] = outlier_data.get('total_outliers', 0)
    
    if stability_scores:
        summary['best_stability_batch'] = max(stability_scores, key=stability_scores.get)
        summary['worst_stability_batch'] = min(stability_scores, key=stability_scores.get)
    
    if outlier_counts:
        summary['most_outliers_batch'] = max(outlier_counts, key=outlier_counts.get)
        summary['least_outliers_batch'] = min(outlier_counts, key=outlier_counts.get)
    
    return summary
