# enhanced_gui.py
# 增强版MCP数据分析助手界面 - 包含数据详情面板

import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QFrame, QScrollArea, QStatusBar, QMenuBar, QAction,
                             QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                             QTreeWidget, QTreeWidgetItem, QHeaderView)
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
        
        # 消息内容
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("微软雅黑", 11))
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        layout.addLayout(header_layout)
        layout.addWidget(content_label)
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
        self.tab_widget.addTab(self.comparison_tab, "⚖️ 批次对比")
        
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
        """创建批次对比标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
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
    
    def update_data(self, analysis_data):
        """更新数据显示"""
        self.current_data = analysis_data
        
        # 清空所有表格
        self.clear_all_tables()
        
        # 检查是否是批次对比结果
        if self._is_batch_comparison_result(analysis_data):
            self.update_comparison_table(analysis_data)
        # 检查是否是单一分析类型的结果（直接返回指标数据）
        elif self._is_single_metric_result(analysis_data):
            # 判断分析类型并更新相应表格
            if self._looks_like_stability_data(analysis_data):
                self.update_stability_table(analysis_data)
            elif self._looks_like_trend_data(analysis_data):
                self.update_trend_table(analysis_data)
            elif self._looks_like_outlier_data(analysis_data):
                self.update_outlier_table(analysis_data)
            elif self._looks_like_stats_data(analysis_data):
                self.update_stats_table(analysis_data)
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
    
    def clear_all_tables(self):
        """清空所有表格数据"""
        self.stats_table.setRowCount(0)
        self.stability_table.setRowCount(0)
        self.trend_table.setRowCount(0)
        self.outlier_table.setRowCount(0)
        self.comparison_table.setRowCount(0)
    
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
                    if "analysis_results" in tool_data:
                        self.data_panel.update_data(tool_data["analysis_results"])
                    
                    # 简化显示工具结果
                    tool_summary = f"✅ {tool_name} 分析完成\n"
                    if "file_metadata" in tool_data:
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
        self.add_message("🎉 系统", "聊天记录已清空，开始新的对话吧！", "tool")
    
    def new_session(self):
        """新建会话"""
        self.clear_chat()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setApplicationName("MCP 数据分析助手 - 增强版")
    app.setApplicationVersion("2.1")
    
    window = EnhancedMCPAssistant()
    window.show()
    
    window.add_message("🎉 系统", "欢迎使用 MCP 智能数据分析助手增强版！\n左侧进行智能对话，右侧查看精确的计算结果。", "tool")
    
    sys.exit(app.exec_())