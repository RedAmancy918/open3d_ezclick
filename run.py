#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
3D模型可视化与编辑程序的主入口文件
Hair Ezclick应用程序
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from gui.main_window import MainWindow
from utils.config_manager import ConfigManager


def main():
    """主程序入口"""
    # 加载配置
    config = ConfigManager()
    config.load_config()
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 设置应用程序全局字体
    font = QFont("Microsoft YaHei", 9)  # 使用微软雅黑字体
    app.setFont(font)
    
    # 创建并显示主窗口
    main_window = MainWindow(config)
    main_window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
