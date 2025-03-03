import sys
import os
import open3d as o3d
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QComboBox, QLabel, QGroupBox, QSplitter
from PySide6.QtCore import Qt, QTimer, Signal, QObject

# Open3D渲染器类
class Open3DRenderer(QObject):
    render_ready = Signal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.vis = o3d.visualization.Visualizer()
        # 创建一个不可见的窗口用于渲染
        self.vis.create_window(visible=False, width=800, height=600)
        
        # 设置渲染选项
        opt = self.vis.get_render_option()
        opt.background_color = np.array([0.1, 0.1, 0.1])  # 深灰色背景
        opt.point_size = 2.0  # 增大点的大小
        
        # 设置视图控制
        view = self.vis.get_view_control()
        view.set_zoom(0.8)
        view.set_front([0, 0, -1])
        view.set_up([0, 1, 0])
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_render)
        self.timer.start(50)  # 20fps
        
        self.geometry_loaded = False
    
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
        """加载3D文件并设置到可视化器中"""
        try:
            self.geometry_loaded = False
            self.vis.clear_geometries()
            
            if file_path.endswith('.pcd'):
                print(f"尝试加载点云: {file_path}")
                pcd = o3d.io.read_point_cloud(file_path)
                if len(pcd.points) == 0:
                    print("加载失败: 点云为空")
                    return False
                
                # 为点云添加颜色(如果没有)
                if not pcd.has_colors():
                    # 使用基于高度的渐变色，以便更好地可视化
                    points = np.asarray(pcd.points)
                    min_z = np.min(points[:, 2])
                    max_z = np.max(points[:, 2])
                    colors = np.zeros((len(points), 3))
                    for i in range(len(points)):
                        normalized = (points[i, 2] - min_z) / (max_z - min_z)
                        colors[i] = [0.2 + 0.8*normalized, 0.2 + 0.5*(1-normalized), 0.2 + 0.8*(1-normalized)]
                    pcd.colors = o3d.utility.Vector3dVector(colors)
                
                added = self.vis.add_geometry(pcd)
                if not added:
                    print("添加几何体到可视化器失败")
                    return False
                
                print(f"点云加载成功，点数: {len(pcd.points)}")
                
            elif file_path.endswith(('.obj', '.ply')):
                print(f"尝试加载网格: {file_path}")
                mesh = o3d.io.read_triangle_mesh(file_path)
                if mesh.is_empty():
                    print("加载失败: 网格为空")
                    return False
                
                if not mesh.has_vertex_colors():
                    mesh.paint_uniform_color([0.7, 0.7, 0.7])
                    
                # 确保有法线
                if not mesh.has_triangle_normals():
                    mesh.compute_triangle_normals()
                
                added = self.vis.add_geometry(mesh)
                if not added:
                    print("添加几何体到可视化器失败")
                    return False
                
                print(f"网格加载成功，顶点数: {len(mesh.vertices)}")
            
            # 重置视图
            self.vis.reset_view_point(True)
            
            # 激活几何体更新
            self.geometry_loaded = True
            return True
            
        except Exception as e:
            print(f"加载文件错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def rotate_view(self, dx, dy):
        """旋转视图"""
        ctr = self.vis.get_view_control()
        ctr.rotate(dx, dy)
    
    def pan_view(self, dx, dy):
        """平移视图"""
        ctr = self.vis.get_view_control()
        ctr.translate(dx, dy)
    
    def zoom_view(self, dy):
        """缩放视图"""
        ctr = self.vis.get_view_control()
        # Open3D中，scale值小于1表示放大，大于1表示缩小
        # 这与直觉相反，所以我们需要反转逻辑
        if dy > 0:
            # 向前滚动 - 放大（在Open3D中使用小于1的值）
            ctr.scale(0.9)
        else:
            # 向后滚动 - 缩小（在Open3D中使用大于1的值）
            ctr.scale(1.1)
    
    def cleanup(self):
        """清理资源"""
        self.timer.stop()
        self.vis.destroy_window()


class ImageViewWidget(QWidget):
    def __init__(self, renderer, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.image = None
        self.renderer = renderer  # 存储渲染器引用
        
        # 鼠标跟踪变量
        self.last_pos = None
        self.setMouseTracking(True)
    
    def set_image(self, img_array):
        """设置要显示的图像"""
        self.image = img_array
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        from PySide6.QtGui import QPainter, QImage, QPixmap
        
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
        else:
            # 如果没有图像，显示提示文本
            painter.drawText(
                self.rect(), 
                Qt.AlignmentFlag.AlignCenter, 
                "未加载模型或渲染中..."
            )
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self.last_pos = event.position()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.last_pos is not None:
            # 使用position()获取当前位置
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
        """鼠标释放事件"""
        self.last_pos = None
    
    def wheelEvent(self, event):
        """鼠标滚轮事件，用于缩放"""
        delta = event.angleDelta().y()
        # 确保正确的缩放方向：向前滚动(正值)放大，向后滚动(负值)缩小
        self.renderer.zoom_view(delta)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Hair Ezclick')
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # 左侧控制面板
        self.control_panel = QWidget()
        self.control_layout = QVBoxLayout(self.control_panel)
        
        # 加载按钮
        self.load_button = QPushButton('加载3D模型')
        self.load_button.clicked.connect(self.load_file)
        self.control_layout.addWidget(self.load_button)
        
        # 分组框：模型设置
        self.settings_group = QGroupBox("模型设置")
        self.settings_layout = QVBoxLayout()
        
        # 密度选择
        self.density_label = QLabel("密度")
        self.density_combo = QComboBox()
        self.density_combo.addItems(["低", "中", "高"])
        
        # 美学对齐选择
        self.align_label = QLabel("美学对齐")
        self.align_combo = QComboBox()
        self.align_combo.addItems(["选项1", "选项2", "选项3"])
        
        # 确认按钮
        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self.on_confirm)
        
        # 添加控件到设置分组
        self.settings_layout.addWidget(self.density_label)
        self.settings_layout.addWidget(self.density_combo)
        self.settings_layout.addWidget(self.align_label)
        self.settings_layout.addWidget(self.align_combo)
        self.settings_layout.addWidget(self.confirm_button)
        self.settings_group.setLayout(self.settings_layout)
        
        # 添加分组到控制面板
        self.control_layout.addWidget(self.settings_group)
        self.control_layout.addStretch()
        
        # 右侧视图面板
        self.view_panel = QWidget()
        self.view_layout = QVBoxLayout(self.view_panel)
        
        # 3D视图标签
        self.view_label = QLabel("3D 模型视图")
        self.view_layout.addWidget(self.view_label)
        
        # 创建渲染器
        self.renderer = Open3DRenderer()
        
        # 图像显示控件
        self.image_view = ImageViewWidget(self.renderer)
        self.renderer.render_ready.connect(self.image_view.set_image)
        self.view_layout.addWidget(self.image_view)
        
        # 状态栏标签
        self.status_label = QLabel("状态: 就绪")
        self.view_layout.addWidget(self.status_label)
        
        # 添加面板到分割器
        self.splitter.addWidget(self.control_panel)
        self.splitter.addWidget(self.view_panel)
        self.splitter.setSizes([250, 750])  # 设置初始分割比例
        
        # 设置状态栏
        self.statusBar().showMessage('就绪')
    
    def load_file(self):
        """打开文件选择对话框并加载3D文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            '打开3D文件', 
            '', 
            '3D文件 (*.pcd *.obj *.ply)'
        )
        
        if file_path:
            self.status_label.setText(f"状态: 加载中...")
            QApplication.processEvents()  # 确保UI更新
            
            success = self.renderer.set_geometry(file_path)
            
            if success:
                file_name = os.path.basename(file_path)
                self.view_label.setText(f"3D 模型视图: {file_name}")
                self.status_label.setText(f"状态: 已加载 {file_name}")
                self.statusBar().showMessage(f'已加载: {file_name}')
            else:
                self.view_label.setText("3D 模型视图")
                self.status_label.setText("状态: 加载失败")
                self.statusBar().showMessage('加载失败')
    
    def on_confirm(self):
        """确认按钮回调"""
        density = self.density_combo.currentText()
        alignment = self.align_combo.currentText()
        print(f"密度: {density}, 美学对齐: {alignment}")
        
        # 这里可以添加后续处理逻辑
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.renderer.cleanup()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())