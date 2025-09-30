# 文件位置: bigworld_blender_exporter/formats/visual_format.py
# -*- coding: utf-8 -*-
"""
Visual file format for BigWorld export (aligned to official grammar)

改进点：
- 支持 LOD（lodDistances + 多个 renderSet）
- 支持 HardPoints（identifier + transform，附加可选 type/flags）
- 支持 Portals（identifier + vertices + plane + adjacentChunk）
- 支持节点层级（递归写入 node/transform）
- 在 geometry 中写入 <vertexFormat>，与 .primitives 顶点布局保持一致
- 更严格校验 primitives 路径与 primitive_groups
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from ..utils.logger import get_logger
from ..utils.xml_writer import write_xml_file
from ..utils.math_utils import blender_to_bigworld_matrix
from ..utils.validation import ValidationError

logger = get_logger("visual_format")


def export_visual_file(filepath: str, visual_data: Dict) -> None:
    """
    导出 .visual XML 文件

    visual_data 预期结构：
      - nodes: List[dict]
        每个节点：
          { 'name': str, 'matrix': 4x4 list[list[float]], 'children': Optional[List[dict]] }
      - world_space: bool
      - primitives: str  或 lods[i]['primitives']: str  （.primitives 路径）
      - primitive_groups: List[dict] 或 lods[i]['primitive_groups']: List[dict]
          dict:
            { 'material': str, 'fx': str, 'materialKind': str,
              'startIndex': int, 'numPrims': int,
              'startVertex': int, 'numVertices': int }
      - vertexFormat: Optional[str] （与 .primitives 的顶点格式一致，如 'xyznuvtb' 或 'xyznuviiiwwtb'）
      - bbox_min: "x y z"
      - bbox_max: "x y z"
      - lods: Optional[List[dict]]
          { 'distance': float, 'primitives': str, 'primitive_groups': List[dict], 'vertexFormat': Optional[str] }
      - hardpoints: Optional[List[dict]]
          { 'identifier': str, 'matrix': 4x4 list[list[float]], 'type': Optional[str], 'flags': Optional[str] }
      - portals: Optional[List[dict]]
          { 'identifier': str, 'vertices': List[(x,y,z)], 'plane': (nx,ny,nz,d), 'adjacentChunk': Optional[str] }
    """
    logger.info(f"Exporting visual file: {filepath}")

    # 基础校验
    if "nodes" not in visual_data or not visual_data["nodes"]:
        raise ValidationError("visual_data 必须包含至少一个节点 'nodes'")

    root = ET.Element("visual")

    # 节点树（支持层级）
    for node_data in visual_data["nodes"]:
        _write_node(root, node_data)

    # LOD 支持
    lods = visual_data.get("lods", [])
    if lods:
        # lodDistances
        lod_elem = ET.SubElement(root, "lodDistances")
        for lod in lods:
            ET.SubElement(lod_elem, "distance").text = f"{float(lod.get('distance', 0.0)):.6f}"
        # 多 renderSet
        for lod in lods:
            _write_render_set(root, visual_data, lod)
    else:
        # 单一 renderSet
        _write_render_set(root, visual_data, None)

    # HardPoints
    hardpoints = visual_data.get("hardpoints", [])
    if hardpoints:
        hp_section = ET.SubElement(root, "hardPoints")
        for hp in hardpoints:
            h = ET.SubElement(hp_section, "hardPoint")
            ET.SubElement(h, "identifier").text = hp["identifier"]
            # 可选 type/flags
            if "type" in hp:
                ET.SubElement(h, "type").text = str(hp["type"])
            if "flags" in hp:
                ET.SubElement(h, "flags").text = str(hp["flags"])
            # 变换
            transform = ET.SubElement(h, "transform")
            mat = blender_to_bigworld_matrix(hp["matrix"])
            for i in range(4):
                row = " ".join(f"{mat[i][j]:.6f}" for j in range(4))
                ET.SubElement(transform, f"row{i}").text = row

    # Portals
    portals = visual_data.get("portals", [])
    if portals:
        p_section = ET.SubElement(root, "portals")
        for p in portals:
            pe = ET.SubElement(p_section, "portal")
            ET.SubElement(pe, "identifier").text = p["identifier"]
            # 顶点
            verts_elem = ET.SubElement(pe, "vertices")
            for v in p["vertices"]:
                ET.SubElement(verts_elem, "v").text = f"{float(v[0]):.6f} {float(v[1]):.6f} {float(v[2]):.6f}"
            # 平面
            if "plane" in p and isinstance(p["plane"], (list, tuple)) and len(p["plane"]) == 4:
                nx, ny, nz, d = p["plane"]
                ET.SubElement(pe, "plane").text = f"{float(nx):.6f} {float(ny):.6f} {float(nz):.6f} {float(d):.6f}"
            # 相邻区块（可选）
            if "adjacentChunk" in p and p["adjacentChunk"]:
                ET.SubElement(pe, "adjacentChunk").text = str(p["adjacentChunk"])

    # Bounding box
    bbox = ET.SubElement(root, "boundingBox")
    ET.SubElement(bbox, "min").text = visual_data.get("bbox_min", "-1.0 -1.0 -1.0")
    ET.SubElement(bbox, "max").text = visual_data.get("bbox_max", "1.0 1.0 1.0")

    # 写出文件
    write_xml_file(root, filepath)
    logger.info(f".visual written: {filepath}")


def _write_node(parent: ET.Element, node_data: Dict) -> None:
    """
    写入一个节点（支持递归 children）
    node_data:
      - name: str
      - matrix: 4x4 list[list[float]]
      - children: Optional[List[dict]]
    """
    node = ET.SubElement(parent, "node")
    ET.SubElement(node, "identifier").text = node_data["name"]

    transform = ET.SubElement(node, "transform")
    mat = blender_to_bigworld_matrix(node_data["matrix"])
    for i in range(4):
        row = " ".join(f"{mat[i][j]:.6f}" for j in range(4))
        ET.SubElement(transform, f"row{i}").text = row

    # 递归写子节点
    for child in node_data.get("children", []) or []:
        _write_node(node, child)


def _write_render_set(root: ET.Element, visual_data: Dict, lod: Optional[Dict]) -> None:
    """
    写入一个 renderSet 节点
    - lod: dict 或 None（包含 distance, primitives, primitive_groups, vertexFormat）
    - visual_data: dict（包含 world_space, nodes, primitives, primitive_groups, vertexFormat）
    """
    rset = ET.SubElement(root, "renderSet")
    ET.SubElement(rset, "treatAsWorldSpaceObject").text = (
        "true" if bool(visual_data.get("world_space", False)) else "false"
    )

    # 绑定到首个节点（如果有层级，loader一般以根节点为绑定入口）
    ET.SubElement(rset, "node").text = visual_data["nodes"][0]["name"]

    geometry = ET.SubElement(rset, "geometry")

    # primitives 文件校验与拆解
    prim_file = (lod or visual_data).get("primitives", "")
    if not isinstance(prim_file, str) or not prim_file.endswith(".primitives"):
        raise ValidationError("visual_data.primitives 必须是以 .primitives 结尾的文件路径")
    base_name = prim_file[:-11]  # 去掉 ".primitives"
    ET.SubElement(geometry, "vertices").text = base_name + ".vertices"
    ET.SubElement(geometry, "primitive").text = base_name + ".indices"

    # 顶点格式（确保与 .primitives 对齐）
    vfmt = (lod or visual_data).get("vertexFormat", visual_data.get("vertexFormat"))
    if vfmt:
        ET.SubElement(geometry, "vertexFormat").text = str(vfmt)

    # primitive groups
    groups = (lod or visual_data).get("primitive_groups", [])
    if not groups:
        raise ValidationError("visual_data 必须包含 primitive_groups（或在 lods 里提供）")

    for g in groups:
        group = ET.SubElement(geometry, "primitiveGroup")

        # 材质
        mat_elem = ET.SubElement(group, "material")
        ET.SubElement(mat_elem, "identifier").text = str(g.get("material", "")).replace(".mfm", "")
        ET.SubElement(mat_elem, "fx").text = str(g.get("fx", "shaders/std_effects.fx"))
        if "materialKind" in g and g["materialKind"]:
            ET.SubElement(mat_elem, "materialKind").text = str(g["materialKind"])

        # 统计
        ET.SubElement(group, "startIndex").text = str(int(g.get("startIndex", 0)))
        ET.SubElement(group, "numPrimitives").text = str(int(g.get("numPrims", 0)))
        ET.SubElement(group, "startVertex").text = str(int(g.get("startVertex", 0)))
        ET.SubElement(group, "numVertices").text = str(int(g.get("numVertices", 0)))



