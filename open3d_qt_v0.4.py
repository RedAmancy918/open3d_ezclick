import sys
import os
import open3d as o3d
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QFileDialog, QComboBox, QLabel, QFrame, QToolButton)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QSize
from PySide6.QtGui import QIcon, QColor, QPalette, QFont

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
        opt.background_color = np.array([1, 1, 1])  # 白色背景
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
        
        # 设置白色背景
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(pal)
    
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
                "请加载3D模型"
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
        # 确保正确的缩放方向
        self.renderer.zoom_view(delta)


class StyledFrame(QFrame):
    """带样式的边框框架"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        
        # 设置浅蓝色背景
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(240, 248, 255))  # 非常浅的蓝色
        self.setPalette(pal)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Hair Ezclick')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 设置应用程序全局背景色为浅灰色
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
        
        # 主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        
        # 左侧控制面板
        self.left_panel = StyledFrame()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(20, 20, 20, 20)
        
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
        
        # 添加控件到左侧面板
        self.left_layout.addWidget(self.density_label)
        self.left_layout.addWidget(self.density_combo)
        self.left_layout.addSpacing(15)
        self.left_layout.addWidget(self.align_label)
        self.left_layout.addWidget(self.align_combo)
        self.left_layout.addStretch()
        self.left_layout.addWidget(self.confirm_button)
        
        # 中间视图面板
        self.center_panel = StyledFrame()
        self.center_layout = QVBoxLayout(self.center_panel)
        self.center_layout.setContentsMargins(1, 1, 1, 1)  # 减小内边距
        
        # 创建渲染器
        self.renderer = Open3DRenderer()
        
        # 图像显示控件
        self.image_view = ImageViewWidget(self.renderer)
        self.renderer.render_ready.connect(self.image_view.set_image)
        self.center_layout.addWidget(self.image_view)
        
        # 右侧工具面板
        self.right_panel = StyledFrame()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加两个工具按钮
        # 注意：这里需要添加图标文件
        self.pen_button = QToolButton()
        self.pen_button.setIcon(QIcon("icons/pen_icon.png"))  # 预留图标路径
        self.pen_button.setIconSize(QSize(32, 32))
        self.pen_button.setToolTip("绘制工具")
        self.pen_button.clicked.connect(self.on_pen_clicked)
        self.pen_button.setCheckable(True)  # 可以切换按下/释放状态
        
        self.user_button = QToolButton()
        self.user_button.setIcon(QIcon("icons/user_icon.png"))  # 预留图标路径
        self.user_button.setIconSize(QSize(32, 32))
        self.user_button.setToolTip("用户工具")
        self.user_button.clicked.connect(self.on_user_clicked)
        self.user_button.setCheckable(True)  # 可以切换按下/释放状态
        
        # 将按钮添加到右侧面板
        self.right_layout.addWidget(self.pen_button)
        self.right_layout.addWidget(self.user_button)
        self.right_layout.addStretch()
        
        # 将所有面板添加到主布局
        self.main_layout.addWidget(self.left_panel, 1)
        self.main_layout.addWidget(self.center_panel, 4)
        self.main_layout.addWidget(self.right_panel, 1)
        
        # 设置菜单栏，用于加载模型
        self.create_menu()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        
        open_action = file_menu.addAction('加载3D模型')
        open_action.triggered.connect(self.load_file)
    
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
            QApplication.processEvents()  # 确保UI更新
            
            success = self.renderer.set_geometry(file_path)
            
            if success:
                file_name = os.path.basename(file_path)
                self.statusBar().showMessage(f'已加载: {file_name}')
            else:
                self.statusBar().showMessage('加载失败')
    
    def on_confirm(self):
        """确认按钮回调"""
        density = self.density_combo.currentText()
        alignment = self.align_combo.currentText()
        print(f"密度: {density}, 美学对齐: {alignment}")
        
        # 这里可以添加后续处理逻辑
    
    def on_pen_clicked(self):
        """笔工具按钮点击回调"""
        is_checked = self.pen_button.isChecked()
        state = "激活" if is_checked else "取消激活"
        print(f"笔工具 {state}")
        self.statusBar().showMessage(f"笔工具 {state}")
        
        # 如果笔工具激活，取消用户工具
        if is_checked and self.user_button.isChecked():
            self.user_button.setChecked(False)
    
    def on_user_clicked(self):
        """用户工具按钮点击回调"""
        is_checked = self.user_button.isChecked()
        state = "激活" if is_checked else "取消激活"
        print(f"用户工具 {state}")
        self.statusBar().showMessage(f"用户工具 {state}")
        
        # 如果用户工具激活，取消笔工具
        if is_checked and self.pen_button.isChecked():
            self.pen_button.setChecked(False)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.renderer.cleanup()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序全局字体
    font = QFont("Microsoft YaHei", 9)  # 使用微软雅黑字体
    app.setFont(font)
    
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())