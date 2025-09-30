# 文件位置: bigworld_blender_exporter/core/collision_processor.py
# -*- coding: utf-8 -*-
"""
Collect collision meshes (prefixed COL_) and build a BSP data structure.

- 扫描对象及其子层级，收集名称以 COL_ 开头的 Mesh。
- 对每个 Mesh 执行评估和三角化，合并为统一的顶点索引空间。
- 使用三角形质心的轴向中位数递归划分构建简单 BSP：
  - 交替使用 X/Y/Z 轴
  - 当三角形数量 <= leaf_limit 或递归深度达到上限时，生成叶子节点
- 输出的 BSP 数据包含 nodes 和 triangles（indices 指向合并后的顶点空间）

说明：
- 这是一个稳健的 BSP 初始实现，能保证层次结构和叶子三角范围连续。
- 可根据需求替换为更优化的平面选择策略（例如 SAH）。
"""

import bpy
import bmesh
from mathutils import Vector
from typing import Dict, List, Tuple
from ..utils import logger

COL_PREFIX = "COL_"
LOG = logger.get_logger("collision_processor")

LeafTriangleLimit = 128
MaxDepth = 16


class CollisionProcessor:
    """
    Find and convert collision meshes into BSP data suitable for .primitives BSP section.
    """

    def collect_bsp_for_object(self, root_obj: bpy.types.Object) -> Dict:
        """
        从 root 对象及其子层级收集以 COL_ 前缀的碰撞网格，构建 BSP 数据。

        返回 bsp_data:
          {
            "nodes": [ { plane:(nx,ny,nz,d), childA:int, childB:int, triStart:int, triCount:int }, ... ],
            "triangles": [ (i0,i1,i2), ... ]
          }
        """
        col_meshes = []

        # root 自身
        if root_obj.type == 'MESH' and root_obj.name.startswith(COL_PREFIX):
            col_meshes.append(root_obj)

        # 递归子层级
        for child in getattr(root_obj, "children_recursive", []):
            if child.type == 'MESH' and child.name.startswith(COL_PREFIX):
                col_meshes.append(child)

        if not col_meshes:
            LOG.info(f"No collision meshes found under: {root_obj.name}")
            return {"nodes": [], "triangles": []}

        # 合并所有碰撞网格的顶点与三角，建立统一索引空间
        global_vertices: List[Vector] = []
        triangles: List[Tuple[int, int, int]] = []
        vertex_offset = 0

        for col in col_meshes:
            mesh = self._eval_and_triangulate(col)
            # 顶点世界空间坐标
            world_m = col.matrix_world.copy()
            local_positions = [world_m @ v.co for v in mesh.vertices]
            global_vertices.extend(local_positions)

            mesh.calc_loop_triangles()
            for tri in mesh.loop_triangles:
                i0 = mesh.loops[tri.loops[0]].vertex_index + vertex_offset
                i1 = mesh.loops[tri.loops[1]].vertex_index + vertex_offset
                i2 = mesh.loops[tri.loops[2]].vertex_index + vertex_offset
                triangles.append((i0, i1, i2))
            vertex_offset += len(mesh.vertices)

        LOG.info(f"Collision collected: meshes={len(col_meshes)} verts={len(global_vertices)} tris={len(triangles)}")

        if not triangles:
            return {"nodes": [], "triangles": []}

        # 构建 BSP
        nodes, ordered_triangles = self._build_bsp(global_vertices, triangles)
        LOG.info(f"BSP built: nodes={len(nodes)} tris={len(ordered_triangles)}")
        return {"nodes": nodes, "triangles": ordered_triangles}

    # ------------------------
    # Internal helpers
    # ------------------------
    def _eval_and_triangulate(self, obj: bpy.types.Object):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        return mesh

    def _build_bsp(self, vertices: List[Vector], triangles: List[Tuple[int, int, int]]):
        """
        构建简单 BSP：
        - 使用三角形质心在当前轴的中位数划分
        - 递归划分直到达到叶子阈值或最大深度
        - 返回 nodes 列表与按叶子顺序重排的三角列表
        """
        # 预先计算质心
        centroids = [self._triangle_centroid(vertices, tri) for tri in triangles]

        # 递归构建，收集叶子三角范围（在原数组中的下标）
        tri_indices = list(range(len(triangles)))
        nodes: List[Dict] = []
        output_triangles: List[Tuple[int, int, int]] = []

        def build_node(idx_list: List[int], depth: int, axis: int) -> int:
            """
            返回当前节点在 nodes 列表中的索引。
            如果是叶子节点，会把三角形追加到 output_triangles，并记录连续范围。
            """
            # 叶子条件
            if depth >= MaxDepth or len(idx_list) <= LeafTriangleLimit:
                # 记录输出范围起点
                tri_start = len(output_triangles)
                for tri_i in idx_list:
                    output_triangles.append(triangles[tri_i])
                tri_count = len(idx_list)

                # 叶子节点（childA/childB = -1）
                node_index = len(nodes)
                # 平面用轴向平面（简化版），d=median
                median = self._median([centroids[i][axis] for i in idx_list])
                plane = [0.0, 0.0, 0.0, 0.0]
                plane[axis] = 1.0
                plane[3] = -median  # n·x + d = 0

                nodes.append({
                    "plane": tuple(plane),
                    "childA": -1,
                    "childB": -1,
                    "triStart": tri_start,
                    "triCount": tri_count,
                })
                return node_index

            # 内部节点：根据中位数划分
            axis_values = [centroids[i][axis] for i in idx_list]
            median = self._median(axis_values)

            left_list = [i for i in idx_list if centroids[i][axis] <= median]
            right_list = [i for i in idx_list if centroids[i][axis] > median]

            # 防止退化（全部在一侧），强制分割
            if not left_list or not right_list:
                # 改换轴或强制均分
                half = len(idx_list) // 2
                left_list, right_list = idx_list[:half], idx_list[half:]

            # 当前节点占位（稍后写 child 索引）
            node_index = len(nodes)
            plane = [0.0, 0.0, 0.0, 0.0]
            plane[axis] = 1.0
            plane[3] = -median

            nodes.append({
                "plane": tuple(plane),
                "childA": -1,
                "childB": -1,
                "triStart": 0,
                "triCount": 0,
            })

            # 构建子节点
            next_axis = (axis + 1) % 3
            left_idx = build_node(left_list, depth + 1, next_axis)
            right_idx = build_node(right_list, depth + 1, next_axis)

            # 回填子索引
            nodes[node_index]["childA"] = left_idx
            nodes[node_index]["childB"] = right_idx
            return node_index

        build_node(tri_indices, 0, axis=0)
        return nodes, output_triangles

    def _triangle_centroid(self, vertices: List[Vector], tri: Tuple[int, int, int]) -> Tuple[float, float, float]:
        v0, v1, v2 = vertices[tri[0]], vertices[tri[1]], vertices[tri[2]]
        c = (v0 + v1 + v2) / 3.0
        return (float(c.x), float(c.y), float(c.z))

    def _median(self, values: List[float]) -> float:
        if not values:
            return 0.0
        vs = sorted(values)
        n = len(vs)
        if n % 2 == 1:
            return vs[n // 2]
        else:
            return 0.5 * (vs[n // 2 - 1] + vs[n // 2])
