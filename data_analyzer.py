# data_analyzer.py
# 数据分析模块：统计分析、趋势检测、异常识别、批次对比
# 专门用于处理测试数据的分析任务

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import linregress
import warnings
warnings.filterwarnings('ignore')

class DataAnalyzer:
    """
    数据分析器，提供多种分析功能
    """
    
    def __init__(self):
        pass
    
    def basic_statistics(self, data, columns=None):
        """
        基础统计分析
        
        参数:
            data (DataFrame): 输入数据
            columns (list): 要分析的列名，None则分析所有数值列
            
        返回:
            dict: 统计结果
        """
        if columns is None:
            # 自动选择数值列，排除无名列和完全缺失的列
            numeric_cols = []
            for col in data.columns:
                # 跳过无名列
                if col.startswith('Unnamed:'):
                    continue
                # 检查是否为数值列且有有效数据
                try:
                    series = pd.to_numeric(data[col], errors='coerce').dropna()
                    if len(series) > 0:
                        numeric_cols.append(col)
                except:
                    continue
        else:
            numeric_cols = columns
        
        results = {}
        for col in numeric_cols:
            if col in data.columns:
                series = pd.to_numeric(data[col], errors='coerce').dropna()
                if len(series) > 0:
                    results[col] = {
                        "count": len(series),
                        "mean": float(series.mean()),
                        "std": float(series.std()),
                        "min": float(series.min()),
                        "max": float(series.max()),
                        "median": float(series.median()),
                        "cv": float(series.std() / series.mean()) if series.mean() != 0 else 0,  # 变异系数
                        "q25": float(series.quantile(0.25)),
                        "q75": float(series.quantile(0.75))
                    }
        
        return results
    
    def stability_analysis(self, data, columns=None, window_size=10):
        """
        稳定性分析
        
        参数:
            data (DataFrame): 输入数据
            columns (list): 要分析的列名
            window_size (int): 滚动窗口大小
            
        返回:
            dict: 稳定性指标
        """
        if columns is None:
            # 自动选择数值列，排除无名列和完全缺失的列
            numeric_cols = []
            for col in data.columns:
                if col.startswith('Unnamed:'):
                    continue
                try:
                    series = pd.to_numeric(data[col], errors='coerce').dropna()
                    if len(series) > 0:
                        numeric_cols.append(col)
                except:
                    continue
        else:
            numeric_cols = columns
        
        results = {}
        for col in numeric_cols:
            if col in data.columns:
                series = pd.to_numeric(data[col], errors='coerce').dropna()
                if len(series) > window_size:
                    # 滚动标准差
                    rolling_std = series.rolling(window=window_size).std()
                    
                    # 稳定性指标
                    stability_index = 1 / (1 + rolling_std.mean()) if rolling_std.mean() > 0 else 1
                    
                    # 变化率分析
                    pct_change = series.pct_change().dropna()
                    
                    results[col] = {
                        "stability_index": float(stability_index),
                        "rolling_std_mean": float(rolling_std.mean()),
                        "rolling_std_max": float(rolling_std.max()),
                        "max_change_rate": float(abs(pct_change).max()) if len(pct_change) > 0 else 0,
                        "avg_change_rate": float(abs(pct_change).mean()) if len(pct_change) > 0 else 0,
                        "stable_periods": int(sum(rolling_std < rolling_std.mean())),  # 稳定周期数
                        "stability_rating": self._get_stability_rating(stability_index)
                    }
        
        return results
    
    def trend_analysis(self, data, columns=None, time_col=None):
        """
        趋势分析
        
        参数:
            data (DataFrame): 输入数据
            columns (list): 要分析的列名
            time_col (str): 时间列名，如果为None则使用索引
            
        返回:
            dict: 趋势分析结果
        """
        if columns is None:
            # 自动选择数值列，排除无名列和完全缺失的列
            numeric_cols = []
            for col in data.columns:
                if col.startswith('Unnamed:'):
                    continue
                try:
                    series = pd.to_numeric(data[col], errors='coerce').dropna()
                    if len(series) > 0:
                        numeric_cols.append(col)
                except:
                    continue
        else:
            numeric_cols = columns
        
        results = {}
        
        # 准备时间序列
        if time_col and time_col in data.columns:
            try:
                time_series = pd.to_datetime(data[time_col])
                x_values = np.arange(len(time_series))
            except:
                x_values = np.arange(len(data))
        else:
            x_values = np.arange(len(data))
        
        for col in numeric_cols:
            if col in data.columns and col != time_col:
                series = pd.to_numeric(data[col], errors='coerce').dropna()
                if len(series) > 2:
                    # 对齐x和y的长度
                    min_len = min(len(x_values), len(series))
                    x = x_values[:min_len]
                    y = series.iloc[:min_len]
                    
                    # 线性回归分析
                    try:
                        slope, intercept, r_value, p_value, std_err = linregress(x, y)
                        
                        # 趋势判断
                        trend_direction = "上升" if slope > 0 else "下降" if slope < 0 else "平稳"
                        trend_strength = "强" if abs(r_value) > 0.7 else "中等" if abs(r_value) > 0.3 else "弱"
                        
                        results[col] = {
                            "slope": float(slope),
                            "intercept": float(intercept),
                            "r_squared": float(r_value ** 2),
                            "correlation": float(r_value),
                            "p_value": float(p_value),
                            "trend_direction": trend_direction,
                            "trend_strength": trend_strength,
                            "is_significant": bool(p_value < 0.05),
                            "relative_change": float((series.iloc[-1] - series.iloc[0]) / series.iloc[0] * 100) if series.iloc[0] != 0 else 0
                        }
                    except Exception as e:
                        results[col] = {"error": f"趋势分析失败: {str(e)}"}
        
        return results
    
    def outlier_detection(self, data, columns=None, method='iqr', threshold=1.5):
        """
        异常值检测
        
        参数:
            data (DataFrame): 输入数据
            columns (list): 要分析的列名
            method (str): 检测方法 'iqr' 或 'zscore'
            threshold (float): 阈值
            
        返回:
            dict: 异常检测结果
        """
        if columns is None:
            # 自动选择数值列，排除无名列和完全缺失的列
            numeric_cols = []
            for col in data.columns:
                if col.startswith('Unnamed:'):
                    continue
                try:
                    series = pd.to_numeric(data[col], errors='coerce').dropna()
                    if len(series) > 0:
                        numeric_cols.append(col)
                except:
                    continue
        else:
            numeric_cols = columns
        
        results = {}
        
        for col in numeric_cols:
            if col in data.columns:
                series = pd.to_numeric(data[col], errors='coerce').dropna()
                if len(series) > 0:
                    outliers = []
                    outlier_indices = []
                    
                    if method == 'iqr':
                        Q1 = series.quantile(0.25)
                        Q3 = series.quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - threshold * IQR
                        upper_bound = Q3 + threshold * IQR
                        
                        outlier_mask = (series < lower_bound) | (series > upper_bound)
                        outliers = series[outlier_mask].tolist()
                        outlier_indices = series[outlier_mask].index.tolist()
                        
                    elif method == 'zscore':
                        z_scores = np.abs(stats.zscore(series))
                        outlier_mask = z_scores > threshold
                        outliers = series[outlier_mask].tolist()
                        outlier_indices = series[outlier_mask].index.tolist()
                    
                    results[col] = {
                        "outlier_count": len(outliers),
                        "outlier_percentage": float(len(outliers) / len(series) * 100),
                        "outlier_values": [float(x) for x in outliers[:10]],  # 最多显示10个
                        "outlier_indices": [int(x) for x in outlier_indices[:10]],
                        "method": method,
                        "threshold": threshold
                    }
        
        return results
    
    def batch_comparison(self, data1, data2, columns=None, batch1_name="批次1", batch2_name="批次2"):
        """
        批次间对比分析
        
        参数:
            data1, data2 (DataFrame): 两个批次的数据
            columns (list): 要对比的列名
            batch1_name, batch2_name (str): 批次名称
            
        返回:
            dict: 对比分析结果
        """
        if columns is None:
            numeric_cols1 = data1.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols2 = data2.select_dtypes(include=[np.number]).columns.tolist()
            columns = list(set(numeric_cols1) & set(numeric_cols2))  # 取交集
        
        results = {
            "batch1_name": batch1_name,
            "batch2_name": batch2_name,
            "comparison": {}
        }
        
        for col in columns:
            if col in data1.columns and col in data2.columns:
                series1 = pd.to_numeric(data1[col], errors='coerce').dropna()
                series2 = pd.to_numeric(data2[col], errors='coerce').dropna()
                
                if len(series1) > 0 and len(series2) > 0:
                    # 基础统计对比
                    mean1, mean2 = series1.mean(), series2.mean()
                    std1, std2 = series1.std(), series2.std()
                    
                    # T检验
                    try:
                        t_stat, t_p_value = stats.ttest_ind(series1, series2)
                        significant_diff = bool(t_p_value < 0.05)  # 确保为Python bool
                    except:
                        t_stat, t_p_value, significant_diff = float(0), float(1), False
                    
                    # 变异系数对比
                    cv1 = std1 / mean1 if mean1 != 0 else 0
                    cv2 = std2 / mean2 if mean2 != 0 else 0
                    
                    results["comparison"][col] = {
                        "batch1_mean": float(mean1),
                        "batch2_mean": float(mean2),
                        "mean_difference": float(mean2 - mean1),
                        "mean_change_percent": float((mean2 - mean1) / mean1 * 100) if mean1 != 0 else 0,
                        "batch1_std": float(std1),
                        "batch2_std": float(std2),
                        "batch1_cv": float(cv1),
                        "batch2_cv": float(cv2),
                        "stability_comparison": "更稳定" if cv2 < cv1 else "不如" if cv2 > cv1 else "相似",
                        "t_statistic": float(t_stat),
                        "t_p_value": float(t_p_value),
                        "significant_difference": significant_diff,
                        "improvement": self._assess_improvement(mean1, mean2, cv1, cv2, col)
                    }
        
        return results
    
    def comprehensive_analysis(self, data, columns=None, time_col=None):
        """
        综合分析：整合所有分析功能
        
        参数:
            data (DataFrame): 输入数据
            columns (list): 要分析的列名
            time_col (str): 时间列名
            
        返回:
            dict: 综合分析结果
        """
        results = {
            "basic_statistics": self.basic_statistics(data, columns),
            "stability_analysis": self.stability_analysis(data, columns),
            "trend_analysis": self.trend_analysis(data, columns, time_col),
            "outlier_detection": self.outlier_detection(data, columns),
            "data_quality": self._assess_data_quality(data, columns),
            "summary": self._generate_summary(data, columns)
        }
        
        return results
    
    def _get_stability_rating(self, stability_index):
        """获取稳定性评级"""
        if stability_index >= 0.9:
            return "极稳定"
        elif stability_index >= 0.7:
            return "稳定"
        elif stability_index >= 0.5:
            return "一般"
        else:
            return "不稳定"
    
    def _assess_improvement(self, mean1, mean2, cv1, cv2, col):
        """评估改进情况"""
        # 根据指标类型判断改进方向
        if "效率" in col or "Eff" in col:
            # 效率类指标：数值越高越好，变异系数越小越好
            mean_better = mean2 > mean1
            stability_better = cv2 < cv1
        else:
            # 其他指标：主要看稳定性
            mean_better = abs(mean2 - mean1) / max(abs(mean1), 1e-6) < 0.05  # 变化小于5%
            stability_better = cv2 < cv1
        
        if mean_better and stability_better:
            return "显著改善"
        elif stability_better:
            return "稳定性改善"
        elif mean_better:
            return "数值改善"
        else:
            return "需要关注"
    
    def _assess_data_quality(self, data, columns):
        """评估数据质量"""
        if columns is None:
            # 使用相同的逻辑选择有效的数值列
            columns = []
            for col in data.columns:
                if col.startswith('Unnamed:'):
                    continue
                try:
                    series = pd.to_numeric(data[col], errors='coerce').dropna()
                    if len(series) > 0:
                        columns.append(col)
                except:
                    continue
        
        total_points = len(data)
        missing_counts = {}
        completeness_rates = {}
        
        for col in columns:
            if col in data.columns and not col.startswith('Unnamed:'):
                missing = data[col].isna().sum()
                missing_counts[col] = int(missing)
                completeness_rates[col] = float((total_points - missing) / total_points * 100)
        
        avg_completeness = np.mean(list(completeness_rates.values())) if completeness_rates else 0
        
        return {
            "total_records": total_points,
            "missing_counts": missing_counts,
            "completeness_rates": completeness_rates,
            "average_completeness": float(avg_completeness),
            "quality_rating": "优秀" if avg_completeness >= 95 else "良好" if avg_completeness >= 85 else "一般" if avg_completeness >= 70 else "较差"
        }
    
    def _generate_summary(self, data, columns):
        """生成分析摘要"""
        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        stats = self.basic_statistics(data, columns)
        stability = self.stability_analysis(data, columns)
        trends = self.trend_analysis(data, columns)
        
        summary = {
            "analyzed_columns": len(columns),
            "total_records": len(data),
            "key_findings": []
        }
        
        # 分析关键发现
        for col in columns[:5]:  # 只分析前5个关键指标
            if col in stats and col in stability and col in trends:
                findings = []
                
                # 稳定性发现
                if stability[col]["stability_rating"] in ["极稳定", "稳定"]:
                    findings.append(f"{col}表现稳定")
                elif stability[col]["stability_rating"] == "不稳定":
                    findings.append(f"{col}存在波动")
                
                # 趋势发现
                if trends[col].get("is_significant", False):
                    direction = trends[col]["trend_direction"]
                    strength = trends[col]["trend_strength"]
                    findings.append(f"{col}呈{strength}{direction}趋势")
                
                if findings:
                    summary["key_findings"].append({
                        "column": col,
                        "findings": findings
                    })
        
        return summary

# 使用示例和测试函数
def test_analyzer():
    """测试数据分析器功能"""
    # 创建测试数据
    np.random.seed(42)
    test_data = pd.DataFrame({
        'Vi': np.random.normal(90, 2, 100),
        'Ii': np.random.normal(1.04, 0.05, 100),
        'Vo1': np.random.normal(3.41, 0.1, 100),
        'Eff': np.random.normal(0.77, 0.02, 100)
    })
    
    analyzer = DataAnalyzer()
    
    # 测试各功能
    print("=== 基础统计分析 ===")
    stats = analyzer.basic_statistics(test_data)
    print(stats)
    
    print("\n=== 稳定性分析 ===")
    stability = analyzer.stability_analysis(test_data)
    print(stability)
    
    print("\n=== 趋势分析 ===")
    trends = analyzer.trend_analysis(test_data)
    print(trends)
    
    return analyzer

if __name__ == "__main__":
    test_analyzer()