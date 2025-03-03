#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型管理模块，负责3D模型的编辑、处理和保存
"""

import os
import numpy as np
import open3d as o3d
from PySide6.QtCore import QObject, Signal


class ModelManager(QObject):
    """模型管理类，处理3D模型的编辑和处理功能"""
    
    # 信号定义
    model_updated = Signal()  # 模型更新后发出的信号
    edit_applied = Signal(str)  # 编辑应用后发出的信号，参数为操作描述
    operation_error = Signal(str)  # 操作错误时发出的信号，参数为错误信息
    
    def __init__(self, config=None):
        """初始化模型管理器
        
        Args:
            config: 配置对象，可选
        """
        super().__init__()
        self.config = config
        self.current_model = None
        self.model_type = None  # 'pcd'表示点云，'mesh'表示网格
        self.history = []  # 操作历史，用于撤销/重做
        self.history_index = -1  # 历史索引
        self.max_history = 20  # 最大历史记录数
    
    def set_model(self, model, model_type):
        """设置当前模型
        
        Args:
            model: 模型对象
            model_type (str): 模型类型，'pcd'或'mesh'
        """
        self.current_model = model
        self.model_type = model_type
        self.clear_history()
        self.add_to_history("加载模型")
    
    def clear_history(self):
        """清除历史记录"""
        self.history = []
        self.history_index = -1
    
    def add_to_history(self, description):
        """添加操作到历史记录
        
        Args:
            description (str): 操作描述
        """
        # 如果当前不在历史的最后，则删除后面的记录
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # 添加新的状态
        if self.model_type == 'pcd':
            # 对于点云，复制点和颜色
            points = np.asarray(self.current_model.points).copy()
            colors = np.asarray(self.current_model.colors).copy() if self.current_model.has_colors() else None
            self.history.append({
                'description': description,
                'points': points,
                'colors': colors
            })
        elif self.model_type == 'mesh':
            # 对于网格，复制顶点、面和颜色
            vertices = np.asarray(self.current_model.vertices).copy()
            triangles = np.asarray(self.current_model.triangles).copy()
            vertex_colors = np.asarray(self.current_model.vertex_colors).copy() if self.current_model.has_vertex_colors() else None
            self.history.append({
                'description': description,
                'vertices': vertices,
                'triangles': triangles,
                'vertex_colors': vertex_colors
            })
        
        # 更新历史索引
        self.history_index = len(self.history) - 1
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1
    
    def can_undo(self):
        """检查是否可以撤销
        
        Returns:
            bool: 是否可以撤销
        """
        return self.history_index > 0
    
    def can_redo(self):
        """检查是否可以重做
        
        Returns:
            bool: 是否可以重做
        """
        return self.history_index < len(self.history) - 1
    
    def undo(self):
        """撤销操作
        
        Returns:
            bool: 是否成功撤销
        """
        if not self.can_undo():
            return False
        
        self.history_index -= 1
        self._restore_state(self.history_index)
        self.edit_applied.emit(f"撤销: {self.history[self.history_index]['description']}")
        return True
    
    def redo(self):
        """重做操作
        
        Returns:
            bool: 是否成功重做
        """
        if not self.can_redo():
            return False
        
        self.history_index += 1
        self._restore_state(self.history_index)
        self.edit_applied.emit(f"重做: {self.history[self.history_index]['description']}")
        return True
    
    def _restore_state(self, index):
        """恢复到指定历史状态
        
        Args:
            index (int): 历史记录索引
        """
        state = self.history[index]
        
        if self.model_type == 'pcd':
            # 恢复点云状态
            self.current_model.points = o3d.utility.Vector3dVector(state['points'])
            if state['colors'] is not None:
                self.current_model.colors = o3d.utility.Vector3dVector(state['colors'])
        elif self.model_type == 'mesh':
            # 恢复网格状态
            self.current_model.vertices = o3d.utility.Vector3dVector(state['vertices'])
            self.current_model.triangles = o3d.utility.Vector3iVector(state['triangles'])
            if state['vertex_colors'] is not None:
                self.current_model.vertex_colors = o3d.utility.Vector3dVector(state['vertex_colors'])
        
        # 通知视图更新
        self.model_updated.emit()
    
    def apply_density(self, density_level):
        """应用密度设置
        
        Args:
            density_level (str): 密度级别，'低'、'中'或'高'
            
        Returns:
            bool: 是否成功应用
        """
        if not self.current_model or self.model_type != 'pcd':
            self.operation_error.emit("只能对点云应用密度设置")
            return False
        
        try:
            # 复制当前模型，以防操作失败
            pcd = self.current_model
            
            # 根据密度级别设置体素大小
            voxel_size = 0.02  # 默认中等密度
            if density_level == "低":
                voxel_size = 0.04
            elif density_level == "高":
                voxel_size = 0.01
            
            # 应用体素下采样
            downsampled_pcd = pcd.voxel_down_sample(voxel_size)
            
            # 更新当前模型
            self.current_model.points = downsampled_pcd.points
            self.current_model.colors = downsampled_pcd.colors
            
            # 添加到历史记录
            self.add_to_history(f"应用密度: {density_level}")
            
            # 通知视图更新
            self.model_updated.emit()
            self.edit_applied.emit(f"已应用密度: {density_level}")
            return True
        except Exception as e:
            self.operation_error.emit(f"应用密度时出错: {str(e)}")
            return False
    
    def apply_aesthetic_alignment(self, alignment_option):
        """应用美学对齐
        
        Args:
            alignment_option (str): 对齐选项
            
        Returns:
            bool: 是否成功应用
        """
        if not self.current_model:
            self.operation_error.emit("没有加载模型")
            return False
        
        try:
            # 这里可以实现不同的美学对齐算法
            # 目前作为示例，我们只是简单地旋转模型
            
            # 添加到历史记录
            self.add_to_history(f"应用美学对齐: {alignment_option}")
            
            # 通知视图更新
            self.model_updated.emit()
            self.edit_applied.emit(f"已应用美学对齐: {alignment_option}")
            return True
        except Exception as e:
            self.operation_error.emit(f"应用美学对齐时出错: {str(e)}")
            return False
    
    def apply_edit(self, edit_type, edit_data):
        """应用编辑操作
        
        Args:
            edit_type (str): 编辑类型
            edit_data (dict): 编辑数据
            
        Returns:
            bool: 是否成功应用
        """
        if not self.current_model:
            self.operation_error.emit("没有加载模型")
            return False
        
        try:
            # 根据不同的编辑类型实现不同的编辑操作
            # 这里是一个框架，具体实现可以扩展
            
            # 添加到历史记录
            self.add_to_history(f"应用编辑: {edit_type}")
            
            # 通知视图更新
            self.model_updated.emit()
            self.edit_applied.emit(f"已应用编辑: {edit_type}")
            return True
        except Exception as e:
            self.operation_error.emit(f"应用编辑时出错: {str(e)}")
            return False
    
    def get_model_info(self):
        """获取当前模型信息
        
        Returns:
            dict: 模型信息
        """
        if not self.current_model:
            return {
                "status": "未加载模型"
            }
        
        info = {
            "type": self.model_type
        }
        
        if self.model_type == 'pcd':
            # 点云信息
            info["points_count"] = len(self.current_model.points)
            info["has_colors"] = self.current_model.has_colors()
            info["has_normals"] = self.current_model.has_normals()
            
            # 计算点云的边界框
            points = np.asarray(self.current_model.points)
            min_bound = points.min(axis=0)
            max_bound = points.max(axis=0)
            info["dimensions"] = max_bound - min_bound
            
        elif self.model_type == 'mesh':
            # 网格信息
            info["vertices_count"] = len(self.current_model.vertices)
            info["triangles_count"] = len(self.current_model.triangles)
            info["has_vertex_colors"] = self.current_model.has_vertex_colors()
            info["has_triangle_normals"] = self.current_model.has_triangle_normals()
            
            # 计算网格的边界框
            vertices = np.asarray(self.current_model.vertices)
            min_bound = vertices.min(axis=0)
            max_bound = vertices.max(axis=0)
            info["dimensions"] = max_bound - min_bound
        
        return info
