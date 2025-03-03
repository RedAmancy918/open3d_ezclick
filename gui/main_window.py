#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主窗口模块，负责创建和管理应用程序的主窗口界面
"""

import os
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QDockWidget, 
                              QFileDialog, QMessageBox, QStatusBar)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Slot, QSize

from gui.viewport import Viewport3D
from gui.toolbars import MainToolBar
from gui.sidebar import PropertiesPanel, ControlPanel
from gui.styled_frame import StyledFrame
from utils.model_manager import ModelManager
from utils.data_interface import DataInterface


class MainWindow(QMainWindow):
    """应用程序的主窗口类"""
    
    def __init__(self, config=None):
        """初始化主窗口
        
        Args:
            config: 应用程序配置对象，可选
        """
        super().__init__()
        
        self.config = config
        self.model_manager = ModelManager(config)
        self.data_interface = DataInterface(config)
        
        # 设置窗口属性
        self.setWindowTitle(config.get_value("window", "title", "Hair Ezclick") if config else "Hair Ezclick")
        self.resize(
            config.get_value("window", "width", 1200) if config else 1200,
            config.get_value("window", "height", 800) if config else 800
        )
        
        # 设置应用程序全局样式表
        self._set_stylesheet()
        
        # 初始化UI组件
        self._init_ui()
        self._create_actions()
        self._create_menus()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 连接信号和槽
        self._connect_signals()
    
    def _set_stylesheet(self):
        """设置应用程序样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QComboBox {
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 5px;
                min-width: 6em;
            }
            QPushButton {
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 8px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton {
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 10px;
                background-color: #f8f8f8;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
                border: 2px solid #808080;
            }
            QToolButton:hover {
                background-color: #e8e8e8;
            }
            QLabel {
                font-size: 14px;
            }
        """)
    
    def _init_ui(self):
        """初始化UI组件"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 创建工具栏
        self.main_toolbar = MainToolBar(self, self.config)
        self.addToolBar(self.main_toolbar)
        
        # 创建左侧控制面板
        self.left_panel = StyledFrame()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建控制面板并添加到左侧面板
        self.control_panel = ControlPanel()
        self.left_layout.addWidget(self.control_panel)
        
        # 创建中间视图面板
        self.center_panel = StyledFrame()
        self.center_layout = QVBoxLayout(self.center_panel)
        self.center_layout.setContentsMargins(1, 1, 1, 1)  # 减小内边距
        
        # 创建3D视口并添加到中间面板
        self.viewport = Viewport3D(self.model_manager, self.config)
        self.center_layout.addWidget(self.viewport)
        
        # 创建右侧属性面板
        self.right_panel = StyledFrame()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建属性面板并添加到右侧面板
        self.properties_panel = PropertiesPanel(self.model_manager)
        self.right_layout.addWidget(self.properties_panel)
        
        # 将所有面板添加到主布局
        main_layout.addWidget(self.left_panel, 1)
        main_layout.addWidget(self.center_panel, 4)
        main_layout.addWidget(self.right_panel, 1)
    
    def _create_actions(self):
        """创建菜单动作"""
        # 文件菜单动作
        self.open_action = QAction("加载3D模型", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.load_file)
        
        self.save_action = QAction("保存模型", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)
        
        self.export_action = QAction("导出模型", self)
        self.export_action.triggered.connect(self.export_file)
        
        self.exit_action = QAction("退出", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        
        # 编辑菜单动作
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.undo)
        
        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.redo)
        
        # 视图菜单动作
        self.reset_view_action = QAction("重置视图", self)
        self.reset_view_action.triggered.connect(self.reset_view)
        
        # 连接到后端的动作
        self.connect_backend_action = QAction("连接到后端", self)
        self.connect_backend_action.triggered.connect(self.connect_to_backend)
    
    def _create_menus(self):
        """创建菜单"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # 编辑菜单
        edit_menu = self.menuBar().addMenu("编辑")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        
        # 视图菜单
        view_menu = self.menuBar().addMenu("视图")
        view_menu.addAction(self.reset_view_action)
        
        # 工具菜单
        tools_menu = self.menuBar().addMenu("工具")
        
        # 后端菜单
        backend_menu = self.menuBar().addMenu("后端")
        backend_menu.addAction(self.connect_backend_action)
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 工具栏信号
        self.main_toolbar.action_triggered.connect(self.handle_toolbar_action)
        
        # 控制面板信号
        self.control_panel.tool_activated.connect(self.handle_tool_activated)
        
        # 属性面板信号
        self.properties_panel.density_changed.connect(self.handle_density_changed)
        self.properties_panel.alignment_changed.connect(self.handle_alignment_changed)
        self.properties_panel.confirm_clicked.connect(self.handle_confirm)
        
        # 模型管理器信号
        self.model_manager.edit_applied.connect(self.handle_edit_applied)
        self.model_manager.operation_error.connect(self.handle_operation_error)
        
        # 数据接口信号
        self.data_interface.model_received.connect(self.handle_model_received)
        self.data_interface.connection_error.connect(self.handle_connection_error)
        self.data_interface.processing_complete.connect(self.handle_processing_complete)
    
    def load_file(self):
        """打开文件选择对话框并加载3D文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            '打开3D文件', 
            '', 
            '3D文件 (*.pcd *.obj *.ply)'
        )
        
        if file_path:
            self.statusBar().showMessage(f"正在加载模型...")
            
            success = self.viewport.load_model(file_path)
            
            if success:
                file_name = os.path.basename(file_path)
                self.statusBar().showMessage(f'已加载: {file_name}')
            else:
                self.statusBar().showMessage('加载失败')
    
    def save_file(self):
        """保存当前模型"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '保存模型',
            '',
            '点云文件 (*.pcd);;网格文件 (*.ply *.obj)'
        )
        
        if file_path:
            # 获取渲染器实例
            renderer = self.viewport.renderer
            
            # 尝试保存模型
            success, message = renderer.save_model(file_path)
            
            if success:
                self.statusBar().showMessage(f"模型已保存到: {file_path}")
            else:
                QMessageBox.warning(self, "保存失败", message)
                self.statusBar().showMessage("保存失败")
    
    def export_file(self):
        """导出当前模型"""
        # 目前与保存功能相同，未来可以扩展为支持更多格式
        self.save_file()
    
    def undo(self):
        """撤销操作"""
        if self.model_manager.can_undo():
            self.model_manager.undo()
            self.statusBar().showMessage("已撤销")
        else:
            self.statusBar().showMessage("无法撤销")
    
    def redo(self):
        """重做操作"""
        if self.model_manager.can_redo():
            self.model_manager.redo()
            self.statusBar().showMessage("已重做")
        else:
            self.statusBar().showMessage("无法重做")
    
    def reset_view(self):
        """重置视图"""
        # 重新加载当前模型以重置视图
        if self.viewport.renderer.current_model_path:
            self.viewport.load_model(self.viewport.renderer.current_model_path)
            self.statusBar().showMessage("视图已重置")
    
    def connect_to_backend(self):
        """连接到后端服务"""
        self.statusBar().showMessage("正在连接到后端...")
        
        # 尝试连接到后端
        success, message = self.data_interface.connect_to_backend()
        
        if success:
            QMessageBox.information(self, "连接成功", "已成功连接到后端服务")
            self.statusBar().showMessage("已连接到后端")
        else:
            QMessageBox.warning(self, "连接失败", f"无法连接到后端: {message}")
            self.statusBar().showMessage("连接到后端失败")
    
    @Slot(str, dict)
    def handle_toolbar_action(self, action_id, data):
        """处理工具栏动作
        
        Args:
            action_id (str): 动作ID
            data (dict): 附加数据
        """
        is_checked = data.get("checked", False)
        
        if action_id == "nav":
            # 导航工具 - 禁用编辑模式
            self.viewport.set_edit_mode(False)
            self.statusBar().showMessage("导航模式")
        elif action_id == "pen":
            # 绘制工具 - 启用编辑模式
            self.viewport.set_edit_mode(is_checked, "pen")
            state = "激活" if is_checked else "取消激活"
            self.statusBar().showMessage(f"绘制工具 {state}")
        elif action_id == "user":
            # 用户工具 - 启用编辑模式
            self.viewport.set_edit_mode(is_checked, "user")
            state = "激活" if is_checked else "取消激活"
            self.statusBar().showMessage(f"用户工具 {state}")
        elif action_id == "edit3d":
            # 3D编辑工具 - 启用编辑模式
            self.viewport.set_edit_mode(is_checked, "edit3d")
            state = "激活" if is_checked else "取消激活"
            self.statusBar().showMessage(f"3D编辑工具 {state}")
    
    @Slot(str)
    def handle_tool_activated(self, tool_id):
        """处理工具激活
        
        Args:
            tool_id (str): 工具ID
        """
        # 同步工具栏按钮状态
        # 这里可以实现更多逻辑
        pass
    
    @Slot(str)
    def handle_density_changed(self, density):
        """处理密度更改
        
        Args:
            density (str): 密度选项
        """
        print(f"密度更改为: {density}")
    
    @Slot(str)
    def handle_alignment_changed(self, alignment):
        """处理对齐选项更改
        
        Args:
            alignment (str): 对齐选项
        """
        print(f"对齐选项更改为: {alignment}")
    
    @Slot()
    def handle_confirm(self):
        """处理确认按钮点击"""
        # 获取当前面板设置
        settings = self.properties_panel.get_current_settings()
        
        # 应用密度设置
        self.model_manager.apply_density(settings["density"])
        
        # 应用美学对齐
        self.model_manager.apply_aesthetic_alignment(settings["alignment"])
        
        self.statusBar().showMessage("已应用设置")
    
    @Slot(str)
    def handle_edit_applied(self, message):
        """处理编辑应用
        
        Args:
            message (str): 编辑应用消息
        """
        self.statusBar().showMessage(message)
    
    @Slot(str)
    def handle_operation_error(self, message):
        """处理操作错误
        
        Args:
            message (str): 错误消息
        """
        QMessageBox.warning(self, "操作错误", message)
        self.statusBar().showMessage(f"错误: {message}")
    
    @Slot(str)
    def handle_model_received(self, file_path):
        """处理从后端接收到的模型
        
        Args:
            file_path (str): 模型文件路径
        """
        self.viewport.load_model(file_path)
        self.statusBar().showMessage(f"已加载来自后端的模型")
    
    @Slot(str)
    def handle_connection_error(self, message):
        """处理连接错误
        
        Args:
            message (str): 错误消息
        """
        QMessageBox.warning(self, "连接错误", message)
        self.statusBar().showMessage(f"连接错误: {message}")
    
    @Slot(dict)
    def handle_processing_complete(self, result):
        """处理后端处理完成
        
        Args:
            result (dict): 处理结果
        """
        # 处理后端返回的结果
        if "model_id" in result:
            # 尝试获取处理后的模型
            self.data_interface.get_model_from_backend(result["model_id"])
        
        self.statusBar().showMessage("后端处理完成")
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        Args:
            event: 关闭事件对象
        """
        # 清理资源
        self.viewport.cleanup()
        
        # 调用父类方法
        super().closeEvent(event)
