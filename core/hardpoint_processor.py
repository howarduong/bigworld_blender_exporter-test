# 文件位置: bigworld_blender_exporter/core/hardpoint_processor.py
# -*- coding: utf-8 -*-
"""
Collect hardpoints (HP_) and portals (PORTAL_) for .visual extensions.

Hardpoints:
  - Objects named 'HP_<Name>' are exported as hardpoints.
  - Data: identifier, transform matrix (4x4), optional type/flags from custom properties:
      obj["hp_type"], obj["hp_flags"]

Portals:
  - Mesh objects named 'PORTAL_<Name>' exported as polygon portals.
  - Data: identifier, vertices (world), plane (nx,ny,nz,d), optional adjacentChunk:
      obj["adjacent_chunk"]

This processor returns structured data to be consumed by formats/visual_format.py.
"""

import bpy
from mathutils import Matrix, Vector
from typing import Dict, List, Tuple
from ..utils import logger

HP_PREFIX = "HP_"
PORTAL_PREFIX = "PORTAL_"
LOG = logger.get_logger("hardpoint_processor")


class HardpointProcessor:
    """
    Scan an object hierarchy for hardpoints and portal meshes.
    """

    def collect(self, root_obj: bpy.types.Object) -> Dict:
        hardpoints = []
        portals = []

        to_visit = [root_obj] + list(getattr(root_obj, "children_recursive", []))
        for obj in to_visit:
            name = obj.name

            # Hardpoints (EMPTY/ARMATURE/MESH 都允许作为 HP 承载点)
            if name.startswith(HP_PREFIX) and obj.type in {'EMPTY', 'ARMATURE', 'MESH'}:
                hp = {
                    "identifier": name[len(HP_PREFIX):].strip(),
                    "matrix": self._world_matrix(obj),
                }
                # 扩展属性（可选）
                if "hp_type" in obj:
                    hp["type"] = str(obj["hp_type"])
                if "hp_flags" in obj:
                    hp["flags"] = str(obj["hp_flags"])
                hardpoints.append(hp)

            # Portals
            if name.startswith(PORTAL_PREFIX) and obj.type == 'MESH' and obj.data is not None:
                mesh = obj.data
                world_m = obj.matrix_world.copy()
                verts_world = [world_m @ v.co for v in mesh.vertices]
                verts_raw = [(float(v.x), float(v.y), float(v.z)) for v in verts_world]

                # 计算平面（基于前3点的法线，如果不共线）
                plane = self._compute_plane(verts_world)
                portal_entry = {
                    "identifier": name[len(PORTAL_PREFIX):].strip(),
                    "vertices": verts_raw,
                    "plane": plane,  # (nx, ny, nz, d)
                }

                # 可选相邻区块
                if "adjacent_chunk" in obj:
                    portal_entry["adjacentChunk"] = str(obj["adjacent_chunk"])

                portals.append(portal_entry)

        LOG.info(f"Collected hardpoints={len(hardpoints)} portals={len(portals)} for {root_obj.name}")
        return {"hardpoints": hardpoints, "portals": portals}

    # ------------------------
    # Internal helpers
    # ------------------------
    def _world_matrix(self, obj: bpy.types.Object) -> Matrix:
        return obj.matrix_world.copy()

    def _compute_plane(self, verts_world: List[Vector]) -> Tuple[float, float, float, float]:
        """
        使用前3个非共线顶点计算平面方程 n·x + d = 0
        返回 (nx, ny, nz, d)。若无法计算，返回 (0,0,1,0)。
        """
        if len(verts_world) < 3:
            return (0.0, 0.0, 1.0, 0.0)

        p0, p1, p2 = verts_world[0], None, None

        # 找到非共线的三角
        for i in range(1, len(verts_world)):
            for j in range(i + 1, len(verts_world)):
                p1 = verts_world[i]
                p2 = verts_world[j]
                n = (p1 - p0).cross(p2 - p0)
                if n.length > 1e-8:
                    # 单位化
                    n.normalize()
                    d = -n.dot(p0)
                    return (float(n.x), float(n.y), float(n.z), float(d))

        # 如果全部共线，返回默认
        return (0.0, 0.0, 1.0, 0.0)
