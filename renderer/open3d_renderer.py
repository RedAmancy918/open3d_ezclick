#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Open3D渲染器模块，负责3D模型的渲染和视图操作
"""

import open3d as o3d
import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal


class Open3DRenderer(QObject):
    """Open3D渲染器类，用于渲染3D模型并提供视图交互功能"""
    
    # 信号定义
    render_ready = Signal(np.ndarray)
    model_loaded = Signal(bool, str)  # 参数: 是否成功, 信息
    point_added = Signal(np.ndarray)  # 新增：当添加新点时发出信号
    
    def __init__(self, config=None):
        """初始化Open3D渲染器
        
        Args:
            config: 配置对象，可选
        """
        super().__init__()
        
        # 配置参数
        self.width = 800
        self.height = 600
        self.background_color = np.array([1, 1, 1])  # 白色背景
        self.point_size = 2.0
        self.click_points = []  # 存储点击生成的点
        self.click_point_cloud = None  # 存储点击生成的点云对象
        
        # 如果提供了配置，从配置中加载参数
        if config:
            self.width = config.get_value("renderer", "width", 800)
            self.height = config.get_value("renderer", "height", 600)
            self.background_color = np.array(config.get_value("renderer", "background_color", [1, 1, 1]))
            self.point_size = config.get_value("renderer", "point_size", 2.0)
            
            # 视图设置
            self.zoom = config.get_value("view", "zoom", 0.8)
            self.front = config.get_value("view", "front", [0, 0, -1])
            self.up = config.get_value("view", "up", [0, 1, 0])
        else:
            self.zoom = 0.8
            self.front = [0, 0, -1]
            self.up = [0, 1, 0]
        
        self.vis = o3d.visualization.Visualizer()
        # 创建一个不可见的窗口用于渲染
        self.vis.create_window(visible=False, width=self.width, height=self.height)
        
        # 设置渲染选项
        opt = self.vis.get_render_option()
        opt.background_color = self.background_color
        opt.point_size = self.point_size
        
        # 设置视图控制
        view = self.vis.get_view_control()
        view.set_zoom(self.zoom)
        view.set_front(self.front)
        view.set_up(self.up)
        
        # 初始化渲染定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_render)
        self.timer.start(50)  # 20fps
        
        self.geometry_loaded = False
        self.current_model = None  # 存储当前加载的模型对象引用
        self.current_model_path = None  # 存储当前模型文件路径
    
    def update_render(self):
        """更新渲染"""
        if self.geometry_loaded:
            self.vis.poll_events()
            self.vis.update_renderer()
            # 捕获渲染的图像
            img = self.vis.capture_screen_float_buffer(do_render=True)
            if img is not None:
                # 转换为numpy数组并发送信号
                img_np = np.asarray(img)
                self.render_ready.emit(img_np)
    
    def set_geometry(self, file_path):
        """加载3D文件并设置到可视化器中
        
        Args:
            file_path (str): 3D模型文件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.geometry_loaded = False
            self.vis.clear_geometries()
            self.current_model_path = file_path
            
            if file_path.endswith('.pcd'):
                return self._load_point_cloud(file_path)
            elif file_path.endswith(('.obj', '.ply')):
                return self._load_mesh(file_path)
            else:
                self.model_loaded.emit(False, "不支持的文件格式")
                return False
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.model_loaded.emit(False, f"加载文件错误: {str(e)}")
            return False
    
    def _load_point_cloud(self, file_path):
        """加载点云文件
        
        Args:
            file_path (str): 点云文件路径
            
        Returns:
            bool: 是否成功加载
        """
        print(f"尝试加载点云: {file_path}")
        pcd = o3d.io.read_point_cloud(file_path)
        if len(pcd.points) == 0:
            self.model_loaded.emit(False, "加载失败: 点云为空")
            return False
        
        # 为点云添加颜色(如果没有)
        if not pcd.has_colors():
            # 使用基于高度的彩虹渐变色，以便更好地可视化
            points = np.asarray(pcd.points)
            min_z = np.min(points[:, 2])
            max_z = np.max(points[:, 2])
            colors = np.zeros((len(points), 3))
            for i in range(len(points)):
                normalized = (points[i, 2] - min_z) / (max_z - min_z)
                # 使用更明亮的渐变色
                if normalized < 0.2:
                    colors[i] = [0, 0, 0.8 + normalized]  # 深蓝到蓝
                elif normalized < 0.4:
                    colors[i] = [0, 2 * (normalized - 0.2), 1]  # 蓝到青
                elif normalized < 0.6:
                    colors[i] = [0, 1, 1 - 2 * (normalized - 0.4)]  # 青到绿
                elif normalized < 0.8:
                    colors[i] = [2 * (normalized - 0.6), 1, 0]  # 绿到黄
                else:
                    colors[i] = [1, 1 - 5 * (normalized - 0.8), 0]  # 黄到红
            pcd.colors = o3d.utility.Vector3dVector(colors)
        
        added = self.vis.add_geometry(pcd)
        if not added:
            self.model_loaded.emit(False, "添加几何体到可视化器失败")
            return False
        
        self.current_model = pcd
        self.geometry_loaded = True
        self.model_loaded.emit(True, f"点云加载成功，点数: {len(pcd.points)}")
        
        # 重置视图
        self.vis.reset_view_point(True)
        return True
    
    def _load_mesh(self, file_path):
        """加载网格文件
        
        Args:
            file_path (str): 网格文件路径
            
        Returns:
            bool: 是否成功加载
        """
        print(f"尝试加载网格: {file_path}")
        mesh = o3d.io.read_triangle_mesh(file_path)
        if mesh.is_empty():
            self.model_loaded.emit(False, "加载失败: 网格为空")
            return False
        
        if not mesh.has_vertex_colors():
            mesh.paint_uniform_color([0.7, 0.7, 0.7])
            
        # 确保有法线
        if not mesh.has_triangle_normals():
            mesh.compute_triangle_normals()
        
        added = self.vis.add_geometry(mesh)
        if not added:
            self.model_loaded.emit(False, "添加几何体到可视化器失败")
            return False
        
        self.current_model = mesh
        self.geometry_loaded = True
        self.model_loaded.emit(True, f"网格加载成功，顶点数: {len(mesh.vertices)}")
        
        # 重置视图
        self.vis.reset_view_point(True)
        return True
    
    def rotate_view(self, dx, dy):
        """旋转视图
        
        Args:
            dx (float): X方向旋转量
            dy (float): Y方向旋转量
        """
        ctr = self.vis.get_view_control()
        ctr.rotate(dx, dy)
    
    def pan_view(self, dx, dy):
        """平移视图
        
        Args:
            dx (float): X方向平移量
            dy (float): Y方向平移量
        """
        ctr = self.vis.get_view_control()
        ctr.translate(dx, dy)
    
    def zoom_view(self, dy):
        """缩放视图
        
        Args:
            dy (float): 缩放量
        """
        ctr = self.vis.get_view_control()
        # Open3D中，scale值小于1表示放大，大于1表示缩小
        # 这与直觉相反，所以我们需要反转逻辑
        if dy > 0:
            # 向前滚动 - 放大（在Open3D中使用小于1的值）
            ctr.scale(0.9)
        else:
            # 向后滚动 - 缩小（在Open3D中使用大于1的值）
            ctr.scale(1.1)
    
    def save_model(self, file_path):
        """保存当前模型到文件
        
        Args:
            file_path (str): 保存路径
            
        Returns:
            bool: 是否成功保存
            str: 成功或错误信息
        """
        if not self.current_model:
            return False, "没有模型可保存"
        
        try:
            # 根据文件类型决定保存方法
            if file_path.endswith('.pcd'):
                o3d.io.write_point_cloud(file_path, self.current_model)
            elif file_path.endswith('.ply'):
                o3d.io.write_triangle_mesh(file_path, self.current_model)
            elif file_path.endswith('.obj'):
                o3d.io.write_triangle_mesh(file_path, self.current_model)
            else:
                return False, "不支持的文件格式"
            
            return True, "模型保存成功"
        except Exception as e:
            return False, f"保存模型时出错: {str(e)}"
    
    def set_background_color(self, color):
        """设置背景颜色
        
        Args:
            color (list): RGB颜色值，范围[0,1]
        """
        opt = self.vis.get_render_option()
        opt.background_color = np.array(color)
    
    def set_point_size(self, size):
        """设置点大小
        
        Args:
            size (float): 点大小
        """
        opt = self.vis.get_render_option()
        opt.point_size = size
    
    def get_current_model(self):
        """获取当前模型对象
        
        Returns:
            object: 当前模型对象
        """
        return self.current_model
    
    def cleanup(self):
        """清理资源"""
        self.timer.stop()
        self.vis.destroy_window()

    def handle_click(self, x, y):
        """处理鼠标点击事件
        
        Args:
            x (int): 点击的x坐标
            y (int): 点击的y坐标
        """
        if not self.geometry_loaded or self.current_model is None:
            return
            
        # 获取深度缓冲
        depth = self.vis.capture_depth_float_buffer(do_render=True)
        if depth is None:
            return
            
        # 获取点击位置的深度值
        depth_value = depth[y, x]
        if depth_value == 1.0:  # 如果点击在背景上
            return
            
        # 获取相机参数
        view_control = self.vis.get_view_control()
        camera_params = view_control.convert_to_pinhole_camera_parameters()
        
        # 将屏幕坐标转换为3D点
        intrinsic = camera_params.intrinsic.intrinsic_matrix
        extrinsic = camera_params.extrinsic
        
        # 计算3D点坐标
        z = depth_value
        x_3d = (x - intrinsic[0, 2]) * z / intrinsic[0, 0]
        y_3d = (y - intrinsic[1, 2]) * z / intrinsic[1, 1]
        point_3d = np.array([x_3d, y_3d, z])
        
        # 转换到世界坐标系
        point_3d = np.dot(extrinsic[:3, :3], point_3d) + extrinsic[:3, 3]
        
        # 添加新点到点云
        self.click_points.append(point_3d)
        
        # 创建或更新点击点云
        if self.click_point_cloud is None:
            self.click_point_cloud = o3d.geometry.PointCloud()
            self.click_point_cloud.points = o3d.utility.Vector3dVector(self.click_points)
            self.click_point_cloud.paint_uniform_color([1, 0, 0])  # 红色
            self.vis.add_geometry(self.click_point_cloud)
        else:
            self.click_point_cloud.points = o3d.utility.Vector3dVector(self.click_points)
            self.vis.update_geometry(self.click_point_cloud)
        
        # 发送信号通知新点已添加
        self.point_added.emit(point_3d)
