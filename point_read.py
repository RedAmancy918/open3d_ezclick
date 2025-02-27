import open3d as o3d
import numpy as np

# 读取点云文件
point_cloud = o3d.io.read_point_cloud("/home/geo/Documents/open3d_learn/standford_cloud_data/dragon.pcd",
    format='pcd',
    remove_nan_points=True,
    remove_infinite_points=True,
    print_progress=True)

# 打印点云对象
print(point_cloud)

# 打印点云的 numpy 数组（即点的坐标）
print(np.asarray(point_cloud.points))

# 可视化点云
o3d.visualization.draw_geometries([point_cloud], window_name="PointCloud Viewer")

