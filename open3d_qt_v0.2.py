import sys
import open3d as o3d
import numpy as np
import platform

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QComboBox, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer
from PySide6.QtGui import QWindow

# 仅在 Windows 平台导入 win32gui
if platform.system() == "Windows":
    import win32gui


class Open3DWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.vis = None
        self.o3d_window = None

        self.init_open3d()  # 初始化 Open3D 可视化窗口

    def init_open3d(self):
        """初始化 Open3D 视觉窗口，并尝试嵌入到 Qt 窗口"""
        if self.vis is not None:
            return  # 避免重复初始化
        
        # **创建 Open3D Visualizer**
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(window_name="Open3D", width=640, height=480, visible=True)

        # **Windows 平台：获取窗口句柄**
        if platform.system() == "Windows":
            hwnd = win32gui.FindWindowEx(0, 0, None, "Open3D")
            if hwnd == 0:
                print("[Error] 无法找到 Open3D 窗口，请检查 window_name")
                return
            self.o3d_window = QWindow.fromWinId(hwnd)
        else:
            # **Linux/macOS 平台：尝试获取 Open3D 窗口**
            self.o3d_window = QWindow.fromWinId(self.vis.get_viewer_window())

        if not self.o3d_window:
            print("[Error] 无法创建 QWindow")
            return

        # **使用 QWindowContainer 进行嵌入**
        self.o3d_container = self.createWindowContainer(self.o3d_window, self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.o3d_container)

        # **创建一个定时器，用于持续更新 Open3D 的渲染**
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_o3d)
        self.timer.start(30)  # 30ms 刷新一次, ~33FPS

    def set_geometry(self, file_path):
        """加载 3D 文件并显示"""
        if self.vis is None:
            print("[Error] Open3D 还未初始化")
            return

        # **读取点云**
        if file_path.endswith('.pcd'):
            pcd = o3d.io.read_point_cloud(file_path)
            if len(pcd.points) == 0:
                print("加载失败: 点云为空")
                return
            self.vis.clear_geometries()
            self.vis.add_geometry(pcd)
        elif file_path.endswith(('.obj', '.ply')):
            mesh = o3d.io.read_triangle_mesh(file_path)
            if mesh.is_empty():
                print("加载失败: 网格为空")
                return
            self.vis.clear_geometries()
            self.vis.add_geometry(mesh)

        # **更新 Open3D 渲染**
        self.vis.poll_events()
        self.vis.update_renderer()
        self.vis.reset_view_point(True)

    def update_o3d(self):
        """更新 Open3D 视图"""
        if self.vis:
            self.vis.poll_events()
            self.vis.update_renderer()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Hair Ezclick')
        self.setGeometry(100, 100, 900, 600)

        # **创建主窗口布局**
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # **创建 Open3D 视图**
        self.viewer = Open3DWidget()
        layout.addWidget(self.viewer)

        # **左侧控制面板**
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)

        # **密度选择**
        self.density_label = QLabel("密度")
        self.density_combo = QComboBox()
        self.density_combo.addItems(["低", "中", "高"])

        # **美学对齐选择**
        self.align_label = QLabel("美学对齐")
        self.align_combo = QComboBox()
        self.align_combo.addItems(["选项1", "选项2", "选项3"])

        # **确认按钮**
        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self.on_confirm)

        # **加载按钮**
        self.load_button = QPushButton("加载3D模型")
        self.load_button.clicked.connect(self.load_file)

        # **添加控件到控制面板**
        control_layout.addWidget(self.density_label)
        control_layout.addWidget(self.density_combo)
        control_layout.addWidget(self.align_label)
        control_layout.addWidget(self.align_combo)
        control_layout.addWidget(self.confirm_button)
        control_layout.addWidget(self.load_button)
        layout.addWidget(control_panel)

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
