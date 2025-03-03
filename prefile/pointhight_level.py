import open3d as o3d
import numpy as np

# 读取点云文件
point_cloud = o3d.io.read_point_cloud("/home/geo/Documents/open3d_learn/standford_cloud_data/dragon.pcd")
points = np.asarray(point_cloud.points)

zdist = points[:, 2]

zhot_colors = plt.get_cmap('hot')(
    (zdist - zdist.min()) / (zdist.max() - zdist.min()))

zhot_colors = zhot_colors[:, :3]   
pcd.colors = o3d.utility.Vector3dVector(zhot_colors)
o3d.visualization.draw_geometries([point_cloud], window_name="热力图渲染颜色", # 显示点云
width=800, height=600, left=50, top=50)