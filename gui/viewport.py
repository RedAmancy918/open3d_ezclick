#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
3D视口组件，整合图像显示和渲染器
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Slot

from gui.image_view_widget import ImageViewWidget
from renderer.open3d_renderer import Open3DRenderer


class Viewport3D(QWidget):
    """3D视口组件，封装了渲染器和图像显示控件"""
    
    def __init__(self, model_manager, config=None, parent=None):
        """初始化3D视口
        
        Args:
            model_manager: 模型管理器对象
            config: 配置对象，可选
            parent: 父级窗口部件
        """
        super().__init__(parent)
        self.model_manager = model_manager
        self.config = config
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建渲染器
        self.renderer = Open3DRenderer(config)
        
        # 创建图像显示控件
        self.image_view = ImageViewWidget(self.renderer)
        self.renderer.render_ready.connect(self.image_view.set_image)
        
        # 添加到布局
        layout.addWidget(self.image_view)
        
        # 连接信号和槽
        self.renderer.model_loaded.connect(self._on_model_loaded)
        self.model_manager.model_updated.connect(self._on_model_updated)
    
    def load_model(self, file_path):
        """加载3D模型文件
        
        Args:
            file_path (str): 模型文件路径
            
        Returns:
            bool: 是否成功加载
        """
        success = self.renderer.set_geometry(file_path)
        
        if success:
            # 根据文件扩展名确定模型类型
            if file_path.endswith('.pcd'):
                model_type = 'pcd'
            else:
                model_type = 'mesh'
            
            # 将当前模型设置到模型管理器
            self.model_manager.set_model(self.renderer.get_current_model(), model_type)
        
        return success
    
    def set_edit_mode(self, enabled, tool=None):
        """设置编辑模式
        
        Args:
            enabled (bool): 是否启用编辑模式
            tool (str): 编辑工具类型
        """
        self.image_view.set_edit_mode(enabled, tool)
    
    @Slot(bool, str)
    def _on_model_loaded(self, success, message):
        """模型加载回调
        
        Args:
            success (bool): 是否成功加载
            message (str): 加载消息
        """
        print(f"模型加载: {'成功' if success else '失败'} - {message}")
    
    @Slot()
    def _on_model_updated(self):
        """模型更新回调，刷新渲染"""
        # 模型已更新，需要刷新渲染
        # 由于Open3D渲染器直接引用了模型对象，这里不需要额外操作
        pass
    
    def cleanup(self):
        """清理资源"""
        self.renderer.cleanup()
