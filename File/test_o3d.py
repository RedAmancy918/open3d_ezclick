import open3d as o3d
import numpy as np
import random

# 生成六边形定点坐标
def generate_hexagon_vertices(center, radius):
	angles = np.linspace(0, 2 * np.pi, 7)[:-1]
	vertices = np.array([
		[center[0] + radius * np.cos(angle), center[1] + radius * np.sin(angle), 0]
		for angle in angles
	])
	return vertices

# 使用重心坐标法在三角形内生成点
def generate_points_in_triangle(v0, v1, v2, num_points):
	points = []
	for _ in range(num_points):
		a, b = sorted([random.random(), random.random()])
		point = (1 - a) * v0 + (a - b) * v1 + b * v2
		points.append(point)
	return points

# 生成填充的六边形点云
def generate_filled_hexagon(center, radius, num_points):
	vertices = generate_hexagon_vertices(center, radius)
	center_point = np.array([center[0], center[1], 0])
	points = []

#将六边形分割成六个三角形，并在每个三角形内生成点
	for i in range(6):
		v0 = vertices[i]
		v1 = vertices[(i + 1) % 6]
		points += generate_points_in_triangle(center_point, v0, v1, num_points // 6)
	return np.array(points)


#中心坐标和半径
center = [0, 0]
radius = 1
num_points = 10000

#生成填充的六边形点云
filled_points = generate_filled_hexagon(center, radius, num_points)

#创建点云对象
point_cloud = o3d.geometry.PointCloud()
point_cloud.points = o3d.utility.Vector3dVector(filled_points)
point_cloud.paint_uniform_color([0, 0, 1])

#create visible cloud point
o3d.visualization.draw_geometries([point_cloud])
