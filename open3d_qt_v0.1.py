import sys
import open3d as o3d

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

class Open3DWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.setFormat(QSurfaceFormat.defaultFormat())

        # Initialize Open3D Visualizer
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(visible=False)  # We will manually show it within Qt

    def initializeGL(self):
        # Initialize Open3D within the OpenGL context
        self.vis.create_window(window_name="Open3D Window", width=640, height=480, visible=True)

    def paintGL(self):
        # Redraw the Open3D scene
        self.vis.poll_events()
        self.vis.update_renderer()

    def set_geometry(self, geometry):
        # Set 3D geometry (mesh or point cloud)
        self.vis.clear_geometries()
        self.vis.add_geometry(geometry)

    def reset_view(self):
        # Optionally reset the view
        self.vis.reset_view_point(True)

class Open3DViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Open3D Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Open3D render window (QOpenGLWidget)
        self.view = Open3DWidget()
        self.layout.addWidget(self.view)

        # File dialog button
        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.load_button = QPushButton('Load 3D File')
        self.load_button.clicked.connect(self.load_3d_file)
        self.button_layout.addWidget(self.load_button)

    def load_3d_file(self):
        # Open file dialog to select a 3D file (e.g., PCD, OBJ, or PLY)
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open 3D File', '', '3D Files (*.pcd *.ply *.obj)')

        if file_name:
            # Load the selected 3D file using Open3D
            mesh = o3d.io.read_triangle_mesh(file_name)
            if mesh.is_empty():
                print("Failed to load the mesh.")
            else:
                # Set the geometry to the Open3DWidget
                self.view.set_geometry(mesh)
                self.view.reset_view()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = Open3DViewer()
    viewer.show()
    sys.exit(app.exec())
