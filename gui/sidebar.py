#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
侧边栏组件，包括属性面板和控制面板
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, 
                              QPushButton, QGroupBox, QFormLayout, QSpinBox, 
                              QLineEdit, QScrollArea, QSizePolicy)
from PySide6.QtCore import Signal


class PropertiesPanel(QWidget):
    """属性面板组件，用于显示和编辑模型属性"""
    
    # 信号定义
    density_changed = Signal(str)
    alignment_changed = Signal(str)
    confirm_clicked = Signal()
    
    def __init__(self, model_manager, parent=None):
        """初始化属性面板
        
        Args:
            model_manager: 模型管理器对象
            parent: 父级窗口部件
        """
        super().__init__(parent)
        self.model_manager = model_manager
        
        # 创建滚动区域以支持更多控件
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容窗口部件
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 模型信息组
        info_group = self._create_info_group()
        layout.addWidget(info_group)
        
        # 密度设置组
        density_group = self._create_density_group()
        layout.addWidget(density_group)
        
        # 美学对齐组
        align_group = self._create_align_group()
        layout.addWidget(align_group)
        
        # 添加编辑设置组（为未来的3D编辑功能预留）
        edit_group = self._create_edit_group()
        layout.addWidget(edit_group)
        
        # 确认按钮
        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self._on_confirm)
        layout.addWidget(self.confirm_button)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # 连接模型管理器信号
        self.model_manager.model_updated.connect(self.update_info)
    
    def _create_info_group(self):
        """创建模型信息组
        
        Returns:
            QGroupBox: 模型信息组
        """
        group = QGroupBox("模型信息")
        layout = QFormLayout(group)
        
        self.model_type_label = QLabel("未加载")
        self.vertices_count_label = QLabel("-")
        self.dimensions_label = QLabel("-")
        
        layout.addRow("类型:", self.model_type_label)
        layout.addRow("顶点/点数:", self.vertices_count_label)
        layout.addRow("尺寸:", self.dimensions_label)
        
        return group
    
    def _create_density_group(self):
        """创建密度设置组
        
        Returns:
            QGroupBox: 密度设置组
        """
        group = QGroupBox("密度")
        layout = QVBoxLayout(group)
        
        self.density_combo = QComboBox()
        self.density_combo.addItems(["低", "中", "高"])
        self.density_combo.setCurrentText("中")
        self.density_combo.currentTextChanged.connect(self._on_density_changed)
        
        layout.addWidget(self.density_combo)
        
        return group
    
    def _create_align_group(self):
        """创建美学对齐组
        
        Returns:
            QGroupBox: 美学对齐组
        """
        group = QGroupBox("美学对齐")
        layout = QVBoxLayout(group)
        
        self.align_combo = QComboBox()
        self.align_combo.addItems(["选项1", "选项2", "选项3"])
        self.align_combo.currentTextChanged.connect(self._on_alignment_changed)
        
        layout.addWidget(self.align_combo)
        
        return group
    
    def _create_edit_group(self):
        """创建编辑设置组
        
        Returns:
            QGroupBox: 编辑设置组
        """
        group = QGroupBox("编辑设置")
        layout = QFormLayout(group)
        
        self.brush_size_spin = QSpinBox()
        self.brush_size_spin.setRange(1, 100)
        self.brush_size_spin.setValue(10)
        self.brush_size_spin.setSuffix(" px")
        
        self.edit_intensity_spin = QSpinBox()
        self.edit_intensity_spin.setRange(1, 100)
        self.edit_intensity_spin.setValue(50)
        self.edit_intensity_spin.setSuffix(" %")
        
        layout.addRow("笔刷大小:", self.brush_size_spin)
        layout.addRow("编辑强度:", self.edit_intensity_spin)
        
        return group
    
    def _on_density_changed(self, text):
        """密度更改回调
        
        Args:
            text (str): 选择的密度选项
        """
        self.density_changed.emit(text)
    
    def _on_alignment_changed(self, text):
        """对齐选项更改回调
        
        Args:
            text (str): 选择的对齐选项
        """
        self.alignment_changed.emit(text)
    
    def _on_confirm(self):
        """确认按钮点击回调"""
        self.confirm_clicked.emit()
    
    def update_info(self):
        """更新模型信息显示"""
        info = self.model_manager.get_model_info()
        
        if "type" in info:
            self.model_type_label.setText("点云" if info["type"] == "pcd" else "网格")
            
            if info["type"] == "pcd":
                self.vertices_count_label.setText(str(info.get("points_count", "-")))
            else:
                self.vertices_count_label.setText(str(info.get("vertices_count", "-")))
            
            if "dimensions" in info:
                dims = info["dimensions"]
                self.dimensions_label.setText(f"{dims[0]:.2f} x {dims[1]:.2f} x {dims[2]:.2f}")
        else:
            self.model_type_label.setText("未加载")
            self.vertices_count_label.setText("-")
            self.dimensions_label.setText("-")
    
    def get_current_settings(self):
        """获取当前面板设置
        
        Returns:
            dict: 当前设置
        """
        return {
            "density": self.density_combo.currentText(),
            "alignment": self.align_combo.currentText(),
            "brush_size": self.brush_size_spin.value(),
            "edit_intensity": self.edit_intensity_spin.value()
        }


class ControlPanel(QWidget):
    """控制面板组件，包含其他不适合放在属性面板的控件"""
    
    # 信号定义
    tool_activated = Signal(str)
    
    def __init__(self, parent=None):
        """初始化控制面板
        
        Args:
            parent: 父级窗口部件
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 工具标签
        self.tool_label = QLabel("工具")
        self.tool_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.tool_label)
        
        # 添加工具按钮
        self.pen_button = QPushButton("绘制工具")
        self.pen_button.setCheckable(True)
        self.pen_button.clicked.connect(lambda checked: self._on_tool_activated("pen", checked))
        layout.addWidget(self.pen_button)
        
        self.user_button = QPushButton("用户工具")
        self.user_button.setCheckable(True)
        self.user_button.clicked.connect(lambda checked: self._on_tool_activated("user", checked))
        layout.addWidget(self.user_button)
        
        # 添加3D编辑工具按钮（未来扩展）
        self.edit3d_button = QPushButton("3D编辑工具")
        self.edit3d_button.setCheckable(True)
        self.edit3d_button.clicked.connect(lambda checked: self._on_tool_activated("edit3d", checked))
        layout.addWidget(self.edit3d_button)
        
        # 添加连接后端按钮
        layout.addSpacing(20)
        self.connect_button = QPushButton("连接到后端")
        self.connect_button.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_button)
        
        # 添加弹性空间
        layout.addStretch()
    
    def _on_tool_activated(self, tool_id, checked):
        """工具激活回调
        
        Args:
            tool_id (str): 工具ID
            checked (bool): 是否激活
        """
        # 如果激活了一个工具，取消其他工具的选中状态
        if checked:
            if tool_id != "pen":
                self.pen_button.setChecked(False)
            if tool_id != "user":
                self.user_button.setChecked(False)
            if tool_id != "edit3d":
                self.edit3d_button.setChecked(False)
            
            # 发出信号
            self.tool_activated.emit(tool_id)
    
    def _on_connect_clicked(self):
        """连接后端按钮点击回调"""
        # 这里可以实现连接后端的逻辑，或者触发一个信号
        print("连接到后端")
