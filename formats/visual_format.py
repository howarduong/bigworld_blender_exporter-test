# 文件位置: bigworld_blender_exporter/formats/visual_format.py
# Visual file format for BigWorld export (aligned to official grammar, with LOD support)

import xml.etree.ElementTree as ET
from ..utils.logger import get_logger
from ..utils.xml_writer import write_xml_file
from ..utils.math_utils import blender_to_bigworld_matrix
from ..utils.validation import ValidationError

logger = get_logger("visual_format")


def export_visual_file(filepath, visual_data):
    """
    Export visual data to BigWorld .visual file

    visual_data dict expected keys:
      - nodes: list of { 'name': str, 'matrix': 4x4 list[list[float]] }
      - world_space: bool
      - primitives: str (path to .primitives file)   # 单LOD时使用
      - primitive_groups: list of { 'material': str, 'fx': str, 'materialKind': str,
                                    'startIndex': int, 'numPrims': int,
                                    'startVertex': int, 'numVertices': int }
      - bbox_min: "x y z"
      - bbox_max: "x y z"
      - lods: optional list of {
            'distance': float,
            'primitives': str,
            'primitive_groups': list[dict]
        }
    """
    logger.info(f"Exporting visual file: {filepath}")

    root = ET.Element("visual")

    # ----------------------------
    # Node tree
    # ----------------------------
    if "nodes" not in visual_data or not visual_data["nodes"]:
        raise ValidationError("visual_data must contain at least one node")

    for node_data in visual_data["nodes"]:
        node = ET.SubElement(root, "node")
        ET.SubElement(node, "identifier").text = node_data["name"]

        transform = ET.SubElement(node, "transform")
        mat = blender_to_bigworld_matrix(node_data["matrix"])
        for i in range(4):
            row = " ".join(f"{mat[i][j]:.6f}" for j in range(4))
            ET.SubElement(transform, f"row{i}").text = row

    # ----------------------------
    # LOD support
    # ----------------------------
    lods = visual_data.get("lods", [])
    if lods:
        # lodDistances
        lod_elem = ET.SubElement(root, "lodDistances")
        for lod in lods:
            ET.SubElement(lod_elem, "distance").text = f"{lod.get('distance', 0.0):.6f}"

        # multiple renderSets
        for lod in lods:
            _write_render_set(root, visual_data, lod)
    else:
        # single renderSet
        _write_render_set(root, visual_data)

    # ----------------------------
    # Bounding box
    # ----------------------------
    bbox = ET.SubElement(root, "boundingBox")
    ET.SubElement(bbox, "min").text = visual_data.get("bbox_min", "-1.0 -1.0 -1.0")
    ET.SubElement(bbox, "max").text = visual_data.get("bbox_max", "1.0 1.0 1.0")

    # ----------------------------
    # Write XML
    # ----------------------------
    write_xml_file(root, filepath)
    logger.info(f".visual written: {filepath}")


def _write_render_set(root, visual_data, lod=None):
    """
    写入一个 renderSet 节点
    - lod: dict (包含 distance, primitives, primitive_groups)
    - visual_data: dict (包含 world_space, nodes, primitives, primitive_groups)
    """
    rset = ET.SubElement(root, "renderSet")
    ET.SubElement(rset, "treatAsWorldSpaceObject").text = (
        "true" if visual_data.get("world_space", False) else "false"
    )
    # attach first node as default
    ET.SubElement(rset, "node").text = visual_data["nodes"][0]["name"]

    geometry = ET.SubElement(rset, "geometry")

    # primitives file
    prim_file = (lod or visual_data).get("primitives", "")
    if not prim_file.endswith(".primitives"):
        raise ValidationError("visual_data.primitives must be a .primitives file path")
    base_name = prim_file.replace(".primitives", "")
    ET.SubElement(geometry, "vertices").text = base_name + ".vertices"
    ET.SubElement(geometry, "primitive").text = base_name + ".indices"

    # primitive groups
    groups = (lod or visual_data).get("primitive_groups", [])
    if not groups:
        raise ValidationError("visual_data must contain primitive_groups")

    for g in groups:
        group = ET.SubElement(geometry, "primitiveGroup")
        mat_elem = ET.SubElement(group, "material")
        ET.SubElement(mat_elem, "identifier").text = g.get("material", "").replace(".mfm", "")
        ET.SubElement(mat_elem, "fx").text = g.get("fx", "shaders/std_effects.fx")
        if "materialKind" in g:
            ET.SubElement(mat_elem, "materialKind").text = g["materialKind"]

        # group stats
        ET.SubElement(group, "startIndex").text = str(g.get("startIndex", 0))
        ET.SubElement(group, "numPrimitives").text = str(g.get("numPrims", 0))
        ET.SubElement(group, "startVertex").text = str(g.get("startVertex", 0))
        ET.SubElement(group, "numVertices").text = str(g.get("numVertices", 0))
