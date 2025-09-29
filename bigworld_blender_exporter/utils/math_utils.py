import math
import struct
from mathutils import Vector, Matrix, Quaternion

def blender_to_bigworld_matrix():
    """Z-up (Blender) to Y-up (BigWorld) 坐标系转换"""
    return Matrix([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, -1, 0, 0],
        [0, 0, 0, 1]
    ])

def bigworld_to_blender_matrix():
    """Y-up (BigWorld) to Z-up (Blender) 坐标系转换"""
    return Matrix([
        [1, 0, 0, 0],
        [0, 0, -1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1]
    ])

def _compress_dir_to_short2(vec3):
    """将单位向量压缩为short2并返回打包后的字节。"""
    # 允许 vec3 为列表/元组/Vector
    v = Vector(vec3)
    if v.length_squared == 0:
        v = Vector((0.0, 0.0, 1.0))
    else:
        v.normalize()
    theta = math.atan2(v.y, v.x)  # [-pi, pi]
    phi = math.acos(max(-1.0, min(1.0, v.z)))  # [0, pi]
    u = int((theta / math.pi + 1.0) * 32767) - 32768
    w = int((phi / math.pi) * 32767) - 32768
    u = max(-32768, min(32767, u))
    w = max(-32768, min(32767, w))
    return struct.pack('<hh', u, w)

def compress_normal(normal):
    """float3 法线 -> short2 字节 (BigWorld风格)。"""
    return _compress_dir_to_short2(normal)

def compress_tangent(tangent):
    return _compress_dir_to_short2(tangent)

def compress_binormal(binormal):
    return _compress_dir_to_short2(binormal)

def calculate_bounding_box(vertices):
    """根据顶点列表计算AABB。顶点为包含 'position' 的字典。"""
    if not vertices:
        return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    min_coords = [float('inf')] * 3
    max_coords = [float('-inf')] * 3
    for v in vertices:
        p = v.get('position', (0.0, 0.0, 0.0))
        for i in range(3):
            if p[i] < min_coords[i]:
                min_coords[i] = p[i]
            if p[i] > max_coords[i]:
                max_coords[i] = p[i]
    return min_coords, max_coords

def calculate_extent(bmin, bmax):
    """返回AABB最大边长作为 extent。"""
    return max(bmax[0]-bmin[0], bmax[1]-bmin[1], bmax[2]-bmin[2])
