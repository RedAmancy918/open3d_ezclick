#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自定义样式框架组件
"""

from PySide6.QtWidgets import QFrame
from PySide6.QtGui import QColor, QPalette


class StyledFrame(QFrame):
    """带样式的边框框架"""
    
    def __init__(self, parent=None, bg_color=None):
        """初始化样式框架
        
        Args:
            parent: 父级窗口部件
            bg_color (QColor, optional): 背景颜色，默认为浅蓝色
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        
        # 设置背景色
        self.setAutoFillBackground(True)
        pal = self.palette()
        
        if bg_color is None:
            # 默认浅蓝色背景
            bg_color = QColor(240, 248, 255)  # 非常浅的蓝色
            
        pal.setColor(QPalette.Window, bg_color)
        self.setPalette(pal)