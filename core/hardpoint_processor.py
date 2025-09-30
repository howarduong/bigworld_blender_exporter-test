# 文件位置: bigworld_blender_exporter/core/hardpoint_processor.py
# -*- coding: utf-8 -*-
"""
Collect hardpoints (HP_) and portals (PORTAL_) for .visual extensions.

Hardpoints:
  - Objects (empties or bones) named 'HP_<Name>' are exported as hardpoints.
  - Data: identifier and transform matrix (4x4), written later in visual_format.

Portals:
  - Mesh objects named 'PORTAL_<Name>' exported as polygon portals.
  - Data: list of vertices in world/local space (configurable).

This processor returns structured data to be consumed by formats/visual_format.py.
"""

import bpy
from mathutils import Matrix
from typing import Dict, List
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

        # Scan root and children
        to_visit = [root_obj] + list(root_obj.children_recursive)
        for obj in to_visit:
            name = obj.name

            # Hardpoints from empties or bones (represented as empties)
            if name.startswith(HP_PREFIX) and obj.type in {'EMPTY', 'ARMATURE', 'MESH'}:
                hp = {
                    "identifier": name[len(HP_PREFIX):].strip(),
                    "matrix": self._world_matrix(obj),
                }
                hardpoints.append(hp)

            # Portals from meshes
            if name.startswith(PORTAL_PREFIX) and obj.type == 'MESH':
                mesh = obj.data
                mesh.calc_loop_triangles()
                verts = [self._world_matrix(obj) @ v.co.to_4d() for v in mesh.vertices]
                portals.append({
                    "identifier": name[len(PORTAL_PREFIX):].strip(),
                    "vertices": [tuple((v.x, v.y, v.z)) for v in verts],
                })

        LOG.info(f"Collected hardpoints={len(hardpoints)} portals={len(portals)} for {root_obj.name}")
        return {"hardpoints": hardpoints, "portals": portals}

    def _world_matrix(self, obj: bpy.types.Object) -> Matrix:
        return obj.matrix_world.copy()
