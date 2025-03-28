#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图像视图组件，用于显示3D渲染结果并处理交互事件
"""

import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QImage, QPixmap, QColor, QPalette
from PySide6.QtCore import Qt, QPoint


class ImageViewWidget(QWidget):
    """图像视图组件，显示3D渲染结果并处理交互事件"""
    
    def __init__(self, renderer, parent=None):
        """初始化图像视图组件
        
        Args:
            renderer: 3D渲染器实例
            parent: 父级窗口部件
        """
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.image = None
        self.renderer = renderer  # 存储渲染器引用
        
        # 鼠标跟踪变量
        self.last_pos = None
        self.setMouseTracking(True)
        
        # 编辑模式相关变量
        self.edit_mode = False
        self.edit_tool = None
        self.edit_points = []  # 存储编辑点
        
        # 设置白色背景
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(pal)
        
        # 连接渲染器的点添加信号
        self.renderer.point_added.connect(self.on_point_added)
    
    def set_image(self, img_array):
        """设置要显示的图像
        
        Args:
            img_array (numpy.ndarray): 图像数组
        """
        self.image = img_array
        self.update()
    
    def paintEvent(self, event):
        """绘制事件处理器
        
        Args:
            event: 绘制事件对象
        """
        painter = QPainter(self)
        
        if self.image is not None:
            # 将numpy数组转换为QImage
            height, width, channels = self.image.shape
            bytes_per_line = channels * width
            
            # 从float [0,1]转换为uint8 [0,255]
            img_8bit = (self.image * 255).astype(np.uint8)
            
            # 创建QImage - RGB格式
            qimg = QImage(img_8bit.data, width, height, 
                          bytes_per_line, QImage.Format_RGB888)
            
            # 缩放图像以适应窗口
            pixmap = QPixmap.fromImage(qimg)
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 计算居中位置
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            # 绘制图像
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # 如果在编辑模式下，绘制编辑点
            if self.edit_mode and self.edit_points:
                # 设置绘制样式
                painter.setPen(Qt.red)
                painter.setBrush(Qt.transparent)
                
                # 绘制编辑点
                for point in self.edit_points:
                    painter.drawEllipse(point, 5, 5)
                
                # 如果有多个点，连接它们
                if len(self.edit_points) > 1:
                    for i in range(len(self.edit_points) - 1):
                        painter.drawLine(self.edit_points[i], self.edit_points[i + 1])
        else:
            # 如果没有图像，显示提示文本
            painter.drawText(
                self.rect(), 
                Qt.AlignmentFlag.AlignCenter, 
                "请加载3D模型"
            )
    
    def mousePressEvent(self, event):
        """鼠标按下事件处理器
        
        Args:
            event: 鼠标事件对象
        """
        if self.edit_mode:
            # 在编辑模式下，记录点击位置
            self.edit_points.append(QPoint(event.position().x(), event.position().y()))
            self.update()
        else:
            # 在默认模式下，处理点击生成点
            if event.button() == Qt.MouseButton.LeftButton:
                # 获取点击位置相对于图像的位置
                if self.image is not None:
                    # 计算图像在窗口中的实际位置和大小
                    scaled_width = self.width() * 0.8  # 假设图像宽度为窗口宽度的80%
                    scaled_height = scaled_width * (self.image.shape[0] / self.image.shape[1])
                    x_offset = (self.width() - scaled_width) / 2
                    y_offset = (self.height() - scaled_height) / 2
                    
                    # 计算点击位置相对于图像的位置
                    x = event.position().x() - x_offset
                    y = event.position().y() - y_offset
                    
                    # 将坐标映射到图像尺寸
                    x = int(x * (self.image.shape[1] / scaled_width))
                    y = int(y * (self.image.shape[0] / scaled_height))
                    
                    # 确保坐标在有效范围内
                    if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
                        # 调用渲染器处理点击
                        self.renderer.handle_click(x, y)
            else:
                # 用于旋转/平移视图
                self.last_pos = event.position()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件处理器
        
        Args:
            event: 鼠标事件对象
        """
        if self.edit_mode and event.buttons() & Qt.MouseButton.LeftButton:
            # 在编辑模式下，跟踪鼠标移动以创建编辑路径
            self.edit_points.append(QPoint(event.position().x(), event.position().y()))
            self.update()
        elif self.last_pos is not None:
            # 在默认模式下，处理视图旋转/平移
            curr_pos = event.position()
            dx = curr_pos.x() - self.last_pos.x()
            dy = curr_pos.y() - self.last_pos.y()
            
            # 根据不同按钮进行不同操作
            if event.buttons() & Qt.MouseButton.LeftButton:
                # 左键旋转
                self.renderer.rotate_view(dx, dy)
            elif event.buttons() & Qt.MouseButton.RightButton:
                # 右键平移
                self.renderer.pan_view(dx, dy)
            
            self.last_pos = curr_pos
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件处理器
        
        Args:
            event: 鼠标事件对象
        """
        if self.edit_mode:
            # 在编辑模式下，完成编辑操作
            self.finalize_edit()
        else:
            # 在默认模式下，清除位置跟踪
            self.last_pos = None
    
    def wheelEvent(self, event):
        """鼠标滚轮事件处理器，用于缩放
        
        Args:
            event: 鼠标滚轮事件对象
        """
        if not self.edit_mode:
            delta = event.angleDelta().y()
            # 确保正确的缩放方向
            self.renderer.zoom_view(delta)
    
    def set_edit_mode(self, enabled, tool=None):
        """设置编辑模式
        
        Args:
            enabled (bool): 是否启用编辑模式
            tool (str): 编辑工具类型
        """
        self.edit_mode = enabled
        self.edit_tool = tool
        self.edit_points = []
        self.update()
    
    def finalize_edit(self):
        """完成编辑操作，将编辑结果应用到模型上"""
        if not self.edit_points:
            return
            
        # 在这里可以根据不同的编辑工具实现不同的编辑操作
        # 目前只是一个基本框架，未来可以扩展
        print(f"编辑完成，使用工具: {self.edit_tool}，点数: {len(self.edit_points)}")
        
        # TODO: 实现编辑操作
        # 比如根据屏幕坐标转换为3D坐标，然后修改模型
        
        # 清除编辑点
        self.edit_points = []
        self.update()

    def on_point_added(self, point_3d):
        """处理新点添加事件
        
        Args:
            point_3d (numpy.ndarray): 新添加的3D点坐标
        """
        print(f"添加新点: {point_3d}")
        # 这里可以添加额外的处理逻辑，比如更新UI显示等
