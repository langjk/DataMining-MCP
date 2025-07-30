# enhanced_gui.py
# 增强版MCP数据分析助手界面 - 包含数据详情面板

import sys
import json
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QFrame, QScrollArea, QStatusBar, QMenuBar, QAction,
                             QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from gpt_dispatcher import dispatch_gpt_response
from gpt_api import ask_gpt
from format_fixer import FormatFixer

class ModernButton(QPushButton):
    """现代化按钮样式"""
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.apply_style()
    
    def apply_style(self):
        if self.primary:
            style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4A90E2, stop:1 #357ABD);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 0 15px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5BA0F2, stop:1 #4A90E2);
                }
                QPushButton:disabled {
                    background: #CCCCCC;
                    color: #888888;
                }
            """
        else:
            style = """
                QPushButton {
                    background: #F8F9FA;
                    color: #495057;
                    border: 2px solid #E9ECEF;
                    border-radius: 6px;
                    font-size: 13px;
                    padding: 0 15px;
                }
                QPushButton:hover {
                    background: #E9ECEF;
                    border-color: #DEE2E6;
                }
            """
        self.setStyleSheet(style)

class StatusIndicator(QLabel):
    """状态指示器"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(12, 12)
        self.set_status("ready")
    
    def set_status(self, status):
        colors = {
            "ready": "#28A745",
            "thinking": "#FFC107", 
            "working": "#17A2B8",
            "error": "#DC3545"
        }
        color = colors.get(status, "#6C757D")
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)

class PlotCanvas(FigureCanvas):
    """matplotlib画布组件"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # 设置中文字体 - 增强版配置
        self.setup_chinese_font()
        
        # 设置样式
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def setup_chinese_font(self):
        """设置中文字体支持"""
        import matplotlib.font_manager as fm
        import matplotlib.pyplot as plt
        
        # 常见的中文字体路径和名称
        chinese_fonts = [
            # Windows系统字体
            'Microsoft YaHei', 'SimHei', 'KaiTi', 'SimSun',
            # Linux系统字体  
            'DejaVu Sans', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC',
            # macOS系统字体
            'PingFang SC', 'Heiti SC', 'STHeiti',
            # 备用字体
            'Arial Unicode MS', 'Droid Sans Fallback'
        ]
        
        # 寻找可用的中文字体
        available_font = None
        for font_name in chinese_fonts:
            try:
                font_path = fm.findfont(fm.FontProperties(family=font_name))
                if font_path and 'DejaVu' not in font_path:  # 排除不支持中文的DejaVu
                    available_font = font_name
                    break
            except:
                continue
        
        # 如果没找到，尝试查找系统中所有包含中文的字体
        if not available_font:
            try:
                fonts = [f.name for f in fm.fontManager.ttflist]
                for font_name in chinese_fonts:
                    if font_name in fonts:
                        available_font = font_name
                        break
            except:
                pass
        
        # 强制设置字体配置 - 更全面的设置
        font_list = [available_font] + chinese_fonts if available_font else chinese_fonts
        
        # 设置所有可能的字体参数
        plt.rcParams['font.sans-serif'] = font_list
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 设置各个组件的字体大小和配置 - 增大字体
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.labelsize'] = 14
        plt.rcParams['xtick.labelsize'] = 11
        plt.rcParams['ytick.labelsize'] = 11
        plt.rcParams['legend.fontsize'] = 11
        plt.rcParams['figure.titlesize'] = 18
        
        # 清除matplotlib的字体缓存，强制重新加载
        try:
            fm._rebuild()
        except:
            pass
    
    def get_chinese_font_prop(self):
        """获取中文字体属性对象"""
        import matplotlib.font_manager as fm
        
        # 优先尝试的字体列表
        preferred_fonts = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'SimSun']
        
        for font_name in preferred_fonts:
            try:
                font_path = fm.findfont(fm.FontProperties(family=font_name))
                if font_path and font_name.lower() in font_path.lower():
                    return fm.FontProperties(family=font_name)
            except:
                continue
        
        # 如果都找不到，返回默认字体
        return fm.FontProperties()
        
    def clear_plot(self):
        """清除图表"""
        self.fig.clear()
        self.draw()
    
    def plot_statistics_charts(self, stats_data):
        """绘制统计数据图表"""
        if not stats_data:
            return
            
        self.fig.clear()
        font_prop = self.get_chinese_font_prop()
        
        # 使用中文标题
        self.fig.suptitle('统计数据可视化', fontsize=18, fontweight='bold', 
                         fontproperties=font_prop)
        
        # 提取数据
        metrics = list(stats_data.keys())[:8]  # 最多显示8个指标
        means = [stats_data[m].get('mean', 0) for m in metrics]
        stds = [stats_data[m].get('std', 0) for m in metrics]
        
        # 创建子图
        ax1 = self.fig.add_subplot(2, 2, 1)
        ax1.bar(metrics, means, color='skyblue', alpha=0.7)
        ax1.set_title('均值对比', fontsize=16, fontproperties=font_prop)
        ax1.tick_params(axis='x', rotation=45, labelsize=11)
        ax1.tick_params(axis='y', labelsize=11)
        
        ax2 = self.fig.add_subplot(2, 2, 2)
        ax2.bar(metrics, stds, color='lightcoral', alpha=0.7)
        ax2.set_title('标准差对比', fontsize=16, fontproperties=font_prop)
        ax2.tick_params(axis='x', rotation=45, labelsize=11)
        ax2.tick_params(axis='y', labelsize=11)
        
        # 变异系数
        cvs = [stats_data[m].get('cv', 0) for m in metrics]
        ax3 = self.fig.add_subplot(2, 2, 3)
        ax3.bar(metrics, cvs, color='lightgreen', alpha=0.7)
        ax3.set_title('变异系数', fontsize=16, fontproperties=font_prop)
        ax3.tick_params(axis='x', rotation=45, labelsize=11)
        ax3.tick_params(axis='y', labelsize=11)
        
        # 散点图：均值 vs 标准差
        ax4 = self.fig.add_subplot(2, 2, 4)
        scatter = ax4.scatter(means, stds, c=cvs, cmap='viridis', alpha=0.7, s=60)
        ax4.set_xlabel('均值', fontsize=14, fontproperties=font_prop)
        ax4.set_ylabel('标准差', fontsize=14, fontproperties=font_prop)
        ax4.set_title('均值-标准差关系', fontsize=16, fontproperties=font_prop)
        ax4.tick_params(labelsize=11)
        cbar = self.fig.colorbar(scatter, ax=ax4)
        cbar.set_label('变异系数', fontsize=14, fontproperties=font_prop)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_stability_charts(self, stability_data):
        """绘制稳定性数据图表"""
        if not stability_data:
            return
            
        self.fig.clear()
        font_prop = self.get_chinese_font_prop()
        
        self.fig.suptitle('稳定性分析可视化', fontsize=14, fontweight='bold', 
                         fontproperties=font_prop)
        
        metrics = list(stability_data.keys())[:10]
        stability_indices = [stability_data[m].get('stability_index', 0) for m in metrics]
        max_changes = [stability_data[m].get('max_change_rate', 0) for m in metrics]
        
        # 稳定性指数柱状图
        ax1 = self.fig.add_subplot(2, 1, 1)
        bars = ax1.bar(metrics, stability_indices, color='steelblue', alpha=0.7)
        ax1.set_title('稳定性指数', fontsize=12, fontproperties=font_prop)
        ax1.set_ylabel('稳定性指数', fontsize=10, fontproperties=font_prop)
        ax1.tick_params(axis='x', rotation=45, labelsize=9)
        ax1.tick_params(axis='y', labelsize=9)
        
        # 添加数值标签
        for bar, val in zip(bars, stability_indices):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.3f}', ha='center', va='bottom', fontsize=8)
        
        # 最大变化率
        ax2 = self.fig.add_subplot(2, 1, 2)
        ax2.bar(metrics, max_changes, color='coral', alpha=0.7)
        ax2.set_title('最大变化率', fontsize=12, fontproperties=font_prop)
        ax2.set_ylabel('最大变化率', fontsize=10, fontproperties=font_prop)
        ax2.tick_params(axis='x', rotation=45, labelsize=9)
        ax2.tick_params(axis='y', labelsize=9)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_trend_charts(self, trend_data):
        """绘制趋势分析图表"""
        if not trend_data:
            return
            
        self.fig.clear()
        font_prop = self.get_chinese_font_prop()
        
        self.fig.suptitle('趋势分析可视化', fontsize=14, fontweight='bold', 
                         fontproperties=font_prop)
        
        # 筛选有效数据
        valid_metrics = []
        correlations = []
        relative_changes = []
        
        for metric, data in trend_data.items():
            if 'error' not in data:
                valid_metrics.append(metric)
                correlations.append(data.get('correlation', 0))
                relative_changes.append(data.get('relative_change', 0))
        
        if not valid_metrics:
            return
        
        valid_metrics = valid_metrics[:8]  # 最多8个指标
        correlations = correlations[:8]
        relative_changes = relative_changes[:8]
        
        # 相关系数
        ax1 = self.fig.add_subplot(2, 1, 1)
        colors = ['red' if c < 0 else 'green' for c in correlations]
        ax1.bar(valid_metrics, correlations, color=colors, alpha=0.7)
        ax1.set_title('趋势相关系数', fontsize=12, fontproperties=font_prop)
        ax1.set_ylabel('相关系数', fontsize=10, fontproperties=font_prop)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.tick_params(axis='x', rotation=45, labelsize=9)
        ax1.tick_params(axis='y', labelsize=9)
        
        # 相对变化百分比
        ax2 = self.fig.add_subplot(2, 1, 2)
        colors = ['red' if c < 0 else 'green' for c in relative_changes]
        ax2.bar(valid_metrics, relative_changes, color=colors, alpha=0.7)
        ax2.set_title('相对变化百分比', fontsize=12, fontproperties=font_prop)
        ax2.set_ylabel('变化百分比 (%)', fontsize=10, fontproperties=font_prop)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.tick_params(axis='x', rotation=45, labelsize=9)
        ax2.tick_params(axis='y', labelsize=9)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_outlier_charts(self, outlier_data):
        """绘制异常检测图表"""
        if not outlier_data:
            return
            
        self.fig.clear()
        font_prop = self.get_chinese_font_prop()
        
        self.fig.suptitle('异常检测可视化', fontsize=14, fontweight='bold', 
                         fontproperties=font_prop)
        
        # 处理两种数据格式
        if isinstance(outlier_data, dict) and 'top_outlier_metrics' in outlier_data:
            # 来自摘要的数据
            top_metrics = outlier_data['top_outlier_metrics'][:8]
            metrics = [m.get('metric', '') for m in top_metrics]
            counts = [m.get('count', 0) for m in top_metrics]
            percentages = [m.get('percentage', 0) for m in top_metrics]
        else:
            # 直接的异常检测数据
            metrics = list(outlier_data.keys())[:8]
            counts = [outlier_data[m].get('outlier_count', 0) for m in metrics]
            percentages = [outlier_data[m].get('outlier_percentage', 0) for m in metrics]
        
        if not metrics:
            return
        
        # 异常值数量
        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.bar(metrics, counts, color='orangered', alpha=0.7)
        ax1.set_title('异常值数量', fontsize=12, fontproperties=font_prop)
        ax1.set_ylabel('异常值数量', fontsize=10, fontproperties=font_prop)
        ax1.tick_params(axis='x', rotation=45, labelsize=9)
        ax1.tick_params(axis='y', labelsize=9)
        
        # 异常值比例
        ax2 = self.fig.add_subplot(2, 1, 2)
        ax2.bar(metrics, percentages, color='darkorange', alpha=0.7)
        ax2.set_title('异常值比例', fontsize=12, fontproperties=font_prop)
        ax2.set_ylabel('异常值比例 (%)', fontsize=10, fontproperties=font_prop)
        ax2.tick_params(axis='x', rotation=45, labelsize=9)
        ax2.tick_params(axis='y', labelsize=9)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_comparison_charts(self, comparison_data):
        """绘制批次对比图表"""
        if not comparison_data:
            return
            
        self.fig.clear()
        font_prop = self.get_chinese_font_prop()
        
        self.fig.suptitle('批次对比可视化', fontsize=14, fontweight='bold', 
                         fontproperties=font_prop)
        
        # 处理不同格式的对比数据
        if "comparison_results" in comparison_data:
            # 精简结果格式
            results = comparison_data["comparison_results"]
            key_differences = results.get("key_differences", [])[:6]
            
            metrics = [diff.get('metric', '') for diff in key_differences]
            changes = [diff.get('mean_change_percent', 0) for diff in key_differences]
            significant = [diff.get('significant', False) for diff in key_differences]
            
        elif "comparison" in comparison_data:
            # 完整结果格式
            comparison = comparison_data["comparison"]
            metrics = list(comparison.keys())[:6]
            changes = [comparison[m].get('mean_change_percent', 0) for m in metrics]
            significant = [comparison[m].get('significant_difference', False) for m in metrics]
        else:
            return
        
        if not metrics:
            return
        
        # 变化百分比柱状图
        ax1 = self.fig.add_subplot(2, 1, 1)
        colors = ['red' if s else 'lightblue' for s in significant]
        bars = ax1.bar(metrics, changes, color=colors, alpha=0.7)
        ax1.set_title('批次间变化百分比', fontsize=12, fontproperties=font_prop)
        ax1.set_ylabel('变化百分比 (%)', fontsize=10, fontproperties=font_prop)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.tick_params(axis='x', rotation=45, labelsize=9)
        ax1.tick_params(axis='y', labelsize=9)
        
        # 添加显著性标记
        for bar, sig in zip(bars, significant):
            if sig:
                height = bar.get_height()
                y_pos = height + (abs(max(changes) - min(changes)) * 0.02) if height >= 0 else height - (abs(max(changes) - min(changes)) * 0.02)
                ax1.text(bar.get_x() + bar.get_width()/2, y_pos,
                        '*', ha='center', va='bottom' if height >= 0 else 'top', 
                        fontsize=12, color='red', fontweight='bold')
        
        # 显著性分布饼图  
        ax2 = self.fig.add_subplot(2, 1, 2)
        sig_count = sum(significant)
        labels = ['显著差异', '无显著差异']
        sizes = [sig_count, len(significant) - sig_count]
        pie_colors = ['lightcoral', 'lightsteelblue']
        
        if sizes[0] > 0 or sizes[1] > 0:
            wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=pie_colors, 
                                              autopct='%1.1f%%', startangle=90)
            ax2.set_title('显著性差异分布', fontsize=12, fontproperties=font_prop)
            
            # 设置饼图文字字体
            for text in texts:
                text.set_fontsize(10)
                text.set_fontproperties(font_prop)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_multi_batch_trend_charts(self, multi_batch_data, selected_metric_type=None):
        """绘制多批次趋势折线图"""
        if not multi_batch_data:
            return
            
        self.fig.clear()
        font_prop = self.get_chinese_font_prop()
        
        # 检查数据类型
        if multi_batch_data.get('analysis_type') == 'multi_batch_comprehensive':
            self._plot_comprehensive_multi_batch_charts(multi_batch_data, font_prop, selected_metric_type)
        elif multi_batch_data.get('analysis_type') == 'multi_batch_outlier_detection':
            self._plot_outlier_detection_lines(multi_batch_data, font_prop)
        else:
            # 默认绘制多批次对比折线图
            self._plot_general_multi_batch_lines(multi_batch_data, font_prop)
    
    def plot_time_series_charts(self, time_series_data):
        """绘制时间序列折线图"""
        print("🔧 [DEBUG] plot_time_series_charts 被调用")
        print(f"🔧 [DEBUG] 接收到的数据类型: {type(time_series_data)}")
        if time_series_data:
            print(f"🔧 [DEBUG] 数据分析类型: {time_series_data.get('analysis_type', 'None')}")
        
        if not time_series_data or time_series_data.get('analysis_type') != 'time_series':
            print("🔧 [DEBUG] 数据验证失败，退出绘制")
            return
            
        self.fig.clear()
        font_prop = self.get_chinese_font_prop()
        
        self.fig.suptitle('时间序列变化曲线', fontsize=18, fontweight='bold', 
                         fontproperties=font_prop)
        
        series_analysis = time_series_data.get('series_analysis', {})
        metrics = list(series_analysis.keys())[:6]  # 最多显示6个指标
        
        if not metrics:
            # 如果没有数据，显示调试信息
            debug_info = time_series_data.get('debug_info', {})
            ax = self.fig.add_subplot(1, 1, 1)
            
            debug_text = '暂无时间序列数据\n\n调试信息:\n'
            debug_text += f"数据列: {debug_info.get('df_columns', [])[:5]}...\n"
            debug_text += f"目标列: {debug_info.get('target_columns', [])}\n"  
            debug_text += f"分析数量: {debug_info.get('analysis_count', 0)}\n"
            debug_text += f"时间列: {time_series_data.get('time_column', 'None')}"
            
            ax.text(0.5, 0.5, debug_text, fontsize=12, 
                   ha='center', va='center', fontproperties=font_prop)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.fig.tight_layout()
            self.draw()
            return
        
        # 计算子图布局
        n_plots = len(metrics)
        n_cols = 2 if n_plots > 1 else 1
        n_rows = (n_plots + n_cols - 1) // n_cols
        
        for i, metric in enumerate(metrics):
            data = series_analysis[metric]
            values = data.get('values', [])
            time_points = data.get('time_points', list(range(len(values))))
            
            if len(values) < 2:
                continue
            
            # 确保时间点和数值长度匹配
            min_len = min(len(values), len(time_points))
            values = values[:min_len]
            time_points = time_points[:min_len]
                
            ax = self.fig.add_subplot(n_rows, n_cols, i + 1)
            
            # 绘制折线图
            ax.plot(time_points, values, 'b-', linewidth=2, marker='o', 
                   markersize=4, alpha=0.8, label=metric)
            
            # 添加趋势线
            if len(values) > 2:
                import numpy as np
                x_trend = np.arange(len(values))
                z = np.polyfit(x_trend, values, 1)
                p = np.poly1d(z)
                ax.plot(time_points, p(x_trend), "r--", alpha=0.7, linewidth=1.5, label='趋势线')
            
            # 设置标题和标签
            trend_direction = data.get('trend_direction', '稳定')
            ax.set_title(f'{metric} - {trend_direction}', fontsize=16, fontproperties=font_prop)
            ax.set_ylabel('数值', fontsize=14, fontproperties=font_prop)
            ax.tick_params(axis='x', labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=11, prop=font_prop)
        
        # 设置底部子图的x轴标签
        for i in range(n_plots):
            if i >= (n_rows - 1) * n_cols:
                ax = self.fig.axes[i]
                ax.set_xlabel('时间点', fontsize=14, fontproperties=font_prop)
        
        self.fig.tight_layout()
        self.draw()
    
    def _plot_stability_trend_lines(self, data, font_prop):
        """绘制稳定性趋势折线图（包括均值趋势）"""
        stability_trends = data.get('stability_trends', {})
        mean_trends = data.get('mean_trends', {})
        
        if not stability_trends and not mean_trends:
            return
            
        # 根据数据内容选择标题
        if mean_trends:
            self.fig.suptitle('多批次均值和稳定性变化趋势', fontsize=18, fontweight='bold', 
                             fontproperties=font_prop)
        else:
            self.fig.suptitle('多批次稳定性变化趋势', fontsize=18, fontweight='bold', 
                             fontproperties=font_prop)
        
        # 优先显示均值趋势，如果没有则显示稳定性趋势
        if mean_trends:
            trends_to_plot = mean_trends
            value_label = '均值'
            is_mean_plot = True
        else:
            trends_to_plot = stability_trends
            value_label = '稳定性指数'
            is_mean_plot = False
        
        metrics = list(trends_to_plot.keys())[:4]  # 最多显示4个指标
        
        for i, metric in enumerate(metrics):
            trend_data = trends_to_plot[metric]
            batch_values = trend_data.get('batch_values', {})
            
            if len(batch_values) < 2:
                continue
                
            ax = self.fig.add_subplot(2, 2, i + 1)
            
            # 准备数据
            batches = list(batch_values.keys())
            values = list(batch_values.values())
            
            # 绘制折线图
            ax.plot(range(len(batches)), values, 'bo-', linewidth=2, 
                   markersize=6, alpha=0.8)
            
            # 添加趋势线
            import numpy as np
            x = np.arange(len(values))
            z = np.polyfit(x, values, 1)
            p = np.poly1d(z)
            trend_color = 'green' if z[0] > 0 else 'red'
            ax.plot(x, p(x), color=trend_color, linestyle='--', 
                   alpha=0.7, linewidth=2)
            
            # 标记最佳和最差批次
            if is_mean_plot:
                # 对于均值图，最高和最低不一定是最佳和最差
                highest_idx = values.index(max(values))
                lowest_idx = values.index(min(values))
                ax.scatter(highest_idx, values[highest_idx], color='blue', s=100, 
                          marker='^', alpha=0.8, label='最高')
                ax.scatter(lowest_idx, values[lowest_idx], color='orange', s=100, 
                          marker='v', alpha=0.8, label='最低')
            else:
                # 对于稳定性图，最高是最佳，最低是最差
                best_idx = values.index(max(values))
                worst_idx = values.index(min(values))
                ax.scatter(best_idx, values[best_idx], color='green', s=100, 
                          marker='^', alpha=0.8, label='最佳')
                ax.scatter(worst_idx, values[worst_idx], color='red', s=100, 
                          marker='v', alpha=0.8, label='最差')
            
            # 设置标题和标签
            trend_direction = trend_data.get('trend_direction', '稳定')
            ax.set_title(f'{metric} - {trend_direction}', fontsize=16, fontproperties=font_prop)
            ax.set_ylabel(value_label, fontsize=14, fontproperties=font_prop)
            ax.set_xticks(range(len(batches)))
            ax.set_xticklabels(batches, rotation=45, fontsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=11, prop=font_prop)
        
        self.fig.tight_layout()
        self.draw()
    
    def _plot_comprehensive_multi_batch_charts(self, data, font_prop, selected_metric_type=None):
        """绘制综合多批次对比图表（支持所有指标类型）"""
        multi_metrics_trends = data.get('multi_metrics_trends', {})
        if not multi_metrics_trends:
            return
            
        self.fig.suptitle('多批次全面指标对比分析', fontsize=18, fontweight='bold', 
                         fontproperties=font_prop)
        
        # 获取前4个指标进行展示
        metrics = list(multi_metrics_trends.keys())[:4]
        
        for i, metric in enumerate(metrics):
            metric_data = multi_metrics_trends[metric]
            batch_names = metric_data.get('batch_names', [])
            metrics_info = metric_data.get('metrics', {})
            
            if len(batch_names) < 2 or not metrics_info:
                continue
                
            ax = self.fig.add_subplot(2, 2, i + 1)
            
            # 根据选择的指标类型获取数据
            metric_type_map = {
                '均值': 'mean',
                '标准差': 'std', 
                '变异系数': 'cv',
                '最小值': 'min',
                '最大值': 'max',
                '稳定性指数': 'stability_index',
                '异常值数量': 'outlier_count'
            }
            
            # 获取当前选择的指标类型
            if selected_metric_type is None:
                selected_metric_type = '均值'  # 默认值
                
                # 尝试从多个层级找到指标类型选择器
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'metric_type_combo'):
                        selected_metric_type = parent.metric_type_combo.currentText()
                        break
                    parent = getattr(parent, 'parent', lambda: None)()
                    if parent is None:
                        break
            
            metric_key = metric_type_map.get(selected_metric_type, 'mean')
            selected_data = metrics_info.get(metric_key, {})
            
            if selected_data.get('values'):
                # 绘制选择的指标趋势线
                values = selected_data['values']
                ax.plot(range(len(batch_names)), values, 'bo-', linewidth=2, 
                       markersize=6, alpha=0.8, label=selected_metric_type)
                
                # 添加趋势线
                import numpy as np
                x = np.arange(len(values))
                slope = selected_data.get('trend_slope', 0)
                if abs(slope) > 0.001:
                    z = np.polyfit(x, values, 1)
                    p = np.poly1d(z)
                    trend_color = 'green' if slope > 0 else 'red'
                    ax.plot(x, p(x), color=trend_color, linestyle='--', 
                           alpha=0.7, linewidth=2, label='趋势线')
                
                # 标记最佳和最差批次（如果有的话）
                best_batch = selected_data.get('best_batch', '')
                worst_batch = selected_data.get('worst_batch', '')
                if best_batch in batch_names and worst_batch in batch_names:
                    best_idx = batch_names.index(best_batch)
                    worst_idx = batch_names.index(worst_batch)
                    ax.scatter(best_idx, values[best_idx], color='green', s=100, 
                              marker='^', alpha=0.8, label='最佳')
                    ax.scatter(worst_idx, values[worst_idx], color='red', s=100, 
                              marker='v', alpha=0.8, label='最差')
            
            # 设置标题和标签
            trend_direction = selected_data.get('trend_direction', '稳定')
            change_percent = selected_data.get('change_percent', 0)
            ax.set_title(f'{metric} ({selected_metric_type}) - {trend_direction} ({change_percent:+.1f}%)', 
                        fontsize=12, fontproperties=font_prop)
            ax.set_ylabel('数值', fontsize=12, fontproperties=font_prop)
            ax.set_xticks(range(len(batch_names)))
            ax.set_xticklabels(batch_names, rotation=45, fontsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=10, prop=font_prop)
        
        self.fig.tight_layout()
        self.draw()
    
    def _plot_outlier_detection_lines(self, data, font_prop):
        """绘制异常批次检测折线图"""
        batch_outlier_scores = data.get('batch_outlier_scores', {})
        if not batch_outlier_scores:
            return
            
        self.fig.suptitle('批次异常程度分析', fontsize=18, fontweight='bold', 
                         fontproperties=font_prop)
        
        # 准备数据
        batches = list(batch_outlier_scores.keys())
        scores = list(batch_outlier_scores.values())
        
        ax = self.fig.add_subplot(1, 1, 1)
        
        # 绘制折线图
        ax.plot(range(len(batches)), scores, 'ro-', linewidth=2, 
               markersize=8, alpha=0.8)
        
        # 标记异常阈值线
        import numpy as np
        threshold = np.mean(scores) + np.std(scores)
        ax.axhline(y=threshold, color='orange', linestyle='--', 
                  alpha=0.7, linewidth=2, label=f'异常阈值 ({threshold:.2f})')
        
        # 标记最异常的批次
        most_abnormal_batches = data.get('most_abnormal_batches', [])[:3]
        for batch_name, score in most_abnormal_batches:
            if batch_name in batches:
                idx = batches.index(batch_name)
                ax.scatter(idx, score, color='red', s=150, 
                          marker='x', alpha=0.9)
                ax.annotate(f'异常', (idx, score), xytext=(5, 5), 
                           textcoords='offset points', fontsize=11,
                           fontproperties=font_prop, color='red')
        
        # 设置标题和标签
        ax.set_title('批次异常评分', fontsize=16, fontproperties=font_prop)
        ax.set_xlabel('批次', fontsize=14, fontproperties=font_prop)
        ax.set_ylabel('异常评分', fontsize=14, fontproperties=font_prop)
        ax.set_xticks(range(len(batches)))
        ax.set_xticklabels(batches, rotation=45, fontsize=11)
        ax.tick_params(axis='y', labelsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11, prop=font_prop)
        
        self.fig.tight_layout()
        self.draw()
    
    def _plot_general_multi_batch_lines(self, data, font_prop):
        """绘制通用多批次对比折线图"""
        # 这个方法用于处理其他类型的多批次数据
        self.fig.suptitle('多批次对比分析', fontsize=18, fontweight='bold', 
                         fontproperties=font_prop)
        
        ax = self.fig.add_subplot(1, 1, 1)
        ax.text(0.5, 0.5, '暂无可视化数据', 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=16, fontproperties=font_prop)
        
        self.fig.tight_layout()
        self.draw()

class ChatMessage(QFrame):
    """聊天消息组件"""
    def __init__(self, sender, content, message_type="user"):
        super().__init__()
        self.setup_ui(sender, content, message_type)
    
    def setup_ui(self, sender, content, message_type):
        self.setFrameStyle(QFrame.NoFrame)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 消息头部
        header_layout = QHBoxLayout()
        
        # 发送者标签
        sender_label = QLabel(sender)
        sender_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        
        # 时间戳
        import datetime
        time_label = QLabel(datetime.datetime.now().strftime("%H:%M"))
        time_label.setFont(QFont("微软雅黑", 9))
        time_label.setStyleSheet("color: #6C757D;")
        
        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        
        # 消息内容 - 使用QLabel替代QTextEdit实现自动高度
        content_display = QLabel()
        content_display.setText(content)
        content_display.setFont(QFont("微软雅黑", 11))
        content_display.setWordWrap(True)  # 启用自动换行
        content_display.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # 顶部左对齐
        content_display.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 允许选择文本
        content_display.setMinimumHeight(30)  # 最小高度
        content_display.setSizePolicy(content_display.sizePolicy().horizontalPolicy(), 
                                    content_display.sizePolicy().Expanding)  # 垂直方向可扩展
        
        content_display.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                padding: 5px;
                line-height: 1.4;
            }
        """)
        
        layout.addLayout(header_layout)
        layout.addWidget(content_display)
        self.setLayout(layout)
        
        # 设置样式
        if message_type == "user":
            self.setStyleSheet("""
                QFrame {
                    background-color: #E3F2FD;
                    border-left: 4px solid #2196F3;
                    border-radius: 8px;
                    margin: 5px 0;
                }
            """)
        elif message_type == "assistant":
            self.setStyleSheet("""
                QFrame {
                    background-color: #F1F8E9;
                    border-left: 4px solid #4CAF50;
                    border-radius: 8px;
                    margin: 5px 0;
                }
            """)
        elif message_type == "tool":
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFF3E0;
                    border-left: 4px solid #FF9800;
                    border-radius: 8px;
                    margin: 5px 0;
                }
            """)
        elif message_type == "error":
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFEBEE;
                    border-left: 4px solid #F44336;
                    border-radius: 8px;
                    margin: 5px 0;
                }
            """)

class DataDetailsPanel(QWidget):
    """数据详情面板"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_data = None
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 面板标题
        title = QLabel("📊 数据详情")
        title.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E1E5E9;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F8F9FA;
                border: 1px solid #E1E5E9;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: none;
            }
        """)
        
        # 统计数据标签页
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "📈 统计数据")
        
        # 稳定性标签页
        self.stability_tab = self.create_stability_tab()
        self.tab_widget.addTab(self.stability_tab, "🎯 稳定性")
        
        # 趋势分析标签页
        self.trend_tab = self.create_trend_tab()
        self.tab_widget.addTab(self.trend_tab, "📊 趋势分析")
        
        # 异常检测标签页
        self.outlier_tab = self.create_outlier_tab()
        self.tab_widget.addTab(self.outlier_tab, "⚠️ 异常检测")
        
        # 批次对比标签页
        self.comparison_tab = self.create_comparison_tab()
        self.tab_widget.addTab(self.comparison_tab, "⚖️ 多批次对比")
        
        # 可视化图表标签页
        self.visualization_tab = self.create_visualization_tab()
        self.tab_widget.addTab(self.visualization_tab, "📊 可视化图表")
        
        layout.addWidget(self.tab_widget)
        
        # 导出按钮
        export_layout = QHBoxLayout()
        export_btn = ModernButton("导出数据")
        export_btn.clicked.connect(self.export_data)
        export_layout.addStretch()
        export_layout.addWidget(export_btn)
        layout.addLayout(export_layout)
        
        self.setLayout(layout)
    
    def create_stats_tab(self):
        """创建统计数据标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 创建表格
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)
        self.stats_table.setHorizontalHeaderLabels(["指标", "均值", "标准差", "最小值", "最大值", "变异系数"])
        
        # 设置表格样式
        self.stats_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E1E5E9;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #F1F3F4;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.stats_table)
        widget.setLayout(layout)
        return widget
    
    def create_stability_tab(self):
        """创建稳定性标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.stability_table = QTableWidget()
        self.stability_table.setColumnCount(4)
        self.stability_table.setHorizontalHeaderLabels(["指标", "稳定性评级", "稳定性指数", "最大变化率"])
        
        self.stability_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E1E5E9;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #F1F3F4;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.stability_table.setAlternatingRowColors(True)
        self.stability_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.stability_table)
        widget.setLayout(layout)
        return widget
    
    def create_trend_tab(self):
        """创建趋势分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.trend_table = QTableWidget()
        self.trend_table.setColumnCount(5)
        self.trend_table.setHorizontalHeaderLabels(["指标", "趋势方向", "趋势强度", "相关系数", "相对变化%"])
        
        self.trend_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E1E5E9;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #F1F3F4;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.trend_table.setAlternatingRowColors(True)
        self.trend_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.trend_table)
        widget.setLayout(layout)
        return widget
    
    def create_outlier_tab(self):
        """创建异常检测标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.outlier_table = QTableWidget()
        self.outlier_table.setColumnCount(3)
        self.outlier_table.setHorizontalHeaderLabels(["指标", "异常值数量", "异常值比例%"])
        
        self.outlier_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E1E5E9;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #F1F3F4;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.outlier_table.setAlternatingRowColors(True)
        self.outlier_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.outlier_table)
        widget.setLayout(layout)
        return widget
    
    def create_comparison_tab(self):
        """创建多批次对比标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加控制面板（仅用于多批次分析）
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        
        # 指标类型选择器
        metric_label = QLabel("显示指标:")
        metric_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        
        self.comparison_metric_combo = QComboBox()
        self.comparison_metric_combo.addItems([
            "均值", "标准差", "变异系数", "最小值", "最大值", "稳定性指数", "异常值数量"
        ])
        self.comparison_metric_combo.currentTextChanged.connect(self.on_comparison_metric_changed)
        
        # 默认隐藏控制面板
        control_panel.setVisible(False)
        self.comparison_control_panel = control_panel
        
        control_layout.addWidget(metric_label)
        control_layout.addWidget(self.comparison_metric_combo)
        control_layout.addStretch()
        
        # 添加查看图表按钮
        view_chart_btn = ModernButton("查看图表")
        view_chart_btn.clicked.connect(self.view_multi_batch_chart)
        view_chart_btn.setFixedWidth(100)
        control_layout.addWidget(view_chart_btn)
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(8)
        self.comparison_table.setHorizontalHeaderLabels([
            "指标", "批次1均值", "批次2均值", "变化%", "稳定性对比", "显著差异", "改进情况", "T检验P值"
        ])
        
        self.comparison_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E1E5E9;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #F1F3F4;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.horizontalHeader().setStretchLastSection(True)
        self.comparison_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.comparison_table)
        widget.setLayout(layout)
        return widget
    
    def create_visualization_tab(self):
        """创建可视化图表标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 图表类型选择
        control_layout = QHBoxLayout()
        
        type_label = QLabel("图表类型:")
        type_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "自动选择",
            "统计数据图表", 
            "稳定性图表",
            "趋势分析图表", 
            "异常检测图表",
            "多批次对比图表",
            "多批次趋势折线图",
            "时间序列折线图"
        ])
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        
        # 指标类型选择（仅用于多批次分析）
        metric_type_label = QLabel("指标类型:")
        metric_type_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        
        self.metric_type_combo = QComboBox()
        self.metric_type_combo.addItems([
            "均值",
            "标准差", 
            "变异系数",
            "最小值",
            "最大值",
            "稳定性指数",
            "异常值数量"
        ])
        self.metric_type_combo.currentTextChanged.connect(self.on_metric_type_changed)
        self.metric_type_combo.setVisible(False)  # 默认隐藏
        metric_type_label.setVisible(False)  # 默认隐藏
        
        refresh_btn = ModernButton("刷新图表")
        refresh_btn.clicked.connect(self.refresh_charts)
        refresh_btn.setFixedWidth(100)
        
        control_layout.addWidget(type_label)
        control_layout.addWidget(self.chart_type_combo)
        control_layout.addWidget(metric_type_label)
        control_layout.addWidget(self.metric_type_combo)
        control_layout.addStretch()
        control_layout.addWidget(refresh_btn)
        
        # 保存标签引用以便后续控制显示
        self.metric_type_label = metric_type_label
        
        layout.addLayout(control_layout)
        
        # matplotlib画布
        self.plot_canvas = PlotCanvas(self, width=8, height=6, dpi=80)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.plot_canvas)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E1E5E9;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
    
    def update_data(self, analysis_data):
        """更新数据显示"""
        self.current_data = analysis_data
        
        # 清空所有表格
        self.clear_all_tables()
        
        # 检查是否是多批次分析结果
        if self._is_multi_batch_result(analysis_data):
            # 更新多批次对比表格
            self.update_multi_batch_table(analysis_data)
            # 切换到多批次对比标签页
            self.tab_widget.setCurrentWidget(self.comparison_tab)
        # 检查是否是时间序列分析结果
        elif self._is_time_series_result(analysis_data):
            print("🔧 [DEBUG] GUI识别到时间序列分析结果")
            print(f"🔧 [DEBUG] 数据内容: {analysis_data.get('analysis_type', 'unknown')}")
            # 直接切换到可视化标签页显示时间序列图
            self.tab_widget.setCurrentWidget(self.visualization_tab)
            # 确保自动选择正确的图表类型
            self.auto_select_chart()
        # 检查是否是批次对比结果
        elif self._is_batch_comparison_result(analysis_data):
            self.update_comparison_table(analysis_data)
            # 切换到批次对比标签页
            self.tab_widget.setCurrentWidget(self.comparison_tab)
        # 检查是否是单一分析类型的结果（直接返回指标数据）
        elif self._is_single_metric_result(analysis_data):
            # 判断分析类型并更新相应表格
            if self._looks_like_stability_data(analysis_data):
                self.update_stability_table(analysis_data)
                self.tab_widget.setCurrentWidget(self.stability_tab)
            elif self._looks_like_trend_data(analysis_data):
                self.update_trend_table(analysis_data)
                self.tab_widget.setCurrentWidget(self.trend_tab)
            elif self._looks_like_outlier_data(analysis_data):
                self.update_outlier_table(analysis_data)
                self.tab_widget.setCurrentWidget(self.outlier_tab)
            elif self._looks_like_stats_data(analysis_data):
                self.update_stats_table(analysis_data)
                self.tab_widget.setCurrentWidget(self.stats_tab)
        else:
            # 处理综合分析结果
            # 更新统计数据
            if "key_metrics_statistics" in analysis_data:
                self.update_stats_table(analysis_data["key_metrics_statistics"])
            elif "basic_statistics" in analysis_data:
                self.update_stats_table(analysis_data["basic_statistics"])
            
            # 更新稳定性数据
            if "key_metrics_stability" in analysis_data:
                self.update_stability_table(analysis_data["key_metrics_stability"])
            elif "stability_analysis" in analysis_data:
                self.update_stability_table(analysis_data["stability_analysis"])
            
            # 更新趋势数据
            if "key_metrics_trends" in analysis_data:
                self.update_trend_table(analysis_data["key_metrics_trends"])
            elif "trend_analysis" in analysis_data:
                self.update_trend_table(analysis_data["trend_analysis"])
            
            # 更新异常检测数据
            if "outlier_summary" in analysis_data:
                self.update_outlier_table_from_summary(analysis_data["outlier_summary"])
            elif "outlier_detection" in analysis_data:
                self.update_outlier_table(analysis_data["outlier_detection"])
        
        # 自动更新可视化图表
        self.update_visualization()
    
    def clear_all_tables(self):
        """清空所有表格数据"""
        self.stats_table.setRowCount(0)
        self.stability_table.setRowCount(0)
        self.trend_table.setRowCount(0)
        self.outlier_table.setRowCount(0)
        self.comparison_table.setRowCount(0)
        
        # 隐藏多批次对比的控制面板
        if hasattr(self, 'comparison_control_panel'):
            self.comparison_control_panel.setVisible(False)
        
        # 清除存储的多批次数据
        if hasattr(self, 'multi_batch_data'):
            delattr(self, 'multi_batch_data')
        
        # 清除图表
        if hasattr(self, 'plot_canvas'):
            self.plot_canvas.clear_plot()
    
    def _is_single_metric_result(self, data):
        """判断是否是单一指标结果（非嵌套结构）"""
        if not isinstance(data, dict):
            return False
        
        # 检查是否所有值都是指标数据字典
        for key, value in data.items():
            if isinstance(value, dict) and any(field in value for field in 
                ["stability_rating", "trend_direction", "outlier_count", "mean", "std"]):
                return True
        return False
    
    def _looks_like_stability_data(self, data):
        """判断是否像稳定性分析数据"""
        for value in data.values():
            if isinstance(value, dict) and "stability_rating" in value:
                return True
        return False
    
    def _looks_like_trend_data(self, data):
        """判断是否像趋势分析数据"""
        for value in data.values():
            if isinstance(value, dict) and "trend_direction" in value:
                return True
        return False
    
    def _looks_like_outlier_data(self, data):
        """判断是否像异常检测数据"""
        for value in data.values():
            if isinstance(value, dict) and "outlier_count" in value:
                return True
        return False
    
    def _looks_like_stats_data(self, data):
        """判断是否像统计数据"""
        for value in data.values():
            if isinstance(value, dict) and ("mean" in value or "std" in value):
                return True
        return False
    
    def _is_batch_comparison_result(self, data):
        """判断是否是批次对比结果"""
        return isinstance(data, dict) and (
            "comparison_results" in data or  # 来自gpt_dispatcher的精简结果
            ("batch1_name" in data and "batch2_name" in data and "comparison" in data)  # 原始结果
        )
    
    def update_stats_table(self, stats_data):
        """更新统计数据表格"""
        self.stats_table.setRowCount(len(stats_data))
        
        for row, (metric, data) in enumerate(stats_data.items()):
            self.stats_table.setItem(row, 0, QTableWidgetItem(metric))
            self.stats_table.setItem(row, 1, QTableWidgetItem(f"{data.get('mean', 0):.4f}"))
            self.stats_table.setItem(row, 2, QTableWidgetItem(f"{data.get('std', 0):.4f}"))
            if isinstance(data.get('range'), list) and len(data['range']) >= 2:
                self.stats_table.setItem(row, 3, QTableWidgetItem(f"{data['range'][0]:.4f}"))
                self.stats_table.setItem(row, 4, QTableWidgetItem(f"{data['range'][1]:.4f}"))
            else:
                self.stats_table.setItem(row, 3, QTableWidgetItem(f"{data.get('min', 0):.4f}"))
                self.stats_table.setItem(row, 4, QTableWidgetItem(f"{data.get('max', 0):.4f}"))
            self.stats_table.setItem(row, 5, QTableWidgetItem(f"{data.get('cv', 0):.4f}"))
    
    def update_stability_table(self, stability_data):
        """更新稳定性表格"""
        self.stability_table.setRowCount(len(stability_data))
        
        for row, (metric, data) in enumerate(stability_data.items()):
            self.stability_table.setItem(row, 0, QTableWidgetItem(metric))
            self.stability_table.setItem(row, 1, QTableWidgetItem(data.get('stability_rating', '')))
            self.stability_table.setItem(row, 2, QTableWidgetItem(f"{data.get('stability_index', 0):.4f}"))
            self.stability_table.setItem(row, 3, QTableWidgetItem(f"{data.get('max_change_rate', 0):.4f}"))
    
    def update_trend_table(self, trend_data):
        """更新趋势表格"""
        self.trend_table.setRowCount(len(trend_data))
        
        for row, (metric, data) in enumerate(trend_data.items()):
            if "error" not in data:
                self.trend_table.setItem(row, 0, QTableWidgetItem(metric))
                self.trend_table.setItem(row, 1, QTableWidgetItem(data.get('trend_direction', '')))
                self.trend_table.setItem(row, 2, QTableWidgetItem(data.get('trend_strength', '')))
                self.trend_table.setItem(row, 3, QTableWidgetItem(f"{data.get('correlation', 0):.4f}"))
                self.trend_table.setItem(row, 4, QTableWidgetItem(f"{data.get('relative_change', 0):.2f}"))
    
    def update_outlier_table(self, outlier_data):
        """更新异常检测表格"""
        self.outlier_table.setRowCount(len(outlier_data))
        
        for row, (metric, data) in enumerate(outlier_data.items()):
            self.outlier_table.setItem(row, 0, QTableWidgetItem(metric))
            self.outlier_table.setItem(row, 1, QTableWidgetItem(str(data.get('outlier_count', 0))))
            self.outlier_table.setItem(row, 2, QTableWidgetItem(f"{data.get('outlier_percentage', 0):.2f}"))
    
    def update_outlier_table_from_summary(self, outlier_summary):
        """从异常检测摘要更新表格"""
        top_metrics = outlier_summary.get('top_outlier_metrics', [])
        self.outlier_table.setRowCount(len(top_metrics))
        
        for row, metric_data in enumerate(top_metrics):
            self.outlier_table.setItem(row, 0, QTableWidgetItem(metric_data.get('metric', '')))
            self.outlier_table.setItem(row, 1, QTableWidgetItem(str(metric_data.get('count', 0))))
            self.outlier_table.setItem(row, 2, QTableWidgetItem(f"{metric_data.get('percentage', 0):.2f}"))
    
    def update_comparison_table(self, comparison_data):
        """更新批次对比表格"""
        # 处理来自gpt_dispatcher的精简结果
        if "comparison_results" in comparison_data:
            results = comparison_data["comparison_results"]
            key_differences = results.get("key_differences", [])
            
            self.comparison_table.setRowCount(len(key_differences))
            
            for row, diff in enumerate(key_differences):
                self.comparison_table.setItem(row, 0, QTableWidgetItem(diff.get('metric', '')))
                self.comparison_table.setItem(row, 1, QTableWidgetItem("N/A"))  # 批次1均值在精简结果中未包含
                self.comparison_table.setItem(row, 2, QTableWidgetItem("N/A"))  # 批次2均值在精简结果中未包含
                self.comparison_table.setItem(row, 3, QTableWidgetItem(f"{diff.get('mean_change_percent', 0):.2f}%"))
                self.comparison_table.setItem(row, 4, QTableWidgetItem(diff.get('stability_comparison', '')))
                self.comparison_table.setItem(row, 5, QTableWidgetItem("是" if diff.get('significant', False) else "否"))
                self.comparison_table.setItem(row, 6, QTableWidgetItem(diff.get('improvement', '')))
                self.comparison_table.setItem(row, 7, QTableWidgetItem("N/A"))  # P值在精简结果中未包含
        
        # 处理原始的完整批次对比结果
        elif "comparison" in comparison_data:
            comparison = comparison_data["comparison"]
            metrics = list(comparison.keys())
            
            self.comparison_table.setRowCount(len(metrics))
            
            for row, metric in enumerate(metrics):
                data = comparison[metric]
                self.comparison_table.setItem(row, 0, QTableWidgetItem(metric))
                self.comparison_table.setItem(row, 1, QTableWidgetItem(f"{data.get('batch1_mean', 0):.4f}"))
                self.comparison_table.setItem(row, 2, QTableWidgetItem(f"{data.get('batch2_mean', 0):.4f}"))
                self.comparison_table.setItem(row, 3, QTableWidgetItem(f"{data.get('mean_change_percent', 0):.2f}%"))
                self.comparison_table.setItem(row, 4, QTableWidgetItem(data.get('stability_comparison', '')))
                self.comparison_table.setItem(row, 5, QTableWidgetItem("是" if data.get('significant_difference', False) else "否"))
                self.comparison_table.setItem(row, 6, QTableWidgetItem(data.get('improvement', '')))
                self.comparison_table.setItem(row, 7, QTableWidgetItem(f"{data.get('t_p_value', 0):.4f}"))
    
    def update_multi_batch_table(self, multi_batch_data):
        """更新多批次对比表格"""
        # 显示控制面板
        if hasattr(self, 'comparison_control_panel'):
            self.comparison_control_panel.setVisible(True)
        
        # 存储多批次数据供下拉框切换使用
        self.multi_batch_data = multi_batch_data
        
        # 更新表格列标题为多批次格式
        multi_metrics_trends = multi_batch_data.get('multi_metrics_trends', {})
        if multi_metrics_trends:
            # 获取批次名称
            first_metric = list(multi_metrics_trends.keys())[0]
            batch_names = multi_metrics_trends[first_metric].get('batch_names', [])
            
            # 动态设置列数和表头
            num_batches = len(batch_names)
            self.comparison_table.setColumnCount(num_batches + 4)
            
            headers = ["指标"] + batch_names + ["趋势方向", "变化率%", "最佳批次"]
            self.comparison_table.setHorizontalHeaderLabels(headers)
        
        # 初始显示均值数据
        self._update_multi_batch_table_data()
    
    def on_comparison_metric_changed(self):
        """多批次对比表格中指标类型改变的处理"""
        if hasattr(self, 'multi_batch_data'):
            self._update_multi_batch_table_data()
    
    def _update_multi_batch_table_data(self):
        """根据选择的指标类型更新多批次表格数据"""
        if not hasattr(self, 'multi_batch_data'):
            return
            
        multi_metrics_trends = self.multi_batch_data.get('multi_metrics_trends', {})
        if not multi_metrics_trends:
            return
            
        # 获取选择的指标类型
        metric_type_map = {
            '均值': 'mean',
            '标准差': 'std', 
            '变异系数': 'cv',
            '最小值': 'min',
            '最大值': 'max',
            '稳定性指数': 'stability_index',
            '异常值数量': 'outlier_count'
        }
        
        selected_metric_type = self.comparison_metric_combo.currentText()
        metric_key = metric_type_map.get(selected_metric_type, 'mean')
        
        # 准备表格数据
        metrics = list(multi_metrics_trends.keys())
        self.comparison_table.setRowCount(len(metrics))
        
        for row, metric in enumerate(metrics):
            metric_data = multi_metrics_trends[metric]
            batch_names = metric_data.get('batch_names', [])
            metrics_info = metric_data.get('metrics', {})
            selected_data = metrics_info.get(metric_key, {})
            
            # 设置指标名称
            self.comparison_table.setItem(row, 0, QTableWidgetItem(metric))
            
            # 设置各批次的数值
            values = selected_data.get('values', [])
            for col, value in enumerate(values):
                if col < len(batch_names):
                    self.comparison_table.setItem(row, col + 1, QTableWidgetItem(f"{value:.4f}"))
            
            # 设置趋势方向
            trend_direction = selected_data.get('trend_direction', '稳定')
            self.comparison_table.setItem(row, len(batch_names) + 1, QTableWidgetItem(trend_direction))
            
            # 设置变化率
            change_percent = selected_data.get('change_percent', 0)
            self.comparison_table.setItem(row, len(batch_names) + 2, QTableWidgetItem(f"{change_percent:+.2f}%"))
            
            # 设置最佳批次
            best_batch = selected_data.get('best_batch', '')
            self.comparison_table.setItem(row, len(batch_names) + 3, QTableWidgetItem(best_batch))
    
    def view_multi_batch_chart(self):
        """切换到可视化标签页查看多批次图表"""
        if hasattr(self, 'multi_batch_data'):
            # 切换到可视化标签页
            self.tab_widget.setCurrentWidget(self.visualization_tab)
            # 自动选择多批次趋势折线图
            self.chart_type_combo.setCurrentText("多批次趋势折线图")
            # 同步指标类型选择
            if hasattr(self, 'metric_type_combo'):
                selected_metric = self.comparison_metric_combo.currentText()
                self.metric_type_combo.setCurrentText(selected_metric)
    
    def export_data(self):
        """导出数据"""
        if not self.current_data:
            return
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, ensure_ascii=False, indent=2)
            
            # 显示成功消息（这里简化处理）
            print(f"数据已导出到: {filename}")
        except Exception as e:
            print(f"导出失败: {str(e)}")
    
    def update_visualization(self):
        """更新可视化图表"""
        if not hasattr(self, 'plot_canvas') or not self.current_data:
            return
        
        chart_type = self.chart_type_combo.currentText()
        
        if chart_type == "自动选择":
            # 根据数据类型自动选择图表
            self.auto_select_chart()
        elif chart_type == "统计数据图表":
            self.plot_statistics_chart()
        elif chart_type == "稳定性图表":
            self.plot_stability_chart()
        elif chart_type == "趋势分析图表":
            self.plot_trend_chart()
        elif chart_type == "异常检测图表":
            self.plot_outlier_chart()
        elif chart_type == "多批次对比图表":
            self.plot_comparison_chart()
        elif chart_type == "多批次趋势折线图":
            self.plot_multi_batch_trend_chart()
        elif chart_type == "时间序列折线图":
            self.plot_time_series_chart()
    
    def auto_select_chart(self):
        """自动选择合适的图表类型"""
        if not self.current_data:
            return
        
        # 检查数据类型并绘制相应图表
        if self._is_multi_batch_result(self.current_data):
            self.chart_type_combo.setCurrentText("多批次趋势折线图")
            # 确保指标类型选择器显示
            self.metric_type_combo.setVisible(True)
            self.metric_type_label.setVisible(True)
            self.plot_multi_batch_trend_chart()
        elif self._is_time_series_result(self.current_data):
            self.plot_time_series_chart()
            self.chart_type_combo.setCurrentText("时间序列折线图")
        elif self._is_batch_comparison_result(self.current_data):
            self.plot_comparison_chart()
            self.chart_type_combo.setCurrentText("多批次对比图表")
        elif self._looks_like_stability_data(self.current_data):
            self.plot_stability_chart()
            self.chart_type_combo.setCurrentText("稳定性图表")
        elif self._looks_like_trend_data(self.current_data):
            self.plot_trend_chart()
            self.chart_type_combo.setCurrentText("趋势分析图表")
        elif self._looks_like_outlier_data(self.current_data):
            self.plot_outlier_chart()
            self.chart_type_combo.setCurrentText("异常检测图表")
        else:
            # 默认绘制统计图表
            self.plot_statistics_chart()
            self.chart_type_combo.setCurrentText("统计数据图表")
    
    def plot_statistics_chart(self):
        """绘制统计数据图表"""
        stats_data = None
        
        if "key_metrics_statistics" in self.current_data:
            stats_data = self.current_data["key_metrics_statistics"]
        elif "basic_statistics" in self.current_data:
            stats_data = self.current_data["basic_statistics"]
        elif self._looks_like_stats_data(self.current_data):
            stats_data = self.current_data
        
        if stats_data:
            self.plot_canvas.plot_statistics_charts(stats_data)
    
    def plot_stability_chart(self):
        """绘制稳定性图表"""
        stability_data = None
        
        if "key_metrics_stability" in self.current_data:
            stability_data = self.current_data["key_metrics_stability"]
        elif "stability_analysis" in self.current_data:
            stability_data = self.current_data["stability_analysis"]
        elif self._looks_like_stability_data(self.current_data):
            stability_data = self.current_data
        
        if stability_data:
            self.plot_canvas.plot_stability_charts(stability_data)
    
    def plot_trend_chart(self):
        """绘制趋势分析图表"""
        trend_data = None
        
        if "key_metrics_trends" in self.current_data:
            trend_data = self.current_data["key_metrics_trends"]
        elif "trend_analysis" in self.current_data:
            trend_data = self.current_data["trend_analysis"]
        elif self._looks_like_trend_data(self.current_data):
            trend_data = self.current_data
        
        if trend_data:
            self.plot_canvas.plot_trend_charts(trend_data)
    
    def plot_outlier_chart(self):
        """绘制异常检测图表"""
        outlier_data = None
        
        if "outlier_summary" in self.current_data:
            outlier_data = self.current_data["outlier_summary"]
        elif "outlier_detection" in self.current_data:
            outlier_data = self.current_data["outlier_detection"]
        elif self._looks_like_outlier_data(self.current_data):
            outlier_data = self.current_data
        
        if outlier_data:
            self.plot_canvas.plot_outlier_charts(outlier_data)
    
    def plot_comparison_chart(self):
        """绘制批次对比图表"""
        if self._is_batch_comparison_result(self.current_data):
            self.plot_canvas.plot_comparison_charts(self.current_data)
    
    def on_chart_type_changed(self):
        """图表类型改变时的处理"""
        chart_type = self.chart_type_combo.currentText()
        # 只有在多批次趋势折线图时显示指标类型选择器
        is_multi_batch = chart_type == "多批次趋势折线图"
        self.metric_type_combo.setVisible(is_multi_batch)
        self.metric_type_label.setVisible(is_multi_batch)
        
        self.update_visualization()
    
    def on_metric_type_changed(self):
        """指标类型改变时的处理"""
        # 当指标类型改变时，重新绘制图表
        if self.chart_type_combo.currentText() == "多批次趋势折线图":
            self.plot_multi_batch_trend_chart()
    
    def refresh_charts(self):
        """刷新图表"""
        self.update_visualization()
    
    def _is_multi_batch_result(self, data):
        """判断是否是多批次分析结果"""
        return isinstance(data, dict) and (
            data.get('analysis_type') in ['multi_batch_stability_trend', 'multi_batch_outlier_detection', 'multi_batch_comprehensive']
        )
    
    def _is_time_series_result(self, data):
        """判断是否是时间序列分析结果"""
        return isinstance(data, dict) and data.get('analysis_type') == 'time_series'
    
    def plot_multi_batch_trend_chart(self):
        """绘制多批次趋势折线图"""
        if self._is_multi_batch_result(self.current_data):
            # 获取当前选择的指标类型
            selected_metric_type = None
            if hasattr(self, 'metric_type_combo'):
                selected_metric_type = self.metric_type_combo.currentText()
            self.plot_canvas.plot_multi_batch_trend_charts(self.current_data, selected_metric_type)
    
    def plot_time_series_chart(self):
        """绘制时间序列折线图"""
        if self._is_time_series_result(self.current_data):
            self.plot_canvas.plot_time_series_charts(self.current_data)

class GPTWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def run(self):
        try:
            gpt_reply = ask_gpt(self.messages)
            self.response_ready.emit(gpt_reply)
        except Exception as e:
            self.error_occurred.emit(str(e))

class EnhancedMCPAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        self.setWindowTitle("MCP 智能数据分析助手 - 增强版")
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧聊天面板
        chat_panel = self.create_chat_panel()
        splitter.addWidget(chat_panel)
        
        # 右侧数据面板
        self.data_panel = DataDetailsPanel()
        splitter.addWidget(self.data_panel)
        
        # 设置分割比例 (60% 聊天 : 40% 数据)
        splitter.setSizes([840, 560])
        splitter.setChildrenCollapsible(False)
        
        main_layout.addWidget(splitter)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('文件')
        
        new_action = QAction('新建会话', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_session)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_indicator = StatusIndicator()
        self.status_bar.addPermanentWidget(QLabel("状态:"))
        self.status_bar.addPermanentWidget(self.status_indicator)
        
        self.status_bar.showMessage("就绪")
    
    def create_chat_panel(self):
        """创建聊天面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 聊天标题栏
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        chat_title = QLabel("💬 智能对话")
        chat_title.setFont(QFont("微软雅黑", 13, QFont.Bold))
        chat_title.setStyleSheet("color: white;")
        
        header_layout.addWidget(chat_title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 聊天历史区域
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E1E5E9;
                border-radius: 8px;
                background-color: #FAFBFC;
            }
        """)
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        
        self.chat_scroll.setWidget(self.chat_widget)
        layout.addWidget(self.chat_scroll)
        
        # 输入区域
        self.create_input_area(layout)
        
        return panel
    
    def create_input_area(self, parent_layout):
        """创建输入区域"""
        input_frame = QFrame()
        input_frame.setFixedHeight(100)
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #E1E5E9;
                border-radius: 8px;
            }
        """)
        
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 12, 8)
        
        # 输入框
        self.user_input = QTextEdit()
        self.user_input.setFixedHeight(50)
        self.user_input.setPlaceholderText("输入您的问题，例如：全面分析第3批次数据...")
        self.user_input.setFont(QFont("微软雅黑", 11))
        self.user_input.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                padding: 4px;
            }
        """)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.btn_clear = ModernButton("清空")
        self.btn_clear.clicked.connect(self.clear_chat)
        self.btn_clear.setFixedWidth(70)
        
        self.btn_send = ModernButton("发送", primary=True)
        self.btn_send.clicked.connect(self.on_send)
        self.btn_send.setFixedWidth(80)
        
        # 绑定回车键
        self.user_input.keyPressEvent = self.handle_key_press
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_clear)
        button_layout.addWidget(self.btn_send)
        
        input_layout.addWidget(self.user_input)
        input_layout.addLayout(button_layout)
        
        parent_layout.addWidget(input_frame)
    
    def handle_key_press(self, event):
        """处理按键事件"""
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.on_send()
        else:
            QTextEdit.keyPressEvent(self.user_input, event)
    
    def apply_theme(self):
        """应用主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F6FA;
            }
            QMenuBar {
                background-color: white;
                border-bottom: 1px solid #E9ECEF;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
                margin: 2px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #E9ECEF;
            }
            QStatusBar {
                background-color: white;
                border-top: 1px solid #E9ECEF;
            }
        """)
    
    def add_message(self, sender, content, message_type="user"):
        """添加消息"""
        message = ChatMessage(sender, content, message_type)
        self.chat_layout.addWidget(message)
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_send(self):
        """发送消息"""
        user_text = self.user_input.toPlainText().strip()
        if not user_text:
            return
        
        self.add_message("🧑‍💻 您", user_text, "user")
        self.user_input.clear()
        
        self.status_indicator.set_status("thinking")
        self.status_bar.showMessage("🤖 AI正在思考...")
        
        self.btn_send.setEnabled(False)
        self.btn_send.setText("思考中...")
        
        self.messages.append({"role": "user", "content": user_text})
        self.worker = GPTWorker(self.messages)
        self.worker.response_ready.connect(self.handle_gpt_reply)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()
    
    def handle_gpt_reply(self, reply_text):
        """处理GPT回复"""
        try:
            success, fixed_response = FormatFixer.fix_gpt_response(reply_text)
            if not success:
                self.add_message("⚠️ 系统", "GPT返回格式不规范，已自动修复", "tool")
            
            gpt_json = json.loads(fixed_response)
            
            if gpt_json.get("action") == "invoke_tool":
                self.status_bar.showMessage("🛠️ 执行数据分析...")
                tool_result = dispatch_gpt_response(fixed_response)

                if tool_result["type"] == "tool_result":
                    tool_name = tool_result.get("tool")
                    tool_data = tool_result.get("data")
                    
                    # 更新右侧数据面板
                    if tool_name in ["multi_batch_analysis", "time_series_analysis"]:
                        # 处理多批次分析和时间序列分析的特殊情况 - 传递analysis_results内容
                        if "analysis_results" in tool_data:
                            self.data_panel.update_data(tool_data["analysis_results"])
                        else:
                            self.data_panel.update_data(tool_data)
                    elif "analysis_results" in tool_data:
                        self.data_panel.update_data(tool_data["analysis_results"])
                    
                    # 简化显示工具结果
                    tool_summary = f"✅ {tool_name} 分析完成\n"
                    if tool_name == "batch_comparison":
                        # 批次对比的特殊显示
                        if "batch1_metadata" in tool_data and "batch2_metadata" in tool_data:
                            meta1 = tool_data["batch1_metadata"]
                            meta2 = tool_data["batch2_metadata"]
                            tool_summary += f"📁 批次1: {meta1.get('filename', '未知')} ({meta1.get('rows', 0)} 条记录)\n"
                            tool_summary += f"📁 批次2: {meta2.get('filename', '未知')} ({meta2.get('rows', 0)} 条记录)\n"
                            tool_summary += f"💾 详细对比数据已显示在右侧面板"
                    elif tool_name == "multi_batch_analysis":
                        # 多批次分析的特殊显示
                        total_batches = tool_data.get("total_batches", 0)
                        analysis_type = tool_data.get("analysis_type", "")
                        tool_summary += f"📊 分析类型: {analysis_type}\n"
                        tool_summary += f"🗂️ 分析批次数: {total_batches}\n"
                        tool_summary += f"📈 多批次趋势图表已显示在右侧面板"
                    elif tool_name == "time_series_analysis":
                        # 时间序列分析的特殊显示
                        file_metadata = tool_data.get("file_metadata", {})
                        analysis_results = tool_data.get("analysis_results", {})
                        total_points = analysis_results.get("total_data_points", 0)
                        tool_summary += f"📁 文件: {file_metadata.get('filename', '未知')}\n"
                        tool_summary += f"📊 数据点数: {total_points}\n"
                        tool_summary += f"📈 时间序列曲线已显示在右侧面板"
                    elif "file_metadata" in tool_data:
                        meta = tool_data["file_metadata"]
                        tool_summary += f"📁 文件: {meta.get('filename', '未知')}\n"
                        tool_summary += f"📊 数据量: {meta.get('rows', 0)} 条记录\n"
                        tool_summary += f"💾 详细数据已显示在右侧面板"
                    
                    self.add_message("🛠️ 分析工具", tool_summary, "tool")
                    
                    # 继续GPT分析
                    enhanced_message = f"""这是 {tool_name} 工具的返回结果：
{json.dumps(tool_data, ensure_ascii=False, indent=2)}

⚠️ 重要提醒：请分析以上数据并严格按照JSON格式返回分析结果：
{{"action": "analysis_complete", "analysis_summary": {{"data_source": "...", "key_findings": [...], "overall_assessment": "...", "recommendations": [...]}}}}
不要返回纯文本，必须返回可解析的JSON格式。"""
                    
                    self.messages.append({"role": "user", "content": enhanced_message})
                    
                    self.status_bar.showMessage("🧠 AI正在分析结果...")
                    self.worker = GPTWorker(self.messages)
                    self.worker.response_ready.connect(self.handle_gpt_reply)
                    self.worker.error_occurred.connect(self.show_error)
                    self.worker.start()
                    return
                    
            elif gpt_json.get("action") == "analysis_complete":
                summary = gpt_json.get("analysis_summary", {})
                formatted_result = self.format_analysis_summary(summary)
                self.add_message("🤖 AI助手", formatted_result, "assistant")
                
            else:
                content = gpt_json.get("reply", gpt_json.get("content", reply_text))
                self.add_message("🤖 AI助手", content, "assistant")
            
            self.reset_ui_state()
                
        except Exception as e:
            self.show_error(f"解析失败: {e}")
    
    def format_analysis_summary(self, summary):
        """格式化分析摘要"""
        formatted = []
        
        if "data_source" in summary:
            formatted.append(f"📁 数据源: {summary['data_source']}")
        
        if "key_findings" in summary and summary["key_findings"]:
            formatted.append("\n🔍 关键发现:")
            for i, finding in enumerate(summary["key_findings"], 1):
                formatted.append(f"  {i}. {finding}")
        
        if "overall_assessment" in summary:
            formatted.append(f"\n📊 整体评价: {summary['overall_assessment']}")
        
        if "recommendations" in summary and summary["recommendations"]:
            formatted.append("\n💡 建议:")
            for i, rec in enumerate(summary["recommendations"], 1):
                formatted.append(f"  {i}. {rec}")
        
        return "\n".join(formatted) if formatted else "分析完成，但未提供详细摘要。"
    
    def show_error(self, message):
        """显示错误"""
        self.add_message("❌ 错误", message, "error")
        self.reset_ui_state()
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.status_indicator.set_status("ready")
        self.status_bar.showMessage("就绪")
        self.btn_send.setEnabled(True)
        self.btn_send.setText("发送")
    
    def clear_chat(self):
        """清空聊天"""
        for i in reversed(range(self.chat_layout.count())):
            child = self.chat_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        self.messages = []
        self.add_message("🎉 系统", "聊天记录已清空！", "tool")
    
    def new_session(self):
        """新建会话"""
        self.clear_chat()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setApplicationName("数据挖掘系统")
    app.setApplicationVersion("2.1")
    
    window = EnhancedMCPAssistant()
    window.show()
    
    window.add_message("🎉 系统", "数据挖掘系统\n左侧进行智能对话，右侧查看精确的计算结果。", "tool")
    
    sys.exit(app.exec_())