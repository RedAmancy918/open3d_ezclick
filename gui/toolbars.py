#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具栏和工具按钮组件
"""

import os
from PySide6.QtWidgets import QToolBar, QToolButton, QButtonGroup
from PySide6.QtGui import QAction
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QSize, Qt


class MainToolBar(QToolBar):
    """主工具栏类"""
    
    # 信号定义
    action_triggered = Signal(str, dict)  # 参数: 动作ID, 附加数据
    
    def __init__(self, parent=None, config=None):
        """初始化主工具栏
        
        Args:
            parent: 父级窗口部件
            config: 配置对象，可选
        """
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QSize(32, 32))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # 保存配置引用
        self.config = config
        
        # 初始化工具按钮
        self._init_tools()
    
    def _init_tools(self):
        """初始化工具按钮"""
        # 创建按钮组，确保只有一个工具处于激活状态
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        
        # 添加导航工具
        self.nav_tool = self._create_tool("nav", "导航", "icons/nav_icon.png", True)
        self.addWidget(self.nav_tool)
        
        # 添加分隔符
        self.addSeparator()
        
        # 添加编辑工具
        self.pen_tool = self._create_tool("pen", "绘制", "icons/pen_icon.png")
        self.addWidget(self.pen_tool)
        
        self.user_tool = self._create_tool("user", "用户", "icons/user_icon.png")
        self.addWidget(self.user_tool)
        
        # 添加3D编辑工具（未来扩展）
        self.addSeparator()
        self.edit3d_tool = self._create_tool("edit3d", "3D编辑", "icons/edit3d_icon.png")
        self.addWidget(self.edit3d_tool)
        
        # 连接信号和槽
        self.tool_group.buttonClicked.connect(self._on_tool_clicked)
    
    def _create_tool(self, tool_id, text, icon_path, checked=False):
        """创建工具按钮
        
        Args:
            tool_id (str): 工具ID
            text (str): 按钮文本
            icon_path (str): 图标路径
            checked (bool, optional): 是否默认选中
            
        Returns:
            QToolButton: 创建的工具按钮
        """
        tool_btn = QToolButton()
        
        # 尝试加载图标，如果不存在则使用默认文本
        icon_full_path = self._get_icon_path(icon_path)
        if os.path.exists(icon_full_path):
            tool_btn.setIcon(QIcon(icon_full_path))
        else:
            # 如果图标不存在，使用文本的第一个字符作为图标文本
            tool_btn.setText(text[0])
        
        tool_btn.setToolTip(text)
        tool_btn.setCheckable(True)
        tool_btn.setChecked(checked)
        tool_btn.setProperty("tool_id", tool_id)
        
        # 添加到按钮组
        self.tool_group.addButton(tool_btn)
        
        return tool_btn
    
    def _get_icon_path(self, icon_path):
        """获取图标的完整路径
        
        Args:
            icon_path (str): 图标相对路径
            
        Returns:
            str: 图标完整路径
        """
        # 如果提供了配置，从配置中获取图标路径
        if self.config:
            base_path = self.config.get_value("paths", "icons", "icons/")
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), base_path, os.path.basename(icon_path))
        else:
            # 否则使用相对路径
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), icon_path)
    
    def _on_tool_clicked(self, button):
        """工具按钮点击回调
        
        Args:
            button: 被点击的按钮
        """
        tool_id = button.property("tool_id")
        is_checked = button.isChecked()
        
        # 触发信号，通知其他组件工具已更改
        self.action_triggered.emit(tool_id, {"checked": is_checked})
