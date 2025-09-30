# 文件位置: bigworld_blender_exporter/core/collision_processor.py
# -*- coding: utf-8 -*-
"""
Collect collision meshes (prefixed COL_) and build a simple BSP data structure.

This module scans Blender objects in the scene to find meshes whose name starts
with 'COL_' and packs their triangles into a BSP-friendly data structure.
For simplicity and robustness, we output a single-node BSP with all triangles.
"""

import bpy
import bmesh
from mathutils import Vector
from typing import Dict, List, Tuple
from ..utils import logger
from ..utils.validation import ValidationError

COL_PREFIX = "COL_"
LOG = logger.get_logger("collision_processor")


class CollisionProcessor:
    """
    Find and convert collision meshes into BSP data suitable for .primitives BSP section.
    """

    def collect_bsp_for_object(self, obj: bpy.types.Object) -> Dict:
        """
        If the object itself is a collision mesh (name starts with COL_), convert it.
        Otherwise, scan its children for collision meshes and combine triangles.

        Returns bsp_data:
          {
            "nodes": [ { plane:(nx,ny,nz,d), childA:-1, childB:-1, triStart:int, triCount:int } ],
            "triangles": [ (i0,i1,i2), ... ]  # vertex indices relative to combined vertex buffer
          }
        """
        col_meshes = []

        if obj.type == 'MESH' and obj.name.startswith(COL_PREFIX):
            col_meshes.append(obj)

        # children
        for child in obj.children:
            if child.type == 'MESH' and child.name.startswith(COL_PREFIX):
                col_meshes.append(child)

        if not col_meshes:
            LOG.info(f"No collision meshes found for object: {obj.name}")
            return {"nodes": [], "triangles": []}

        # Accumulate triangles in object-local vertex indexing.
        # Caller must remap to global vertex indices if needed.
        triangles: List[Tuple[int, int, int]] = []
        vertex_offset = 0

        for col in col_meshes:
            mesh = self._eval_and_triangulate(col)
            # loop_triangles uses mesh vertices; collect per triangle indices
            mesh.calc_loop_triangles()
            # Build local mapping from loop triangle to vertex index
            for tri in mesh.loop_triangles:
                i0 = mesh.loops[tri.loops[0]].vertex_index + vertex_offset
                i1 = mesh.loops[tri.loops[1]].vertex_index + vertex_offset
                i2 = mesh.loops[tri.loops[2]].vertex_index + vertex_offset
                triangles.append((i0, i1, i2))
            vertex_offset += len(mesh.vertices)

        # Simple BSP: single node, plane = (0,0,1,0), encompass all triangles
        nodes = [{
            "plane": (0.0, 0.0, 1.0, 0.0),
            "childA": -1,
            "childB": -1,
            "triStart": 0,
            "triCount": len(triangles),
        }]

        LOG.info(f"Collision BSP built: triangles={len(triangles)} nodes=1")
        return {"nodes": nodes, "triangles": triangles}

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
