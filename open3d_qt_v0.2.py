import sys
import open3d as o3d
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QComboBox, QLabel, QGroupBox
from PySide6.QtOpenGLWidgets import QOpenGLWidget


class Open3DWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)

        # 初始化 Open3D 可视化窗口
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(window_name="Open3D Viewer", width=640, height=480, visible=False)

    def initializeGL(self):
        """初始化 Open3D 渲染窗口"""
        self.vis.create_window(window_name="Open3D Window", width=640, height=480, visible=True)

    def paintGL(self):
        """刷新 Open3D 视图"""
        self.vis.poll_events()
        self.vis.update_renderer()

    def set_geometry(self, file_path):
        """加载 3D 文件并显示"""
        if file_path.endswith('.pcd'):
            # 读取点云
            pcd = o3d.io.read_point_cloud(file_path)
            if len(pcd.points) == 0:
                print("加载失败: 点云为空")
                return
            self.vis.clear_geometries()
            self.vis.add_geometry(pcd)
        elif file_path.endswith(('.obj', '.ply')):
            # 读取网格
            mesh = o3d.io.read_triangle_mesh(file_path)
            if mesh.is_empty():
                print("加载失败: 网格为空")
                return
            self.vis.clear_geometries()
            self.vis.add_geometry(mesh)

        self.vis.reset_view_point(True)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Hair Ezclick')
        self.setGeometry(100, 100, 900, 600)

        # 主布局
        self.layout = QHBoxLayout(self)

        # 左侧控制面板
        self.control_panel = QWidget()
        self.control_layout = QVBoxLayout(self.control_panel)

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

        # 添加控件到控制面板
        self.control_layout.addWidget(self.density_label)
        self.control_layout.addWidget(self.density_combo)
        self.control_layout.addWidget(self.align_label)
        self.control_layout.addWidget(self.align_combo)
        self.control_layout.addWidget(self.confirm_button)
        self.layout.addWidget(self.control_panel)

        # Open3D 视图
        self.viewer = Open3DWidget()
        self.layout.addWidget(self.viewer)

        # 加载按钮
        self.load_button = QPushButton('加载3D模型')
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)

    def load_file(self):
        """打开文件选择对话框并加载 3D 文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, '打开3D文件', '', '3D Files (*.pcd *.obj *.ply)')
        if file_path:
            self.viewer.set_geometry(file_path)

    def on_confirm(self):
        """确认按钮回调"""
        print(f"密度: {self.density_combo.currentText()}, 美学对齐: {self.align_combo.currentText()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
