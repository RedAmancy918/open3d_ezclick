import open3d as o3d
import numpy as np
dragon = o3d.io.read_point_cloud("/home/geo/Documents/open3d_learn/standford_cloud_data/dragon.pcd")
print(dragon)
aabb = dragon.get_axis_aligned_bounding_box()
aabb.color = (1, 0, 0)

[center_x, center_y, center_z] = aabb.get_center()
print("aabb_包围盒的中心坐标: \n", [center_x, center_y, center_z])

vertex_set = np.asarray(aabb.get_box_points())
print("obb_包围盒的顶点: \n", vertex_set)

aabb_box_length = np.asarray(aabb.get_extent())
print("aabb_包围盒边长: \n", aabb_box_length)

half_extent = np.asarray(aabb.get_half_extent())
print("aabb_包围盒半边长: \n", half_extent)

max_bound = np.asarray(aabb.get_max_bound())
print("aabb_包围盒边长的最大值: \n", max_bound)

max_extent = np.asarray(aabb.get_max_extent())
print("aabb_包围盒边长的最大范围，即X,Y和Z轴的最大值: \n", max_extent)

min_bound = np.asarray(aabb.get_min_bound())
print("aabb_包围盒边长的最小值: \n", min_bound)

o3d.visualization.draw_geometries([dragon, aabb], window_name="PointCloud Viewer",
                                  width=1024, height=768, left=50, top=50,
                                  point_show_normal=False, mesh_show_wireframe=False,
                                  mesh_show_back_face=False)   
