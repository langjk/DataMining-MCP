# launcher.py
# MCP数据分析助手启动器

import sys
from enhanced_gui import EnhancedMCPAssistant
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MCP 数据分析助手")  
    app.setApplicationVersion("3.0")
    
    window = EnhancedMCPAssistant()
    window.show()
    
    window.add_message("🎉 系统", "欢迎使用 MCP 智能数据分析助手！\n左侧进行智能对话，右侧查看精确的计算结果。", "tool")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()